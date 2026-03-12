from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.user import User
from app.models.project import Project, ProjectMember, MemberRole
from app.models.template import IssueTemplate
from app.schemas.template import TemplateCreate, TemplateOut
from app.core.deps import get_current_user

router = APIRouter(prefix="/api/projects/{project_id}/templates", tags=["templates"])


def _get_project_and_check_access(project_id: int, user: User, db: Session) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    ids = [m.user_id for m in project.members] + [project.owner_id]
    if user.id not in ids:
        raise HTTPException(status_code=403, detail="Access denied")
    return project


def _require_member_or_above(project: Project, user: User, db: Session):
    """Viewers cannot create/delete templates."""
    member = db.query(ProjectMember).filter_by(project_id=project.id, user_id=user.id).first()
    if member and member.role == MemberRole.viewer:
        raise HTTPException(status_code=403, detail="Viewers cannot manage templates")


@router.get("/", response_model=List[TemplateOut])
def list_templates(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_project_and_check_access(project_id, current_user, db)
    return db.query(IssueTemplate).filter(IssueTemplate.project_id == project_id).all()


@router.post("/", response_model=TemplateOut, status_code=status.HTTP_201_CREATED)
def create_template(
    project_id: int,
    template_in: TemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_project_and_check_access(project_id, current_user, db)
    _require_member_or_above(project, current_user, db)
    template = IssueTemplate(
        **template_in.model_dump(),
        project_id=project_id,
        created_by_id=current_user.id,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    project_id: int,
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_project_and_check_access(project_id, current_user, db)
    _require_member_or_above(project, current_user, db)
    template = db.query(IssueTemplate).filter(
        IssueTemplate.id == template_id,
        IssueTemplate.project_id == project_id,
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(template)
    db.commit()
