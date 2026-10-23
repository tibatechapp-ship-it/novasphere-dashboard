"""Security primitives: password hashing (bcrypt) + JWT (stdlib only).

Uses hmac + base64 instead of PyJWT to avoid the cryptography
dependency that is broken on Termux/Python 3.14.
"""

import base64
import hashlib
import hmac
import json
import time
from datetime import UTC, datetime, timedelta

import bcrypt

from app.core.config import get_settings


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    # Add padding
    pad = 4 - (len(s) % 4)
    if pad != 4:
        s += "=" * pad
    return base64.urlsafe_b64decode(s)


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt (cost=12)."""
    if not password or len(password) < 6:
        raise ValueError("password too short")
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Constant-time password verification."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(data: dict) -> str:
    """Create a signed JWT (HS256) with an expiry claim."""
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode["exp"] = expire.timestamp()

    header = {"alg": settings.jwt_algorithm, "typ": "JWT"}
    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64url_encode(json.dumps(to_encode, separators=(",", ":"), default=str).encode())

    # HMAC-SHA256 signature
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signature = hmac.new(
        settings.jwt_secret_key.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    sig_b64 = _b64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_token(token: str | None) -> dict | None:
    """Decode and verify a JWT. Returns None on any failure."""
    if not token:
        return None
    settings = get_settings()
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, sig_b64 = parts

        # Verify signature
        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        expected_sig = hmac.new(
            settings.jwt_secret_key.encode("utf-8"),
            signing_input,
            hashlib.sha256,
        ).digest()
        if not hmac.compare_digest(expected_sig, _b64url_decode(sig_b64)):
            return None

        # Decode payload
        payload = json.loads(_b64url_decode(payload_b64))

        # Check expiry
        exp = payload.get("exp")
        if exp is not None and time.time() > exp:
            return None

        # Check algorithm
        header = json.loads(_b64url_decode(header_b64))
        if header.get("alg") != settings.jwt_algorithm:
            return None

        return payload
    except Exception:
        return None
