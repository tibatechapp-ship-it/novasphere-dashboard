"""Insights + runbook tests — no skips, real ASGI."""

import pytest


@pytest.mark.asyncio
async def test_insights_requires_auth(client):
    r = await client.post("/api/insights", json={"events": [], "metrics": {}})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_insights_healthy_no_runbook(client, registered_user):
    r = await client.post(
        "/api/insights",
        json={"events": [], "metrics": {"cpu": 30, "mem": 40}},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["runbook"] is None


@pytest.mark.asyncio
async def test_insights_cpu_critical_runbook(client, registered_user):
    r = await client.post(
        "/api/insights",
        json={"events": [], "metrics": {"cpu": 95, "platform": "linux"}},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["runbook"] is not None
    assert body["runbook"]["severity"] == "critical"
    assert any("top" in (s.get("command") or "") for s in body["runbook"]["steps"])


@pytest.mark.asyncio
async def test_insights_platform_filter_linux(client, registered_user):
    r = await client.post(
        "/api/insights",
        json={"events": [], "metrics": {"cpu": 95, "platform": "linux"}},
    )
    body = r.json()
    step_platforms = {s["platform_hint"] for s in body["runbook"]["steps"]}
    assert "linux" in step_platforms or "generic" in step_platforms


@pytest.mark.asyncio
async def test_insights_platform_filter_kubernetes(client, registered_user):
    """K8s payload must NOT include linux-only commands (e.g. `top -o %CPU`)."""
    r = await client.post(
        "/api/insights",
        json={"events": [], "metrics": {"cpu": 95, "platform": "kubernetes"}},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["runbook"] is not None

    commands = [s.get("command") for s in body["runbook"]["steps"] if s.get("command")]
    assert all("top -o" not in c for c in commands), f"linux command leaked: {commands}"
    assert all("journalctl" not in c for c in commands), f"journalctl leaked: {commands}"
    assert all("pmap" not in c for c in commands), f"pmap leaked: {commands}"
