import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.auth import decode_token
from app.database import SessionLocal
from app.models.user import User
from app.models.project import Project

logger = logging.getLogger("axelo.ws")
router = APIRouter(tags=["websocket"])


class ConnectionManager:
    """In-memory WebSocket connection manager.

    Tracks connections per project so we can broadcast project events
    to all connected members without Redis. (Single-server only.)
    Also tracks per-user connections for personal notification delivery.
    """

    def __init__(self):
        # project_id → list of (websocket, user_id)
        self._project_sockets: dict[int, list[tuple[WebSocket, int]]] = {}
        # user_id → list of websockets (personal notifications)
        self._user_sockets: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, project_id: int, user_id: int):
        await websocket.accept()
        self._project_sockets.setdefault(project_id, []).append((websocket, user_id))
        self._user_sockets.setdefault(user_id, []).append(websocket)

    def disconnect(self, websocket: WebSocket, project_id: int, user_id: int):
        self._project_sockets.setdefault(project_id, [])
        self._project_sockets[project_id] = [
            (ws, uid) for ws, uid in self._project_sockets[project_id]
            if ws is not websocket
        ]
        self._user_sockets.setdefault(user_id, [])
        self._user_sockets[user_id] = [
            ws for ws in self._user_sockets[user_id] if ws is not websocket
        ]

    async def broadcast_project(self, project_id: int, event: str, data: dict, exclude_user: int | None = None):
        """Send an event to all connections in a project."""
        message = json.dumps({"event": event, "data": data})
        dead = []
        for ws, uid in self._project_sockets.get(project_id, []):
            if exclude_user is not None and uid == exclude_user:
                continue
            try:
                await ws.send_text(message)
            except Exception:
                dead.append((ws, uid))
        # Clean up dead sockets
        for ws, uid in dead:
            self._project_sockets[project_id] = [
                (w, u) for w, u in self._project_sockets[project_id]
                if w is not ws
            ]

    async def send_to_user(self, user_id: int, event: str, data: dict):
        """Send an event to all connections of a specific user."""
        message = json.dumps({"event": event, "data": data})
        dead = []
        for ws in self._user_sockets.get(user_id, []):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._user_sockets[user_id] = [
                w for w in self._user_sockets[user_id] if w is not ws
            ]


# Singleton shared across the app
manager = ConnectionManager()


@router.websocket("/ws/{project_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    project_id: int,
    token: str = Query(...),
):
    """WebSocket endpoint for real-time project collaboration.

    Authentication: pass JWT as query param ?token=<jwt>
    The token is validated before accepting the connection.
    """
    # Validate JWT before accepting
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = int(payload.get("sub", 0))

    # Check project access
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            await websocket.close(code=4001, reason="User not found")
            return

        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            await websocket.close(code=4004, reason="Project not found")
            return

        member_ids = [m.user_id for m in project.members] + [project.owner_id]
        if user_id not in member_ids:
            await websocket.close(code=4003, reason="Access denied")
            return
    finally:
        db.close()

    await manager.connect(websocket, project_id, user_id)
    logger.info("WS connected: user=%d project=%d", user_id, project_id)

    try:
        while True:
            # Keep connection alive; client can send pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id, user_id)
        logger.info("WS disconnected: user=%d project=%d", user_id, project_id)
