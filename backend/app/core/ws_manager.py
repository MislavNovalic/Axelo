"""
WebSocket connection manager.
Maintains a mapping of user_id -> set of active WebSocket connections.
All routers import `manager` and call `manager.broadcast_to_project(...)`.
"""
import asyncio
import json
from typing import Dict, Set
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # project_id -> { user_id -> set[WebSocket] }
        self._project_connections: Dict[int, Dict[int, Set[WebSocket]]] = {}
        # user_id -> set[WebSocket]  (for user-specific notifications)
        self._user_connections: Dict[int, Set[WebSocket]] = {}

    # ── connect / disconnect ──────────────────────────────────────────────────

    def connect(self, websocket: WebSocket, user_id: int, project_id: int | None = None):
        if project_id is not None:
            self._project_connections.setdefault(project_id, {})
            self._project_connections[project_id].setdefault(user_id, set())
            self._project_connections[project_id][user_id].add(websocket)

        self._user_connections.setdefault(user_id, set())
        self._user_connections[user_id].add(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int, project_id: int | None = None):
        if project_id is not None:
            sockets = self._project_connections.get(project_id, {}).get(user_id, set())
            sockets.discard(websocket)

        sockets = self._user_connections.get(user_id, set())
        sockets.discard(websocket)

    # ── broadcast helpers ─────────────────────────────────────────────────────

    async def _send(self, websocket: WebSocket, payload: dict):
        try:
            await websocket.send_text(json.dumps(payload))
        except Exception:
            pass  # connection already closed

    async def broadcast_to_project(self, project_id: int, payload: dict, exclude_user_id: int | None = None):
        """Send to everyone in the project room (except optionally the actor)."""
        for uid, sockets in self._project_connections.get(project_id, {}).items():
            if uid == exclude_user_id:
                continue
            for ws in list(sockets):
                await self._send(ws, payload)

    async def send_to_user(self, user_id: int, payload: dict):
        """Send to all connections of a specific user (notification delivery)."""
        for ws in list(self._user_connections.get(user_id, set())):
            await self._send(ws, payload)


manager = ConnectionManager()
