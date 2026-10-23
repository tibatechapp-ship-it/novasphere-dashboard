"""Auth: JWT (HS256, stdlib) + bcrypt, backed by SQLAlchemy User model."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Optional

import bcrypt
from sqlalchemy.orm import Session

from config import ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY
from database import SessionLocal
from models import User


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def create_token(username: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": username,
        "iat": int(time.time()),
        "exp": int(time.time()) + ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }
    h = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    p = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    sig = hmac.new(SECRET_KEY.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
    return f"{h}.{p}.{_b64url_encode(sig)}"


def verify_token(token: Optional[str]) -> Optional[str]:
    if not token:
        return None
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        h, p, s = parts
        sig = hmac.new(SECRET_KEY.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(_b64url_encode(sig), s):
            return None
        payload = json.loads(_b64url_decode(p))
        if payload.get("exp", 0) < time.time():
            return None
        return payload.get("sub")
    except Exception:
        return None


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False


def get_db_session() -> Session:
    return SessionLocal()


def create_user(username: str, password: str) -> tuple[bool, str]:
    username = username.strip()
    if not username or not password:
        return False, "username and password required"
    if len(password) < 4:
        return False, "password too short (min 4)"
    db = get_db_session()
    try:
        if db.query(User).filter(User.username == username).first():
            return False, "user already exists"
        user = User(username=username, hashed_password=hash_password(password))
        db.add(user)
        db.commit()
        return True, create_token(username)
    finally:
        db.close()


def authenticate(username: str, password: str) -> Optional[str]:
    db = get_db_session()
    try:
        user = db.query(User).filter(User.username == username.strip()).first()
        if not user or not check_password(password, user.hashed_password):
            return None
        return create_token(username.strip())
    finally:
        db.close()


def get_user(token: Optional[str]) -> Optional[str]:
    return verify_token(token)