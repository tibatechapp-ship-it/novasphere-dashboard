"""Events endpoint tests."""

import pytest


@pytest.mark.asyncio
async def test_events_requires_auth(client):
    r = await client.get("/api/events")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_events_returns_list(client, registered_user):
    r = await client.get("/api/events?limit=5")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert isinstance(body["events"], list)
