"""Metrics endpoint — verify Prometheus output is real."""

import pytest


@pytest.mark.asyncio
async def test_metrics_endpoint_returns_prometheus_format(client):
    """DoD requires /metrics to return real Prometheus output."""
    r = await client.get("/metrics")
    assert r.status_code == 200
    body = r.text
    assert "# HELP" in body or "# TYPE" in body
    assert "raqib_ws_connections_active" in body
    assert "raqib_insights_requests_total" in body


@pytest.mark.asyncio
async def test_metrics_reflects_requests(client, registered_user):
    """After hitting /api/insights, the metric counter increases."""
    before = _extract_metric((await client.get("/metrics")).text, "raqib_insights_requests_total")

    await client.post("/api/insights", json={"events": [], "metrics": {"cpu": 50}})

    after = _extract_metric((await client.get("/metrics")).text, "raqib_insights_requests_total")
    assert after > before


def _extract_metric(text: str, name: str) -> float:
    """Extract a numeric metric value from Prometheus text output."""
    for line in text.splitlines():
        if line.startswith(name) and not line.startswith("#"):
            parts = line.split()
            if len(parts) >= 2:
                try:
                    return float(parts[-1])
                except ValueError:
                    pass
    return 0.0
