"""
Central notification factory.
Creates a Notification row and immediately pushes it to the recipient via WebSocket.
"""
import asyncio
from typing import Optional
from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.core.ws_manager import manager


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
):
    """Persist a notification and push it live to the user."""
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
    return notif


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


def notify(db, user_id, type, title, body="", link="", actor_id=None, project_id=None, issue_id=None):
    """Sync wrapper — can be called from regular (non-async) FastAPI route handlers."""
    _run(push_notification(db, user_id, type, title, body, link, actor_id, project_id, issue_id))
