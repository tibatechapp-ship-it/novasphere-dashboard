"""Pytest fixtures: isolated DB + ASGI client + seeded user.

CRITICAL: os.environ MUST be set at module import time, BEFORE any
import of `app.*`, otherwise `get_settings()`'s lru_cache captures the
real `.env` and tests pollute the production DB.
"""

import os
import tempfile
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Environment MUST be set before importing any app module.
_TMP_DIR = tempfile.mkdtemp(prefix="raqib-test-")
_DB_FILE = Path(_TMP_DIR) / "test.db"

os.environ["DATABASE_URL"] = f"sqlite:///{_DB_FILE}"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-32-chars-minimum-abcdef"
os.environ["ENV"] = "development"
os.environ["MOCK_DATA"] = "false"
os.environ["REDIS_URL"] = "redis://localhost:6399/15"


def pytest_configure(config):
    """Clear any settings cached by modules imported during collection."""
    try:
        from app.core.config import get_settings

        get_settings.cache_clear()
    except ImportError:
        pass


@pytest.fixture(scope="session")
def app():
    from app.db.base import Base
    from app.db.session import engine
    from app.main import create_app

    # Ensure tables exist (ASGITransport does not trigger lifespan)
    Base.metadata.create_all(bind=engine)
    return create_app()


@pytest_asyncio.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def registered_user(client: AsyncClient):
    resp = await client.post(
        "/api/auth/signup",
        data={"username": "testuser", "password": "secret123"},
    )
    if resp.status_code == 400:
        resp = await client.post(
            "/api/auth/login",
            data={"username": "testuser", "password": "secret123"},
        )
    assert resp.status_code == 200, resp.text
    token = resp.json()["token"]
    client.cookies.set("ns_token", token)
    return {"username": "testuser", "token": token}


@pytest.fixture
def db_session():
    """Direct DB session for assertions — same DB the app uses."""
    from app.db.session import SessionLocal
    from app.models.audit_log import AuditLog

    db = SessionLocal()
    # Clean up any leftover rows from previous tests
    db.query(AuditLog).delete()
    db.commit()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture(autouse=True)
def _clean_audit_log():
    """Ensure audit_log table is empty before each test (HTTP tests commit via app session)."""
    from app.db.base import Base
    from app.db.session import SessionLocal, engine
    from app.models.audit_log import AuditLog

    # Ensure tables exist (app fixture may not have run yet)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        db.query(AuditLog).delete()
        db.commit()
    finally:
        db.close()
    yield


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Clear rate limiter storage between tests (memory + Redis)."""
    _clear_limiter()
    yield
    _clear_limiter()


def _clear_limiter() -> None:
    """Best-effort cleanup of slowapi keys in Redis or memory."""
    try:
        import redis

        from app.core.config import get_settings

        r = redis.from_url(get_settings().redis_url, decode_responses=True)
        for pattern in ("LIMITER/*", "slowapi/*"):
            for key in r.scan_iter(pattern, count=100):
                r.delete(key)
    except Exception:
        try:
            from app.core.rate_limit import limiter

            storage = getattr(limiter, "_storage", None)
            if storage is not None and hasattr(storage, "storage"):
                storage.storage.clear()
        except Exception:
            pass


@pytest.fixture(scope="session")
def sync_client(app):
    """Starlette TestClient for WebSocket tests."""
    from fastapi.testclient import TestClient

    return TestClient(app)
