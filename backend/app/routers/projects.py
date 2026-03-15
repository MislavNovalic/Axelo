import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.user import User
from app.models.project import Project, ProjectMember, MemberRole
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectOut, AddMemberRequest, UpdateRoleRequest
from app.core.deps import get_current_user
from app.core.ws_manager import manager
from app.core.notify import notify

router = APIRouter(prefix="/api/projects", tags=["projects"])


def get_project_or_404(project_id: int, db: Session) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def require_member(project: Project, user: User):
    ids = [m.user_id for m in project.members] + [project.owner_id]
    if user.id not in ids:
        raise HTTPException(status_code=403, detail="Access denied")


def require_admin_or_owner(project: Project, user: User, db: Session):
    member = db.query(ProjectMember).filter_by(project_id=project.id, user_id=user.id).first()
    if not member or member.role not in (MemberRole.owner, MemberRole.admin):
        raise HTTPException(status_code=403, detail="Admin or Owner role required")


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


@router.get("/", response_model=List[ProjectOut])
def list_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    memberships = db.query(ProjectMember).filter(ProjectMember.user_id == current_user.id).all()
    member_project_ids = [m.project_id for m in memberships]
    return db.query(Project).filter(
        (Project.owner_id == current_user.id) | (Project.id.in_(member_project_ids))
    ).limit(200).all()


@router.post("/", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(project_in: ProjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if db.query(Project).filter(Project.key == project_in.key.upper()).first():
        raise HTTPException(status_code=400, detail="Project key already exists")
    data = project_in.model_dump()
    data['key'] = data['key'].upper()
    project = Project(**data, owner_id=current_user.id)
    db.add(project)
    db.flush()
    db.add(ProjectMember(project_id=project.id, user_id=current_user.id, role=MemberRole.owner))
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = get_project_or_404(project_id, db)
    require_member(project, current_user)
    return project


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(project_id: int, project_in: ProjectUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = get_project_or_404(project_id, db)
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the owner can update the project")
    for field, value in project_in.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = get_project_or_404(project_id, db)
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the owner can delete the project")
    db.delete(project)
    db.commit()


@router.post("/{project_id}/members", response_model=ProjectOut)
def add_member(project_id: int, req: AddMemberRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = get_project_or_404(project_id, db)
    require_admin_or_owner(project, current_user, db)
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if db.query(ProjectMember).filter_by(project_id=project_id, user_id=user.id).first():
        raise HTTPException(status_code=400, detail="User is already a member")
    db.add(ProjectMember(project_id=project_id, user_id=user.id, role=req.role))
    db.commit()
    db.refresh(project)

    # notify the invited user
    notify(
        db, user.id,
        type="added_to_project",
        title=f"You were added to \"{project.name}\"",
        body=f"Role: {req.role}",
        link=f"/projects/{project_id}",
        actor_id=current_user.id,
        project_id=project_id,
    )
    db.commit()

    return project


@router.patch("/{project_id}/members/{user_id}", response_model=ProjectOut)
def update_member_role(project_id: int, user_id: int, req: UpdateRoleRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = get_project_or_404(project_id, db)
    require_admin_or_owner(project, current_user, db)
    member = db.query(ProjectMember).filter_by(project_id=project_id, user_id=user_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    if member.role == MemberRole.owner:
        raise HTTPException(status_code=403, detail="Cannot change the owner's role")
    old_role = member.role
    member.role = req.role
    db.commit()
    db.refresh(project)

    if user_id != current_user.id:
        notify(
            db, user_id,
            type="role_changed",
            title=f"Your role in \"{project.name}\" changed to {req.role}",
            body=f"Previously: {old_role}",
            link=f"/projects/{project_id}",
            actor_id=current_user.id,
            project_id=project_id,
        )
        db.commit()

    return project


@router.delete("/{project_id}/members/{user_id}", response_model=ProjectOut)
def remove_member(project_id: int, user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = get_project_or_404(project_id, db)
    require_admin_or_owner(project, current_user, db)
    member = db.query(ProjectMember).filter_by(project_id=project_id, user_id=user_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    if member.role == MemberRole.owner:
        raise HTTPException(status_code=403, detail="Cannot remove the project owner")
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot remove yourself")
    db.delete(member)
    db.commit()
    db.refresh(project)
    return project
