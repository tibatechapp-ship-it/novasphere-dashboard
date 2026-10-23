"""NovaSphere Dashboard — FastAPI + WebSockets + Cyberpunk UI."""
from __future__ import annotations

import asyncio
import json
import random
import time
from pathlib import Path
from typing import Any

from fastapi import Cookie, FastAPI, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from auth import authenticate, create_user, get_user

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"

app = FastAPI(title="NovaSphere Dashboard", version="0.1.0")

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class ConnectionManager:
    def __init__(self) -> None:
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, payload: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        for ws in list(self.active):
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()

AGENTS = [
    {"id": "A01", "name": "Profiler", "group": "core"},
    {"id": "A02", "name": "Analyst", "group": "core"},
    {"id": "A03", "name": "Critic", "group": "core"},
    {"id": "A04", "name": "Architect", "group": "planning"},
    {"id": "A05", "name": "Planner", "group": "planning"},
    {"id": "A06", "name": "Designer", "group": "planning"},
    {"id": "A07", "name": "Tester", "group": "quality"},
    {"id": "A08", "name": "Reviewer", "group": "quality"},
    {"id": "A09", "name": "Debugger", "group": "quality"},
    {"id": "A10", "name": "DevOps", "group": "ops"},
]


def _random_metrics() -> dict[str, Any]:
    return {
        "ts": time.time(),
        "cpu": round(random.uniform(5, 95), 1),
        "mem": round(random.uniform(20, 85), 1),
        "req_per_sec": random.randint(10, 400),
        "latency_ms": random.randint(5, 120),
        "agents": [
            {
                "id": a["id"],
                "name": a["name"],
                "group": a["group"],
                "status": random.choice(["online", "online", "online", "busy", "idle"]),
                "load": random.randint(0, 100),
                "tasks": random.randint(0, 50),
            }
            for a in AGENTS
        ],
        "events": [
            {
                "ts": time.time() - random.uniform(0, 30),
                "level": random.choice(["info", "info", "warn", "error"]),
                "msg": random.choice(
                    [
                        "Agent A03 completed task #42",
                        "WebSocket client connected",
                        "CPU spike detected",
                        "Memory threshold 80%",
                        "New agent registered",
                        "Task queue drained",
                    ]
                ),
            }
            for _ in range(5)
        ],
    }


@app.get("/login", response_class=HTMLResponse)
async def login_page() -> HTMLResponse:
    html_path = STATIC_DIR / "login.html"
    if html_path.exists():
        return HTMLResponse(html_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Login</h1>")


@app.get("/", response_class=HTMLResponse, response_model=None)
async def index(ns_token: str | None = Cookie(default=None)) -> HTMLResponse | RedirectResponse:
    if not get_user(ns_token):
        return RedirectResponse(url="/login", status_code=303)
    html_path = STATIC_DIR / "index.html"
    if html_path.exists():
        return HTMLResponse(html_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>NovaSphere</h1><p>static/index.html missing</p>")


@app.post("/api/auth/signup", response_model=None)
async def signup(username: str = Form(...), password: str = Form(...)):
    ok, msg = create_user(username, password)
    if not ok:
        return {"ok": False, "error": msg}
    resp = RedirectResponse(url="/", status_code=303)
    resp.set_cookie("ns_token", msg, httponly=True, samesite="lax", max_age=86400)
    return {"ok": True, "token": msg}


@app.post("/api/auth/login", response_model=None)
async def login(username: str = Form(...), password: str = Form(...)):
    token = authenticate(username, password)
    if not token:
        return {"ok": False, "error": "invalid credentials"}
    resp = RedirectResponse(url="/", status_code=303)
    resp.set_cookie("ns_token", token, httponly=True, samesite="lax", max_age=86400)
    return {"ok": True, "token": token}


@app.post("/api/auth/logout", response_model=None)
async def logout():
    resp = RedirectResponse(url="/login", status_code=303)
    resp.delete_cookie("ns_token")
    return {"ok": True}


@app.get("/api/auth/me")
async def me(ns_token: str | None = Cookie(default=None)):
    user = get_user(ns_token)
    if not user:
        return {"ok": False, "error": "not authenticated"}
    return {"ok": True, "username": user}


@app.get("/api/health")
async def health() -> dict[str, Any]:
    return {"ok": True, "service": "novasphere", "version": "0.1.0", "clients": len(manager.active)}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await manager.connect(ws)
    try:
        while True:
            await ws.send_json(_random_metrics())
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception:
        manager.disconnect(ws)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
