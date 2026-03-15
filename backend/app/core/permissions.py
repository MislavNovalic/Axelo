"""
Role-based permission helpers.
Viewer role is read-only. Member and above can write.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.project import Project, ProjectMember, MemberRole
from app.models.user import User


def _get_member(project: Project, user: User, db: Session) -> ProjectMember | None:
    return db.query(ProjectMember).filter_by(
        project_id=project.id, user_id=user.id
    ).first()


def require_project_write(project: Project, user: User, db: Session):
    """Raise 403 if user is a viewer or not a member."""
    member = _get_member(project, user, db)
    if not member:
        raise HTTPException(status_code=403, detail="Access denied")
    if member.role == MemberRole.viewer:
        raise HTTPException(status_code=403, detail="Viewers cannot make changes")


def require_admin_or_owner(project: Project, user: User, db: Session):
    member = _get_member(project, user, db)
    if not member or member.role not in (MemberRole.owner, MemberRole.admin):
        raise HTTPException(status_code=403, detail="Admin or Owner role required")


def validate_assignee_is_member(project: Project, assignee_id: int | None, db: Session):
    """A01 FIX: Ensure the assignee actually belongs to the project."""
    if assignee_id is None:
        return
    member_ids = {m.user_id for m in project.members} | {project.owner_id}
    if assignee_id not in member_ids:
        raise HTTPException(status_code=422, detail="Assignee is not a project member")
