from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.sprint import Sprint, SprintStatus
from app.schemas.sprint import SprintCreate, SprintUpdate, SprintOut
from app.core.deps import get_current_user

router = APIRouter(prefix="/api/projects/{project_id}/sprints", tags=["sprints"])


def get_project_and_check_access(project_id: int, user: User, db: Session) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    ids = [m.user_id for m in project.members] + [project.owner_id]
    if user.id not in ids:
        raise HTTPException(status_code=403, detail="Access denied")
    return project


@router.get("/", response_model=List[SprintOut])
def list_sprints(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    get_project_and_check_access(project_id, current_user, db)
    return db.query(Sprint).filter(Sprint.project_id == project_id).all()


@router.post("/", response_model=SprintOut, status_code=status.HTTP_201_CREATED)
def create_sprint(project_id: int, sprint_in: SprintCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    get_project_and_check_access(project_id, current_user, db)
    sprint = Sprint(**sprint_in.model_dump(), project_id=project_id)
    db.add(sprint)
    db.commit()
    db.refresh(sprint)
    return sprint


@router.patch("/{sprint_id}", response_model=SprintOut)
def update_sprint(
    project_id: int,
    sprint_id: int,
    sprint_in: SprintUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_project_and_check_access(project_id, current_user, db)
    sprint = db.query(Sprint).filter(Sprint.id == sprint_id, Sprint.project_id == project_id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    if sprint_in.status == SprintStatus.active:
        active = db.query(Sprint).filter(Sprint.project_id == project_id, Sprint.status == SprintStatus.active).first()
        if active and active.id != sprint_id:
            raise HTTPException(status_code=400, detail="A sprint is already active")
    for field, value in sprint_in.model_dump(exclude_unset=True).items():
        setattr(sprint, field, value)
    db.commit()
    db.refresh(sprint)
    return sprint


@router.delete("/{sprint_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sprint(project_id: int, sprint_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    get_project_and_check_access(project_id, current_user, db)
    sprint = db.query(Sprint).filter(Sprint.id == sprint_id, Sprint.project_id == project_id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    db.delete(sprint)
    db.commit()
