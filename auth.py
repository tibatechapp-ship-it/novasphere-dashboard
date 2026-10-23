"""NovaSphere auth — JWT (HS256, stdlib) + bcrypt password hashing."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path
from typing import Any

import bcrypt

SECRET = os.environ.get("NOVASPHERE_SECRET", "novasphere-dev-secret-change-me")
JWT_ALG = "HS256"
TOKEN_TTL = 60 * 60 * 24  # 24h

USERS_FILE = Path(__file__).resolve().parent / "data" / "users.json"


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def create_token(username: str) -> str:
    header = {"alg": JWT_ALG, "typ": "JWT"}
    payload = {"sub": username, "iat": int(time.time()), "exp": int(time.time()) + TOKEN_TTL}
    h = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    p = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    sig = hmac.new(SECRET.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
    return f"{h}.{p}.{_b64url_encode(sig)}"


def verify_token(token: str) -> str | None:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        h, p, s = parts
        sig = hmac.new(SECRET.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
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


# ---- user store (file-backed) ----
def _load_users() -> dict[str, str]:
    try:
        if USERS_FILE.exists():
            return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _save_users(users: dict[str, str]) -> None:
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    USERS_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")


def create_user(username: str, password: str) -> tuple[bool, str]:
    username = username.strip()
    if not username or not password:
        return False, "username and password required"
    if len(password) < 4:
        return False, "password too short (min 4)"
    users = _load_users()
    if username in users:
        return False, "user already exists"
    users[username] = hash_password(password)
    _save_users(users)
    return True, create_token(username)


def authenticate(username: str, password: str) -> str | None:
    users = _load_users()
    hashed = users.get(username.strip())
    if not hashed:
        return None
    if not check_password(password, hashed):
        return None
    return create_token(username.strip())


def get_user(token: str | None) -> str | None:
    if not token:
        return None
    return verify_token(token)


def random_secret() -> str:
    return secrets.token_hex(32)
