"""Retention policy tests."""

from datetime import UTC, datetime, timedelta

import pytest

from app.models.audit_log import AuditLog
from app.services.audit_retention import prune_once


def test_prune_deletes_old_rows(db_session, monkeypatch):
    """Old rows are deleted; recent rows survive."""
    now = datetime.now(UTC)
    db_session.add_all(
        [
            AuditLog(user="u1", action="runbook_view", target="old", ts=now - timedelta(days=100)),
            AuditLog(
                user="u1", action="runbook_view", target="recent", ts=now - timedelta(days=10)
            ),
        ]
    )
    db_session.commit()

    monkeypatch.setenv("AUDIT_RETENTION_DAYS", "90")
    from app.core.config import get_settings

    get_settings.cache_clear()

    deleted = prune_once()
    assert deleted == 1

    remaining = db_session.query(AuditLog).all()
    assert len(remaining) == 1
    assert remaining[0].target == "recent"


def test_prune_disabled_when_zero(db_session, monkeypatch):
    """retention_days=0 keeps everything."""
    db_session.add(
        AuditLog(
            user="u1",
            action="runbook_view",
            target="ancient",
            ts=datetime.now(UTC) - timedelta(days=9999),
        )
    )
    db_session.commit()

    monkeypatch.setenv("AUDIT_RETENTION_DAYS", "0")
    from app.core.config import get_settings

    get_settings.cache_clear()

    deleted = prune_once()
    assert deleted == 0
    assert db_session.query(AuditLog).count() == 1


@pytest.mark.asyncio
async def test_audit_log_endpoint_requires_auth(client):
    r = await client.get("/api/audit/log")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_audit_log_returns_own_rows(client, registered_user, db_session):
    for i in range(2):
        await client.post(
            "/api/audit/runbook-view", json={"runbook_id": f"rb-{i}", "severity": "warn"}
        )

    r = await client.get("/api/audit/log?page=1&page_size=10")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert len(body["rows"]) == 2
    assert all(row["user"] == "testuser" for row in body["rows"])


@pytest.mark.asyncio
async def test_audit_log_rejects_other_user(client, registered_user):
    """Querying someone else's audit is forbidden."""
    r = await client.get("/api/audit/log?user=someone_else")
    assert r.status_code == 403
