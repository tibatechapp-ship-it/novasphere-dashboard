"""WebSocket endpoint with auth, metrics, and clean disconnect.

v0.3.1 fix: uses await ws.receive() instead of asyncio.sleep(ONE_HOUR)
to detect client disconnects immediately.
"""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.metrics import (
    ws_auth_failures_total,
    ws_connections_active,
    ws_messages_sent_total,
)
from app.core.security import decode_token

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """Tracks active WebSocket connections and broadcasts payloads."""

    def __init__(self) -> None:
        self._active: list[WebSocket] = []

    @property
    def active_connections(self) -> int:
        return len(self._active)

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._active.append(ws)
        ws_connections_active.set(len(self._active))

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self._active:
            self._active.remove(ws)
            ws_connections_active.set(len(self._active))

    async def broadcast(self, payload: dict) -> None:
        dead: list[WebSocket] = []
        for ws in list(self._active):
            try:
                await ws.send_json(payload)
                ws_messages_sent_total.inc()
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    token = ws.cookies.get("ns_token") or ws.query_params.get("token")
    if not decode_token(token):
        ws_auth_failures_total.inc()
        await ws.close(code=4401)
        return

    await manager.connect(ws)
    try:
        # receive() blocks until the client sends anything OR disconnects.
        # On clean close, it returns {"type": "websocket.disconnect"}.
        # On abrupt close, it raises WebSocketDisconnect.
        while True:
            msg = await ws.receive()
            if msg.get("type") == "websocket.disconnect":
                break
    except WebSocketDisconnect:
        pass
    except Exception as exc:  # pragma: no cover
        logger.error("WebSocket error: %s", exc)
    finally:
        manager.disconnect(ws)
