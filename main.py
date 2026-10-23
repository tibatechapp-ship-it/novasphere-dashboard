"""NovaSphere Dashboard — FastAPI + WebSockets + Cyberpunk UI."""
from __future__ import annotations

import asyncio
import json
import logging
import random
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import Cookie, FastAPI, Form, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from auth import authenticate, create_user, get_user
from config import ACCESS_TOKEN_EXPIRE_MINUTES
from database import Base, SessionLocal, engine
from models import Event, User
from ws import ConnectionManager

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"

manager = ConnectionManager()

# Simple in-memory rate limiter (fixed window per IP)
import time as _rl_time
_RL_BUCKET: dict[str, list[float]] = {}
_RL_LIMIT = 20
_RL_WINDOW = 60.0


def _check_rate_limit(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    now = _rl_time.time()
    bucket = _RL_BUCKET.setdefault(ip, [])
    # drop old
    bucket[:] = [t for t in bucket if now - t < _RL_WINDOW]
    if len(bucket) >= _RL_LIMIT:
        from fastapi import HTTPException
        raise HTTPException(status_code=429, detail="too many requests")
    bucket.append(now)

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
    cpu = round(random.uniform(5, 95), 1)
    mem = round(random.uniform(20, 85), 1)
    rps = random.randint(10, 400)
    lat = random.randint(5, 120)
    events = []
    msgs = [
        "Agent A03 completed task #42",
        "WebSocket client connected",
        "CPU spike detected",
        "Memory threshold 80%",
        "New agent registered",
        "Task queue drained",
        "Crypto price tick: BTC/USD",
        "Server temperature nominal",
    ]
    for _ in range(5):
        lvl = random.choice(["info", "info", "warn", "error"])
        events.append({"ts": time.time() - random.uniform(0, 30), "level": lvl, "msg": random.choice(msgs)})
    return {
        "ts": time.time(),
        "cpu": cpu,
        "mem": mem,
        "req_per_sec": rps,
        "latency_ms": lat,
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
        "events": events,
    }


async def background_generator() -> None:
    """Broadcast live metrics every second (only if MOCK_DATA enabled)."""
    from config import MOCK_DATA
    if not MOCK_DATA:
        logging.info("MOCK_DATA disabled; background generator stopped.")
        return
    while True:
        payload = _random_metrics()
        try:
            db: Session = SessionLocal()
            for ev in payload["events"][:2]:
                db.add(Event(level=ev["level"], message=ev["msg"], metric_cpu=payload["cpu"], metric_mem=payload["mem"], metric_rps=payload["req_per_sec"]))
            db.commit()
            db.close()
        except Exception as exc:
            logging.error("background_generator persist failed: %s", exc)
        await manager.broadcast(payload)
        await asyncio.sleep(1.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    task = asyncio.create_task(background_generator())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="NovaSphere Dashboard", version="0.2.0", lifespan=lifespan)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# Security: CORS (restrictive by default)
import os as _os
_allowed = _os.getenv("CORS_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _allowed if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

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
async def signup(request: Request, username: str = Form(...), password: str = Form(...)):
    _check_rate_limit(request)
    username = (username or "").strip()
    if len(username) < 3 or len(username) > 32:
        return {"ok": False, "error": "username must be 3-32 chars"}
    if len(password or "") < 6:
        return {"ok": False, "error": "password must be at least 6 chars"}
    ok, msg = create_user(username, password)
    if not ok:
        return {"ok": False, "error": msg}
    resp = JSONResponse({"ok": True, "token": msg})
    resp.set_cookie("ns_token", msg, httponly=True, samesite="lax", max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    return resp


@app.post("/api/auth/login", response_model=None)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    _check_rate_limit(request)
    token = authenticate(username, password)
    if not token:
        return {"ok": False, "error": "invalid credentials"}
    resp = JSONResponse({"ok": True, "token": token})
    resp.set_cookie("ns_token", token, httponly=True, samesite="lax", max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    return resp


@app.post("/api/auth/logout", response_model=None)
async def logout():
    resp = JSONResponse({"ok": True})
    resp.delete_cookie("ns_token")
    return resp


@app.get("/api/auth/me")
async def me(ns_token: str | None = Cookie(default=None)):
    user = get_user(ns_token)
    if not user:
        return {"ok": False, "error": "not authenticated"}
    return {"ok": True, "username": user}


@app.get("/api/health")
async def health() -> dict[str, Any]:
    return {"ok": True, "service": "novasphere", "version": "0.2.0", "clients": manager.count}


@app.get("/api/events")
async def recent_events(limit: int = 10, ns_token: str | None = Cookie(default=None)):
    if not get_user(ns_token):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="not authenticated")
    db: Session = SessionLocal()
    try:
        rows = db.query(Event).order_by(Event.ts.desc()).limit(limit).all()
        return {"ok": True, "events": [
            {"id": r.id, "ts": r.ts.timestamp(), "level": r.level, "msg": r.message} for r in rows
        ]}
    finally:
        db.close()


@app.post("/api/insights", response_model=None)
async def insights(request: Request, payload: dict[str, Any], ns_token: str | None = Cookie(default=None)):
    _check_rate_limit(request)
    if not get_user(ns_token):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="not authenticated")
    events = payload.get("events", []) or []
    metrics = payload.get("metrics", {}) or {}
    last = events[-10:]
    levels: dict[str, int] = {}
    for ev in last:
        lvl = ev.get("level", "info")
        levels[lvl] = levels.get(lvl, 0) + 1
    msgs = [str(ev.get("msg", "")) for ev in last]
    cpu = metrics.get("cpu")
    mem = metrics.get("mem")
    rps = metrics.get("req_per_sec")
    lat = metrics.get("latency_ms")
    insights: list[str] = []
    if levels.get("error", 0) > 0:
        insights.append(f"Detected {levels['error']} error event(s) in the last 10 — investigate immediately.")
    if levels.get("warn", 0) > 0:
        insights.append(f"{levels['warn']} warning(s) observed — review event log.")
    if cpu is not None and cpu > 80:
        insights.append(f"CPU is high ({cpu}%) — consider scaling or throttling agents.")
    if mem is not None and mem > 80:
        insights.append(f"Memory pressure ({mem}%) — check for leaks or reduce load.")
    if lat is not None and lat > 90:
        insights.append(f"Latency elevated ({lat}ms) — optimize hot paths.")
    if rps is not None and rps > 300:
        insights.append(f"High throughput ({rps} req/s) — ensure rate limits are in place.")
    if not insights:
        insights.append("System looks healthy — no anomalies in the last 10 events.")
    return {
        "ok": True,
        "summary": " | ".join(insights),
        "insights": insights,
        "stats": {"events": len(last), "levels": levels, "cpu": cpu, "mem": mem, "rps": rps, "latency": lat},
    }


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    # Auth via cookie or query token
    token = ws.cookies.get("ns_token") or ws.query_params.get("token")
    if not get_user(token):
        await ws.close(code=4401)
        return
    await manager.connect(ws)
    try:
        while True:
            await asyncio.sleep(3600)
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception:
        manager.disconnect(ws)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)