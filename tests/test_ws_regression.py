"""Regression tests — prevent WebSocket leak from being reintroduced."""

import inspect
import time


def test_handler_uses_receive_not_sleep():
    """Source check: handler must use receive(), not long sleep()."""
    from app.api.ws import websocket_endpoint

    src = inspect.getsource(websocket_endpoint)

    assert "await ws.receive" in src, (
        "ws handler must call `await ws.receive()` to detect disconnects. "
        "Regression: v0.3.0 shipped with `asyncio.sleep(3600)`."
    )
    assert "asyncio.sleep(3600)" not in src, (
        "`asyncio.sleep(3600)` causes WebSocket leak — see v0.3.1 hotfix"
    )


def test_disconnect_in_finally():
    """Source check: disconnect must be reachable on any exit."""
    from app.api.ws import websocket_endpoint

    src = inspect.getsource(websocket_endpoint)
    finally_idx = src.find("finally:")
    assert finally_idx != -1, "ws handler must have a finally block"
    disconnect_idx = src.find("manager.disconnect", finally_idx)
    assert disconnect_idx > finally_idx, "manager.disconnect must be inside finally block"


def _wait_until(fn, timeout=3.0, interval=0.05):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if fn():
            return True
        time.sleep(interval)
    return fn()


def test_no_leak_after_100_cycles(sync_client):
    """Runtime check: 100 connect/disconnect cycles must leave 0 connections."""
    from app.api.ws import manager

    r = sync_client.post(
        "/api/auth/signup",
        data={"username": "leaktest", "password": "secret123"},
    )
    if r.status_code == 400:
        r = sync_client.post(
            "/api/auth/login",
            data={"username": "leaktest", "password": "secret123"},
        )
    token = r.json()["token"]

    before = manager.active_connections
    for _ in range(100):
        with sync_client.websocket_connect(f"/ws?token={token}"):
            pass

    assert _wait_until(lambda: manager.active_connections == before), (
        f"WebSocket leak: expected {before}, got {manager.active_connections}"
    )


def test_gauge_resets_to_zero(sync_client):
    """Prometheus gauge must return to 0 (or its baseline)."""
    from prometheus_client import REGISTRY

    def gauge_val() -> float:
        for metric in REGISTRY.collect():
            if metric.name == "raqib_ws_connections_active":
                for sample in metric.samples:
                    return float(sample.value)
        return -1.0

    before = gauge_val()

    r = sync_client.post(
        "/api/auth/signup",
        data={"username": "gaugetest", "password": "secret123"},
    )
    if r.status_code == 400:
        r = sync_client.post(
            "/api/auth/login",
            data={"username": "gaugetest", "password": "secret123"},
        )
    token = r.json()["token"]

    with sync_client.websocket_connect(f"/ws?token={token}"):
        pass

    assert _wait_until(lambda: gauge_val() == before), (
        f"Prometheus gauge leaked: {gauge_val()} != {before}"
    )
