"""
Issue Templates — P1.
Admins define reusable templates per project; users pick them when creating issues.
  GET    /api/projects/{id}/templates/
  POST   /api/projects/{id}/templates/
  PATCH  /api/projects/{id}/templates/{tid}
  DELETE /api/projects/{id}/templates/{tid}
  GET    /api/projects/{id}/templates/{tid}   → prefill data for CreateIssueModal
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.issue import IssueType, IssuePriority
from app.models.issue_template import IssueTemplate
from app.core.deps import get_current_user
from app.core.permissions import require_admin_or_owner
from app.core.security import clamp_str

router = APIRouter(prefix="/api/projects/{project_id}/templates", tags=["templates"])


class TemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    type: IssueType = IssueType.task
    priority: IssuePriority = IssuePriority.medium
    title_template: Optional[str] = None
    body_template: Optional[str] = None


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[IssueType] = None
    priority: Optional[IssuePriority] = None
    title_template: Optional[str] = None
    body_template: Optional[str] = None


def _get_project(project_id: int, db: Session) -> Project:
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return p


def _check_member(project: Project, user: User):
    ids = {m.user_id for m in project.members} | {project.owner_id}
    if user.id not in ids:
        raise HTTPException(status_code=403, detail="Access denied")


def _serialize(t: IssueTemplate) -> dict:
    return {
        "id":             t.id,
        "name":           t.name,
        "description":    t.description,
        "type":           t.type.value,
        "priority":       t.priority.value,
        "title_template": t.title_template,
        "body_template":  t.body_template,
        "created_at":     t.created_at.isoformat() if t.created_at else None,
    }


@router.get("/")
def list_templates(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_project(project_id, db)
    _check_member(project, current_user)
    templates = db.query(IssueTemplate).filter(IssueTemplate.project_id == project_id).limit(200).all()
    return [_serialize(t) for t in templates]


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_template(
    project_id: int,
    body: TemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_project(project_id, db)
    require_admin_or_owner(project, current_user, db)
    t = IssueTemplate(
        project_id=project_id,
        created_by=current_user.id,
        name=clamp_str(body.name, 128),
        description=clamp_str(body.description, 512),
        type=body.type,
        priority=body.priority,
        title_template=clamp_str(body.title_template, 512),
        body_template=clamp_str(body.body_template, 50_000),
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return _serialize(t)


@router.get("/{template_id}")
def get_template(
    project_id: int, template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_project(project_id, db)
    _check_member(project, current_user)
    t = db.query(IssueTemplate).filter(IssueTemplate.id == template_id, IssueTemplate.project_id == project_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return _serialize(t)


@router.patch("/{template_id}")
def update_template(
    project_id: int, template_id: int,
    body: TemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_project(project_id, db)
    require_admin_or_owner(project, current_user, db)
    t = db.query(IssueTemplate).filter(IssueTemplate.id == template_id, IssueTemplate.project_id == project_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(t, field, value)
    db.commit()
    db.refresh(t)
    return _serialize(t)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    project_id: int, template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_project(project_id, db)
    require_admin_or_owner(project, current_user, db)
    t = db.query(IssueTemplate).filter(IssueTemplate.id == template_id, IssueTemplate.project_id == project_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(t)
    db.commit()
