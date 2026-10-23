"""Authentication endpoints with per-route rate limits."""

import logging

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.metrics import auth_attempts_total
from app.core.rate_limit import limiter
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()


def _create_user(db: Session, username: str, password: str) -> User:
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="username already exists")
    user = User(username=username, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _authenticate(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    return user if verify_password(password, user.password_hash) else None


def _set_cookie(resp: JSONResponse, token: str) -> None:
    s = get_settings()
    resp.set_cookie(
        "ns_token",
        token,
        httponly=True,
        secure=s.is_production,
        samesite="strict" if s.is_production else "lax",
        max_age=s.access_token_expire_minutes * 60,
        path="/",
    )


@router.post("/signup")
@limiter.limit("5/minute")
async def signup(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    if not (3 <= len(username) <= 32):
        raise HTTPException(status_code=400, detail="username 3-32 chars")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="password >= 6 chars")

    try:
        user = _create_user(db, username, password)
    except HTTPException:
        auth_attempts_total.labels(endpoint="signup", result="exists").inc()
        raise

    auth_attempts_total.labels(endpoint="signup", result="ok").inc()
    token = create_access_token({"sub": user.username})
    resp = JSONResponse({"ok": True, "token": token})
    _set_cookie(resp, token)
    return resp


@router.post("/login")
@limiter.limit("10/minute")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = _authenticate(db, username, password)
    if not user:
        auth_attempts_total.labels(endpoint="login", result="fail").inc()
        raise HTTPException(status_code=401, detail="invalid credentials")

    auth_attempts_total.labels(endpoint="login", result="ok").inc()
    token = create_access_token({"sub": user.username})
    resp = JSONResponse({"ok": True, "token": token})
    _set_cookie(resp, token)
    return resp


@router.post("/logout")
async def logout():
    resp = JSONResponse({"ok": True})
    resp.delete_cookie("ns_token", path="/")
    return resp
