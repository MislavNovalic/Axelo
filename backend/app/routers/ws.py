"""
WebSocket endpoint + REST endpoints for notifications.
WS URL: ws://host/api/ws?token=<jwt>
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.core.ws_manager import manager
from app.core.auth import verify_token
from app.core.deps import get_current_user
from app.models.notification import Notification
from app.models.user import User

router = APIRouter(tags=["websocket"])


# ── WebSocket ────────────────────────────────────────────────────────────────

@router.websocket("/api/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    project_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    # Authenticate via token query param (headers aren't supported in WS)
    user_data = verify_token(token)
    if not user_data:
        await websocket.close(code=4001)
        return

    user_id = user_data.get("sub")
    if not user_id:
        await websocket.close(code=4001)
        return

    user_id = int(user_id)
    await websocket.accept()
    manager.connect(websocket, user_id, project_id)

    try:
        while True:
            # Keep connection alive; client can send pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id, project_id)


# ── Notifications REST ────────────────────────────────────────────────────────

@router.get("/api/notifications")
def list_notifications(
    limit: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .all()
    )
    return [_serialize(n, db) for n in notifications]


@router.get("/api/notifications/unread-count")
def unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.read == False,
    ).count()
    return {"count": count}


@router.patch("/api/notifications/{notif_id}/read")
def mark_read(
    notif_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    n = db.query(Notification).filter(
        Notification.id == notif_id,
        Notification.user_id == current_user.id,
    ).first()
    if not n:
        raise HTTPException(status_code=404)
    n.read = True
    db.commit()
    return {"ok": True}


@router.post("/api/notifications/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.read == False,
    ).update({"read": True})
    db.commit()
    return {"ok": True}


def _serialize(n: Notification, db: Session):
    actor = db.query(User).filter(User.id == n.actor_id).first() if n.actor_id else None
    return {
        "id":         n.id,
        "type":       n.type,
        "title":      n.title,
        "body":       n.body or "",
        "link":       n.link or "",
        "read":       n.read,
        "actor":      {"id": actor.id, "full_name": actor.full_name} if actor else None,
        "project_id": n.project_id,
        "issue_id":   n.issue_id,
        "created_at": n.created_at.isoformat() if n.created_at else None,
    }
