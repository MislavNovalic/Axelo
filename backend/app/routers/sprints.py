import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.user import User
from app.models.project import Project, ProjectMember
from app.models.sprint import Sprint, SprintStatus
from app.schemas.sprint import SprintCreate, SprintUpdate, SprintOut
from app.core.deps import get_current_user
from app.core.permissions import require_project_write
from app.core.ws_manager import manager
from app.core.notify import notify

router = APIRouter(prefix="/api/projects/{project_id}/sprints", tags=["sprints"])


def get_project_and_check_access(project_id: int, user: User, db: Session) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    ids = [m.user_id for m in project.members] + [project.owner_id]
    if user.id not in ids:
        raise HTTPException(status_code=403, detail="Access denied")
    return project


def _broadcast(project_id: int, event: str, data: dict, exclude_user_id: int | None = None):
    payload = {"event": event, "data": data}
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(manager.broadcast_to_project(project_id, payload, exclude_user_id))
        else:
            loop.run_until_complete(manager.broadcast_to_project(project_id, payload, exclude_user_id))
    except RuntimeError:
        asyncio.run(manager.broadcast_to_project(project_id, payload, exclude_user_id))


@router.get("/", response_model=List[SprintOut])
def list_sprints(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    get_project_and_check_access(project_id, current_user, db)
    return db.query(Sprint).filter(Sprint.project_id == project_id).limit(200).all()


@router.post("/", response_model=SprintOut, status_code=status.HTTP_201_CREATED)
def create_sprint(project_id: int, sprint_in: SprintCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = get_project_and_check_access(project_id, current_user, db)
    require_project_write(project, current_user, db)
    sprint = Sprint(**sprint_in.model_dump(), project_id=project_id)
    db.add(sprint)
    db.commit()
    db.refresh(sprint)
    _broadcast(project_id, "sprint_created", {"id": sprint.id, "name": sprint.name, "status": sprint.status.value})
    return sprint


@router.patch("/{sprint_id}", response_model=SprintOut)
def update_sprint(
    project_id: int,
    sprint_id: int,
    sprint_in: SprintUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project_and_check_access(project_id, current_user, db)
    require_project_write(project, current_user, db)
    sprint = db.query(Sprint).filter(Sprint.id == sprint_id, Sprint.project_id == project_id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    if sprint_in.status == SprintStatus.active:
        active = db.query(Sprint).filter(Sprint.project_id == project_id, Sprint.status == SprintStatus.active).first()
        if active and active.id != sprint_id:
            raise HTTPException(status_code=400, detail="A sprint is already active")

    old_status = sprint.status
    for field, value in sprint_in.model_dump(exclude_unset=True).items():
        setattr(sprint, field, value)
    db.commit()
    db.refresh(sprint)

    # ── broadcast sprint update ───────────────────────────────────────────────
    _broadcast(project_id, "sprint_updated", {
        "id": sprint.id, "name": sprint.name, "status": sprint.status.value
    }, exclude_user_id=current_user.id)

    # ── notify all members on sprint start / complete ─────────────────────────
    new_status = sprint.status
    if old_status != new_status and new_status in (SprintStatus.active, SprintStatus.completed):
        event_type = "sprint_started" if new_status == SprintStatus.active else "sprint_completed"
        title = (
            f"Sprint \"{sprint.name}\" has started" if new_status == SprintStatus.active
            else f"Sprint \"{sprint.name}\" completed"
        )
        member_ids = [m.user_id for m in project.members] + [project.owner_id]
        for uid in set(member_ids):
            if uid != current_user.id:
                notify(
                    db, uid,
                    type=event_type,
                    title=title,
                    body=f"Project: {project.name}",
                    link=f"/projects/{project_id}",
                    actor_id=current_user.id,
                    project_id=project_id,
                )
        db.commit()

    return sprint


@router.delete("/{sprint_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sprint(project_id: int, sprint_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = get_project_and_check_access(project_id, current_user, db)
    require_project_write(project, current_user, db)
    sprint = db.query(Sprint).filter(Sprint.id == sprint_id, Sprint.project_id == project_id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    db.delete(sprint)
    db.commit()
    _broadcast(project_id, "sprint_deleted", {"id": sprint_id})
