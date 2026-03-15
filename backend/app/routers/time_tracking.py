"""
Time tracking router — Phase 3.
OWASP A01: all mutations validate project membership + write role.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from app.database import get_db
from app.core.deps import get_current_user
from app.core.permissions import require_project_write
from app.models.user import User
from app.models.project import Project, ProjectMember
from app.models.issue import Issue
from app.models.time_log import TimeLog

router = APIRouter(tags=["time-tracking"])


class TimeLogCreate(BaseModel):
    minutes: int = Field(..., gt=0, le=14400)   # max 10 days per entry
    description: Optional[str] = Field(None, max_length=500)


class TimeLogOut(BaseModel):
    id: int
    issue_id: int
    user_id: int
    user_name: str
    minutes: int
    description: Optional[str]
    logged_at: str

    class Config:
        from_attributes = True


def _get_project_and_issue(project_id: int, issue_id: int, db: Session) -> tuple[Project, Issue]:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    issue = db.query(Issue).filter(Issue.id == issue_id, Issue.project_id == project_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return project, issue


@router.get("/projects/{project_id}/issues/{issue_id}/time-logs")
def list_time_logs(
    project_id: int,
    issue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project, issue = _get_project_and_issue(project_id, issue_id, db)

    # Verify membership (read access)
    member = db.query(ProjectMember).filter_by(
        project_id=project_id, user_id=current_user.id
    ).first()
    if not member and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    logs = (
        db.query(TimeLog, User)
        .join(User, TimeLog.user_id == User.id)
        .filter(TimeLog.issue_id == issue_id)
        .order_by(TimeLog.logged_at.desc())
        .all()
    )

    total_minutes = sum(log.TimeLog.minutes for log in logs)

    return {
        "logs": [
            {
                "id": log.TimeLog.id,
                "issue_id": log.TimeLog.issue_id,
                "user_id": log.TimeLog.user_id,
                "user_name": log.User.full_name,
                "minutes": log.TimeLog.minutes,
                "description": log.TimeLog.description,
                "logged_at": log.TimeLog.logged_at.isoformat(),
            }
            for log in logs
        ],
        "total_minutes": total_minutes,
    }


@router.post("/projects/{project_id}/issues/{issue_id}/time-logs", status_code=201)
def log_time(
    project_id: int,
    issue_id: int,
    body: TimeLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project, issue = _get_project_and_issue(project_id, issue_id, db)
    require_project_write(project, current_user, db)

    log = TimeLog(
        issue_id=issue_id,
        user_id=current_user.id,
        minutes=body.minutes,
        description=body.description,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return {
        "id": log.id,
        "issue_id": log.issue_id,
        "user_id": log.user_id,
        "user_name": current_user.full_name,
        "minutes": log.minutes,
        "description": log.description,
        "logged_at": log.logged_at.isoformat(),
    }


@router.delete("/projects/{project_id}/issues/{issue_id}/time-logs/{log_id}", status_code=204)
def delete_time_log(
    project_id: int,
    issue_id: int,
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project, _ = _get_project_and_issue(project_id, issue_id, db)
    log = db.query(TimeLog).filter(TimeLog.id == log_id, TimeLog.issue_id == issue_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Time log not found")

    # Only the log author or an admin/owner can delete
    member = db.query(ProjectMember).filter_by(
        project_id=project_id, user_id=current_user.id
    ).first()
    from app.models.project import MemberRole
    is_admin = (project.owner_id == current_user.id) or (
        member and member.role in (MemberRole.admin, MemberRole.owner)
    )
    if log.user_id != current_user.id and not is_admin:
        raise HTTPException(status_code=403, detail="You can only delete your own time logs")

    db.delete(log)
    db.commit()


@router.get("/projects/{project_id}/reports/time")
def time_report(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Weekly time totals per team member and per issue for the project."""
    from app.core.permissions import require_admin_or_owner
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    require_admin_or_owner(project, current_user, db)

    # Per-user totals
    per_user = (
        db.query(User.id, User.full_name, func.sum(TimeLog.minutes).label("total"))
        .join(TimeLog, User.id == TimeLog.user_id)
        .join(Issue, TimeLog.issue_id == Issue.id)
        .filter(Issue.project_id == project_id)
        .group_by(User.id, User.full_name)
        .all()
    )

    # Per-issue totals
    per_issue = (
        db.query(Issue.id, Issue.key, Issue.title, func.sum(TimeLog.minutes).label("total"))
        .join(TimeLog, Issue.id == TimeLog.issue_id)
        .filter(Issue.project_id == project_id)
        .group_by(Issue.id, Issue.key, Issue.title)
        .order_by(func.sum(TimeLog.minutes).desc())
        .limit(20)
        .all()
    )

    return {
        "per_user": [
            {"user_id": r.id, "user_name": r.full_name, "total_minutes": r.total}
            for r in per_user
        ],
        "per_issue": [
            {"issue_id": r.id, "key": r.key, "title": r.title, "total_minutes": r.total}
            for r in per_issue
        ],
    }
