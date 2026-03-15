"""
Central notification factory.
Creates a Notification row, pushes it live via WebSocket,
and enqueues an email notification via Redis/ARQ.
"""
import asyncio
import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.models.user import User
from app.core.ws_manager import manager

logger = logging.getLogger(__name__)


async def push_notification(
    db: Session,
    user_id: int,
    type: str,
    title: str,
    body: str = "",
    link: str = "",
    actor_id: Optional[int] = None,
    project_id: Optional[int] = None,
    issue_id: Optional[int] = None,
    actor_name: str = "",
    project_name: str = "",
):
    """Persist a notification, push it live via WebSocket, and queue an email."""
    notif = Notification(
        user_id=user_id,
        type=type,
        title=title,
        body=body,
        link=link,
        actor_id=actor_id,
        project_id=project_id,
        issue_id=issue_id,
    )
    db.add(notif)
    db.flush()   # get the id before commit

    # 1. WebSocket push (real-time in-app notification)
    payload = {
        "event": "notification",
        "data": {
            "id":         notif.id,
            "type":       notif.type,
            "title":      notif.title,
            "body":       notif.body,
            "link":       notif.link,
            "read":       False,
            "actor_id":   notif.actor_id,
            "project_id": notif.project_id,
            "issue_id":   notif.issue_id,
            "created_at": notif.created_at.isoformat() if notif.created_at else None,
        }
    }
    await manager.send_to_user(user_id, payload)

    # 2. Queue email notification via Redis/ARQ
    await _enqueue_notification_email(
        db=db,
        user_id=user_id,
        notification_type=type,
        title=title,
        body=body,
        link=link,
        actor_name=actor_name,
        project_name=project_name,
    )

    return notif


async def _enqueue_notification_email(
    db: Session,
    user_id: int,
    notification_type: str,
    title: str,
    body: str,
    link: str,
    actor_name: str,
    project_name: str,
) -> None:
    """Look up the recipient's email and enqueue the email job in Redis."""
    try:
        from app.core.queue import enqueue_email
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.email:
            return
        await enqueue_email(
            notification_type=notification_type,
            to_email=user.email,
            to_name=user.full_name or user.email,
            title=title,
            body=body,
            link=link,
            actor_name=actor_name,
            project_name=project_name,
        )
    except Exception:
        # Never let email queueing break the main notification flow
        logger.warning("Failed to enqueue notification email for user_id=%s", user_id)


def _run(coro):
    """Run an async coroutine from a sync context (used inside sync route handlers)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(coro)
        else:
            loop.run_until_complete(coro)
    except RuntimeError:
        asyncio.run(coro)


def notify(
    db, user_id, type, title, body="", link="",
    actor_id=None, project_id=None, issue_id=None,
    actor_name="", project_name="",
):
    """Sync wrapper — can be called from regular (non-async) FastAPI route handlers."""
    _run(push_notification(
        db, user_id, type, title, body, link,
        actor_id, project_id, issue_id,
        actor_name=actor_name, project_name=project_name,
    ))
