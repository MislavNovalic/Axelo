"""
Reporting endpoints — P2:
  GET /api/projects/{id}/reports/burndown?sprint_id=N  → Sprint burndown data
  GET /api/projects/{id}/reports/velocity              → Points per sprint (last 6)
  GET /api/projects/{id}/reports/cycle-time            → Avg days in_progress→done per sprint
  GET /api/projects/{id}/reports/issue-flow            → Created vs resolved last 30d
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional
from datetime import date, timedelta, datetime
from app.database import get_db
from app.models.user import User
from app.models.project import Project, ProjectMember
from app.models.issue import Issue, IssueStatus
from app.models.sprint import Sprint
from app.core.deps import get_current_user

router = APIRouter(prefix="/api/projects/{project_id}/reports", tags=["reports"])


def _check_access(project_id: int, user: User, db: Session):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404)
    ids = {m.user_id for m in project.members} | {project.owner_id}
    if user.id not in ids:
        raise HTTPException(status_code=403)
    return project


# ── Burndown ──────────────────────────────────────────────────────────────────
@router.get("/burndown")
def burndown(
    project_id: int,
    sprint_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_access(project_id, current_user, db)
    sprint = db.query(Sprint).filter(Sprint.id == sprint_id, Sprint.project_id == project_id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    issues = db.query(Issue).filter(Issue.sprint_id == sprint_id).all()
    total_points = sum(i.story_points or 1 for i in issues)
    done_points  = sum(i.story_points or 1 for i in issues if i.status == IssueStatus.done)

    start = sprint.start_date.date() if sprint.start_date else date.today()
    end   = sprint.end_date.date()   if sprint.end_date   else (date.today() + timedelta(days=14))
    total_days = max((end - start).days, 1)

    # Ideal line: linearly decreasing
    ideal = []
    for d in range(total_days + 1):
        day = start + timedelta(days=d)
        if day > date.today():
            break
        remaining = total_points * (1 - d / total_days)
        ideal.append({"date": day.isoformat(), "points": round(remaining, 1)})

    # Actual line: use updated_at on done issues as a proxy
    actual_map: dict[str, float] = {}
    remaining = total_points
    for d in range(total_days + 1):
        day = start + timedelta(days=d)
        if day > date.today():
            break
        completed_today = sum(
            i.story_points or 1 for i in issues
            if i.status == IssueStatus.done
            and i.updated_at
            and i.updated_at.date() == day
        )
        remaining -= completed_today
        actual_map[day.isoformat()] = max(remaining, 0)

    actual = [{"date": k, "points": v} for k, v in actual_map.items()]

    return {
        "sprint":       {"id": sprint.id, "name": sprint.name},
        "total_points": total_points,
        "done_points":  done_points,
        "ideal":        ideal,
        "actual":       actual,
    }


# ── Velocity ──────────────────────────────────────────────────────────────────
@router.get("/velocity")
def velocity(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_access(project_id, current_user, db)
    from app.models.sprint import SprintStatus
    sprints = (
        db.query(Sprint)
        .filter(Sprint.project_id == project_id, Sprint.status == SprintStatus.completed)
        .order_by(Sprint.end_date.desc())
        .limit(6)
        .all()
    )[::-1]  # chronological

    data = []
    for sprint in sprints:
        issues = db.query(Issue).filter(Issue.sprint_id == sprint.id).all()
        committed = sum(i.story_points or 1 for i in issues)
        completed = sum(i.story_points or 1 for i in issues if i.status == IssueStatus.done)
        data.append({
            "sprint_id":   sprint.id,
            "sprint_name": sprint.name,
            "committed":   committed,
            "completed":   completed,
        })

    avg = round(sum(d["completed"] for d in data) / len(data), 1) if data else 0
    return {"sprints": data, "avg_velocity": avg}


# ── Cycle Time ────────────────────────────────────────────────────────────────
@router.get("/cycle-time")
def cycle_time(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_access(project_id, current_user, db)
    done_issues = (
        db.query(Issue)
        .filter(Issue.project_id == project_id, Issue.status == IssueStatus.done)
        .filter(Issue.created_at.isnot(None), Issue.updated_at.isnot(None))
        .limit(100)
        .all()
    )
    cycles = []
    for i in done_issues:
        days = (i.updated_at - i.created_at).days
        cycles.append({"key": i.key, "title": i.title, "days": max(days, 0), "type": i.type.value})

    avg = round(sum(c["days"] for c in cycles) / len(cycles), 1) if cycles else 0
    return {"issues": cycles, "avg_days": avg}


# ── Issue Flow ────────────────────────────────────────────────────────────────
@router.get("/issue-flow")
def issue_flow(
    project_id: int,
    days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_access(project_id, current_user, db)
    start_dt = datetime.utcnow() - timedelta(days=days)

    all_issues = db.query(Issue).filter(
        Issue.project_id == project_id,
        Issue.created_at >= start_dt,
    ).all()

    # Build daily buckets
    flow: dict[str, dict] = {}
    for d in range(days):
        day = (date.today() - timedelta(days=days - 1 - d)).isoformat()
        flow[day] = {"date": day, "created": 0, "resolved": 0}

    for i in all_issues:
        day = i.created_at.date().isoformat()
        if day in flow:
            flow[day]["created"] += 1
        if i.status == IssueStatus.done and i.updated_at:
            rday = i.updated_at.date().isoformat()
            if rday in flow:
                flow[rday]["resolved"] += 1

    return {"days": list(flow.values())}


# ── Audit Log ─────────────────────────────────────────────────────────────────
@router.get("/audit-log")
def get_audit_log(
    project_id: int,
    skip: int = 0,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_access(project_id, current_user, db)
    from app.models.audit_log import AuditLog
    from app.models.user import User as UserModel

    logs = (
        db.query(AuditLog)
        .filter(AuditLog.project_id == project_id)
        .order_by(AuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        {
            "id":          l.id,
            "entity_type": l.entity_type,
            "entity_id":   l.entity_id,
            "entity_key":  l.entity_key,
            "action":      l.action,
            "diff":        l.diff,
            "description": l.description,
            "created_at":  l.created_at.isoformat(),
            "user": (
                {"id": l.user.id, "full_name": l.user.full_name}
                if l.user else None
            ),
        }
        for l in logs
    ]
