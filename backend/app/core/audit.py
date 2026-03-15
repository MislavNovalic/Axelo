"""Thin helpers for writing audit log entries."""
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog


def audit(
    db: Session,
    project_id: int,
    user_id: int | None,
    entity_type: str,
    action: str,
    entity_id: int | None = None,
    entity_key: str | None = None,
    diff: dict | None = None,
    description: str | None = None,
):
    entry = AuditLog(
        project_id=project_id,
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_key=entity_key,
        action=action,
        diff=diff,
        description=description,
    )
    db.add(entry)
    # caller must commit
    return entry
