"""Rate limiting — isolated per test via Redis key cleanup."""

import pytest


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Clear limiter storage before AND after each test."""
    _clear_limiter_keys()
    yield
    _clear_limiter_keys()


def _clear_limiter_keys() -> None:
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


@pytest.mark.asyncio
async def test_login_rate_limit(client):
    """10/min limit → 11 rapid attempts must hit 429."""
    statuses = []
    for _ in range(11):
        r = await client.post(
            "/api/auth/login",
            data={"username": "nobody", "password": "wrongpass"},
        )
        statuses.append(r.status_code)
        if r.status_code == 429:
            assert "Retry-After" in r.headers
            break
    assert 429 in statuses, f"expected 429 within 11 attempts; got {statuses}"


@pytest.mark.asyncio
async def test_insights_rate_limit_per_user(client, registered_user):
    """30/min per user → 31 attempts must hit 429."""
    payload = {"events": [], "metrics": {"cpu": 30}}
    for _ in range(31):
        r = await client.post("/api/insights", json=payload)
        if r.status_code == 429:
            assert "Retry-After" in r.headers
            return
    pytest.fail("insights rate limit not enforced")
