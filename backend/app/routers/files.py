import re
"""
File attachments — P2.
Stores files in /uploads volume (S3-ready: swap save/serve logic for boto3).
  POST   /api/projects/{pid}/issues/{iid}/attachments/   → upload
  GET    /api/projects/{pid}/issues/{iid}/attachments/   → list
  GET    .../attachments/{id}/download                   → download
  DELETE .../attachments/{id}                            → delete
"""
import os
import uuid
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.project import Project, ProjectMember, MemberRole
from app.models.issue import Issue
from app.models.attachment import Attachment
from app.core.deps import get_current_user
from app.core.permissions import require_project_write

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/uploads")
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_MIME = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "application/pdf", "text/plain", "text/csv",
    "application/zip",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "video/mp4", "video/webm",
}

os.makedirs(UPLOAD_DIR, exist_ok=True)


def _sanitize_filename(name: str) -> str:
    """Strip non-ASCII, path separators and quote chars to prevent
    Content-Disposition header injection (OWASP A03)."""
    # Keep only safe chars
    safe = re.sub(r'[^\w\s\-\.()]', '_', name, flags=re.ASCII)
    safe = safe.strip().strip('.')[:200] or 'file'
    return safe

router = APIRouter(prefix="/api/projects/{project_id}/issues/{issue_id}/attachments", tags=["files"])


def _check_access(project_id: int, issue_id: int, user: User, db: Session):
    issue = db.query(Issue).filter(Issue.id == issue_id, Issue.project_id == project_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    ids = {m.user_id for m in project.members} | {project.owner_id}
    if user.id not in ids:
        raise HTTPException(status_code=403, detail="Access denied")
    return project, issue


@router.get("/")
def list_attachments(
    project_id: int, issue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_access(project_id, issue_id, current_user, db)
    return [_serialize(a) for a in db.query(Attachment).filter(Attachment.issue_id == issue_id).limit(100).all()]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    project_id: int, issue_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project, _ = _check_access(project_id, issue_id, current_user, db)
    require_project_write(project, current_user, db)

    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(status_code=415, detail=f"File type not allowed: {file.content_type}")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds 50 MB limit")

    ext = os.path.splitext(file.filename or "")[-1].lower()[:10]
    stored_name = f"{uuid.uuid4().hex}{ext}"
    dest = os.path.join(UPLOAD_DIR, stored_name)

    async with aiofiles.open(dest, "wb") as f:
        await f.write(content)

    a = Attachment(
        issue_id=issue_id, uploader_id=current_user.id,
        filename=_sanitize_filename(file.filename or 'file'), stored_name=stored_name,
        content_type=file.content_type, size_bytes=len(content),
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return _serialize(a)


@router.get("/{attachment_id}/download")
def download_attachment(
    project_id: int, issue_id: int, attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_access(project_id, issue_id, current_user, db)
    a = db.query(Attachment).filter(Attachment.id == attachment_id, Attachment.issue_id == issue_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Attachment not found")
    path = os.path.join(UPLOAD_DIR, a.stored_name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    safe_name = _sanitize_filename(a.filename)
    return FileResponse(path, media_type=a.content_type, filename=safe_name, headers={'X-Content-Type-Options': 'nosniff'})


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
    project_id: int, issue_id: int, attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project, _ = _check_access(project_id, issue_id, current_user, db)
    require_project_write(project, current_user, db)
    a = db.query(Attachment).filter(Attachment.id == attachment_id, Attachment.issue_id == issue_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Attachment not found")
    member = db.query(ProjectMember).filter_by(project_id=project_id, user_id=current_user.id).first()
    if a.uploader_id != current_user.id and (not member or member.role not in (MemberRole.admin, MemberRole.owner)):
        raise HTTPException(status_code=403, detail="Only the uploader or an admin can delete attachments")
    path = os.path.join(UPLOAD_DIR, a.stored_name)
    if os.path.exists(path):
        os.remove(path)
    db.delete(a)
    db.commit()


def _serialize(a: Attachment) -> dict:
    return {
        "id":           a.id,
        "filename":     a.filename,
        "content_type": a.content_type,
        "size_bytes":   a.size_bytes,
        "created_at":   a.created_at.isoformat() if a.created_at else None,
        "uploader":     {"id": a.uploader.id, "full_name": a.uploader.full_name} if a.uploader else None,
    }
