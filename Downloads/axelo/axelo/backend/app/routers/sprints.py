from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.sprint import Sprint, SprintStatus
from app.models.issue import Issue, IssueStatus
from app.schemas.sprint import SprintCreate, SprintUpdate, SprintOut
from app.core.deps import get_current_user

router = APIRouter(prefix="/api/projects/{project_id}/sprints", tags=["sprints"])


def _get_project_and_check_access(project_id: int, user: User, db: Session) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    ids = [m.user_id for m in project.members] + [project.owner_id]
    if user.id not in ids:
        raise HTTPException(status_code=403, detail="Access denied")
    return project


@router.get("/", response_model=List[SprintOut])
def list_sprints(
    project_id: int,
    limit: int = 50,
    offset: int = 0,
    response: Response = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    limit = min(limit, 200)
    _get_project_and_check_access(project_id, current_user, db)
    query = db.query(Sprint).filter(Sprint.project_id == project_id)
    total = query.count()
    items = query.offset(offset).limit(limit).all()
    if response is not None:
        response.headers["X-Total-Count"] = str(total)
    return items


@router.post("/", response_model=SprintOut, status_code=status.HTTP_201_CREATED)
def create_sprint(
    project_id: int,
    sprint_in: SprintCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_project_and_check_access(project_id, current_user, db)
    sprint = Sprint(**sprint_in.model_dump(), project_id=project_id)
    db.add(sprint)
    db.commit()
    db.refresh(sprint)
    return sprint


@router.patch("/{sprint_id}", response_model=SprintOut)
async def update_sprint(
    project_id: int,
    sprint_id: int,
    sprint_in: SprintUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_project_and_check_access(project_id, current_user, db)
    sprint = db.query(Sprint).filter(Sprint.id == sprint_id, Sprint.project_id == project_id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    if sprint_in.status == SprintStatus.active:
        active = db.query(Sprint).filter(
            Sprint.project_id == project_id, Sprint.status == SprintStatus.active
        ).first()
        if active and active.id != sprint_id:
            raise HTTPException(status_code=400, detail="A sprint is already active")

    old_status = sprint.status
    for field, value in sprint_in.model_dump(exclude_unset=True).items():
        setattr(sprint, field, value)
    db.commit()
    db.refresh(sprint)

    # Broadcast sprint events for real-time UI updates
    from app.routers.websocket import manager
    if sprint_in.status and sprint_in.status != old_status:
        event = "sprint.started" if sprint.status == SprintStatus.active else \
                "sprint.completed" if sprint.status == SprintStatus.completed else "sprint.updated"
        await manager.broadcast_project(
            project_id, event,
            {"sprint_id": sprint.id, "sprint_name": sprint.name, "status": sprint.status},
        )
    return sprint


@router.delete("/{sprint_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sprint(
    project_id: int,
    sprint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_project_and_check_access(project_id, current_user, db)
    sprint = db.query(Sprint).filter(Sprint.id == sprint_id, Sprint.project_id == project_id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    db.delete(sprint)
    db.commit()


@router.get("/{sprint_id}/burndown")
def get_burndown(
    project_id: int,
    sprint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return burndown chart data for a sprint.

    Uses completed_at timestamps to reconstruct daily burn history.
    """
    _get_project_and_check_access(project_id, current_user, db)
    sprint = db.query(Sprint).filter(Sprint.id == sprint_id, Sprint.project_id == project_id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    issues = db.query(Issue).filter(Issue.sprint_id == sprint_id).all()
    total_points = sum(i.story_points or 0 for i in issues)

    if not sprint.start_date or not sprint.end_date or total_points == 0:
        return {"total_points": total_points, "days": []}

    start = sprint.start_date.date() if hasattr(sprint.start_date, "date") else sprint.start_date
    end = sprint.end_date.date() if hasattr(sprint.end_date, "date") else sprint.end_date
    today = date.today()
    end = min(end, today)

    total_days = max((sprint.end_date.date() if hasattr(sprint.end_date, "date") else sprint.end_date - start).days, 1)
    num_days = (end - start).days + 1

    days = []
    cumulative_burned = 0
    for i in range(num_days):
        current_day = start + timedelta(days=i)
        # Points completed on this day
        day_burned = sum(
            (issue.story_points or 0)
            for issue in issues
            if issue.completed_at
            and issue.completed_at.date() == current_day
            and issue.status == IssueStatus.done
        )
        cumulative_burned += day_burned
        remaining = total_points - cumulative_burned
        ideal = total_points * (1 - i / total_days)
        days.append({
            "date": current_day.isoformat(),
            "ideal": round(ideal, 1),
            "actual": remaining,
        })

    return {"total_points": total_points, "days": days}
