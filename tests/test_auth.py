"""Auth flow tests."""

import pytest


@pytest.mark.asyncio
async def test_signup_and_login(client):
    r = await client.post(
        "/api/auth/signup",
        data={"username": "alice", "password": "secret123"},
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post(
        "/api/auth/signup",
        data={"username": "bob", "password": "secret123"},
    )
    r = await client.post(
        "/api/auth/login",
        data={"username": "bob", "password": "wrong"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_short_password_rejected(client):
    r = await client.post(
        "/api/auth/signup",
        data={"username": "charlie", "password": "123"},
    )
    assert r.status_code == 400
