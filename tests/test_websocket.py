"""Real WebSocket tests using TestClient (in-process)."""

import time

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect


def _wait_until(predicate, timeout: float = 2.0, interval: float = 0.05) -> bool:
    """Poll predicate until true or timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return predicate()


def _register_and_get_token(client: TestClient, username: str) -> str:
    r = client.post(
        "/api/auth/signup",
        data={"username": username, "password": "secret123"},
    )
    if r.status_code == 400:
        r = client.post(
            "/api/auth/login",
            data={"username": username, "password": "secret123"},
        )
    assert r.status_code == 200, r.text
    return r.json()["token"]


def test_ws_rejects_without_token(sync_client: TestClient):
    with pytest.raises(WebSocketDisconnect) as exc, sync_client.websocket_connect("/ws") as ws:
        ws.receive_json()
    assert exc.value.code == 4401


def test_ws_rejects_bad_token(sync_client: TestClient):
    with pytest.raises(WebSocketDisconnect) as exc:
        with sync_client.websocket_connect("/ws?token=bogus"):
            pass
    assert exc.value.code == 4401


def test_ws_connects_and_registers(sync_client: TestClient):
    from app.api.ws import manager

    token = _register_and_get_token(sync_client, "ws_ok")
    before = manager.active_connections

    with sync_client.websocket_connect(f"/ws?token={token}") as ws:
        assert ws is not None
        assert _wait_until(lambda: manager.active_connections == before + 1), (
            f"expected {before + 1}, got {manager.active_connections}"
        )

    assert _wait_until(lambda: manager.active_connections == before), (
        f"leak! expected {before}, got {manager.active_connections}"
    )


def test_ws_disconnect_cleanup(sync_client: TestClient):
    """Regression test: server MUST clean up on client disconnect."""
    from app.api.ws import manager

    token = _register_and_get_token(sync_client, "ws_cleanup")
    before = manager.active_connections

    with sync_client.websocket_connect(f"/ws?token={token}"):
        assert _wait_until(lambda: manager.active_connections == before + 1)

    assert _wait_until(lambda: manager.active_connections == before, timeout=3.0), (
        f"WebSocket leak detected: expected {before}, got {manager.active_connections}"
    )


def test_ws_no_leak_after_many_cycles(sync_client: TestClient):
    """100 connect/disconnect cycles must not accumulate connections."""
    from app.api.ws import manager

    token = _register_and_get_token(sync_client, "ws_cycles")
    before = manager.active_connections

    for _ in range(100):
        with sync_client.websocket_connect(f"/ws?token={token}"):
            pass

    assert _wait_until(lambda: manager.active_connections == before, timeout=5.0), (
        f"leak after 100 cycles: expected {before}, got {manager.active_connections}"
    )
