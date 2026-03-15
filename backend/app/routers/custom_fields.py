"""
Custom Fields — P2.
Admins define fields; anyone with write access can set values on issues.
  GET/POST   /api/projects/{id}/fields/
  PATCH/DEL  /api/projects/{id}/fields/{fid}
  GET/PUT    /api/projects/{id}/issues/{iid}/fields/
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, Any
from pydantic import BaseModel
from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.issue import Issue
from app.models.custom_field import CustomField, CustomFieldValue, FieldType
from app.core.deps import get_current_user
from app.core.permissions import require_admin_or_owner, require_project_write

router = APIRouter(tags=["custom_fields"])

# ── Field definitions ─────────────────────────────────────────────────────────
fields_router = APIRouter(prefix="/api/projects/{project_id}/fields")


class FieldCreate(BaseModel):
    name: str
    field_type: FieldType
    options: Optional[list] = None
    required: bool = False


class FieldUpdate(BaseModel):
    name: Optional[str] = None
    options: Optional[list] = None
    required: Optional[bool] = None


def _get_project(pid: int, db: Session) -> Project:
    p = db.query(Project).filter(Project.id == pid).first()
    if not p:
        raise HTTPException(404, "Project not found")
    return p


def _check_member(project: Project, user: User):
    ids = {m.user_id for m in project.members} | {project.owner_id}
    if user.id not in ids:
        raise HTTPException(403, "Access denied")


def _serialize_field(f: CustomField) -> dict:
    return {
        "id": f.id, "name": f.name, "field_type": f.field_type.value,
        "options": f.options, "required": f.required,
        "created_at": f.created_at.isoformat() if f.created_at else None,
    }


@fields_router.get("/")
def list_fields(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = _get_project(project_id, db)
    _check_member(project, current_user)
    return [_serialize_field(f) for f in db.query(CustomField).filter_by(project_id=project_id).limit(200).all()]


@fields_router.post("/", status_code=201)
def create_field(project_id: int, body: FieldCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = _get_project(project_id, db)
    require_admin_or_owner(project, current_user, db)
    count = db.query(CustomField).filter_by(project_id=project_id).count()
    if count >= 20:
        raise HTTPException(400, "Maximum 20 custom fields per project")
    f = CustomField(project_id=project_id, name=body.name[:64], field_type=body.field_type,
                    options=body.options, required=body.required)
    db.add(f); db.commit(); db.refresh(f)
    return _serialize_field(f)


@fields_router.patch("/{field_id}")
def update_field(project_id: int, field_id: int, body: FieldUpdate,
                 db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = _get_project(project_id, db)
    require_admin_or_owner(project, current_user, db)
    f = db.query(CustomField).filter_by(id=field_id, project_id=project_id).first()
    if not f:
        raise HTTPException(404, "Field not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(f, k, v)
    db.commit(); db.refresh(f)
    return _serialize_field(f)


@fields_router.delete("/{field_id}", status_code=204)
def delete_field(project_id: int, field_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = _get_project(project_id, db)
    require_admin_or_owner(project, current_user, db)
    f = db.query(CustomField).filter_by(id=field_id, project_id=project_id).first()
    if not f:
        raise HTTPException(404, "Field not found")
    db.delete(f); db.commit()


# ── Issue field values ─────────────────────────────────────────────────────────
values_router = APIRouter(prefix="/api/projects/{project_id}/issues/{issue_id}/fields")


class SetFieldValue(BaseModel):
    field_id: int
    value: Any


@values_router.get("/")
def get_issue_fields(project_id: int, issue_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = _get_project(project_id, db)
    _check_member(project, current_user)
    issue = db.query(Issue).filter_by(id=issue_id, project_id=project_id).first()
    if not issue:
        raise HTTPException(404, "Issue not found")
    fields = db.query(CustomField).filter_by(project_id=project_id).all()
    values = {v.field_id: v.value for v in db.query(CustomFieldValue).filter_by(issue_id=issue_id).all()}
    return [{"field": _serialize_field(f), "value": values.get(f.id)} for f in fields]


@values_router.put("/")
def set_issue_fields(project_id: int, issue_id: int, body: list[SetFieldValue],
                     db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = _get_project(project_id, db)
    require_project_write(project, current_user, db)
    issue = db.query(Issue).filter_by(id=issue_id, project_id=project_id).first()
    if not issue:
        raise HTTPException(404, "Issue not found")
    for item in body:
        field = db.query(CustomField).filter_by(id=item.field_id, project_id=project_id).first()
        if not field:
            continue
        existing = db.query(CustomFieldValue).filter_by(field_id=item.field_id, issue_id=issue_id).first()
        if existing:
            existing.value = item.value
        else:
            db.add(CustomFieldValue(field_id=item.field_id, issue_id=issue_id, value=item.value))
    db.commit()
    return {"ok": True}


# Combine into single router export
router.include_router(fields_router)
router.include_router(values_router)
