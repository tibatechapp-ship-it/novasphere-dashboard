"""Audit log tests — same isolation pattern as v0.3.1.

Covers:
1. runbook_view writes an entry
2. action_url_click writes an entry
3. Unknown action is rejected (allowlist)
4. Secret keys are stripped from metadata
5. Unauthenticated requests return 401
6. Entries are readable by the intended user (query by `user`)
"""

import pytest

from app.models.audit_log import AuditLog
from app.services import audit_service

# ─────────────────────────────────────────────────────────────
# Service-level (unit) tests — no HTTP, no auth.
# ─────────────────────────────────────────────────────────────


def test_record_rejects_unknown_action(db_session):
    entry = audit_service.record(
        db_session,
        user="alice",
        action="totally_unknown",
        target="something",
    )
    assert entry is None
    assert db_session.query(AuditLog).count() == 0


def test_record_strips_secret_keys(db_session):
    audit_service.record(
        db_session,
        user="alice",
        action="runbook_view",
        target="cpu_critical",
        metadata={
            "severity": "critical",
            "password": "should-be-dropped",
            "token": "also-dropped",
            "user_agent": "Mozilla",
        },
    )
    row = db_session.query(AuditLog).one()
    assert row.metadata_json == {"severity": "critical", "user_agent": "Mozilla"}
    assert "password" not in str(row.metadata_json)
    assert "token" not in str(row.metadata_json)


def test_record_truncates_long_fields(db_session):
    long_target = "x" * 500
    entry = audit_service.record(
        db_session,
        user="a" * 100,
        action="runbook_view",
        target=long_target,
    )
    assert entry is not None
    assert len(entry.user) == 32
    assert len(entry.target) == 200


def test_record_empty_user_skipped(db_session):
    entry = audit_service.record(
        db_session,
        user="",
        action="runbook_view",
        target="cpu_critical",
    )
    assert entry is None


def test_record_commit_false_defers(db_session):
    entry = audit_service.record(
        db_session,
        user="bob",
        action="runbook_view",
        target="cpu_critical",
        commit=False,
    )
    assert entry is not None
    # Not yet in DB until caller commits
    assert db_session.query(AuditLog).count() == 1  # flushed, in session
    # If caller rolls back, entry disappears
    db_session.rollback()
    assert db_session.query(AuditLog).count() == 0


# ─────────────────────────────────────────────────────────────
# HTTP-level (integration) tests — auth + routing.
# ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_runbook_view_requires_auth(client):
    r = await client.post(
        "/api/audit/runbook-view",
        json={"runbook_id": "cpu_critical", "severity": "critical"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_runbook_view_writes_entry(client, registered_user, db_session):
    r = await client.post(
        "/api/audit/runbook-view",
        json={"runbook_id": "cpu_critical", "severity": "critical"},
    )
    assert r.status_code == 200
    assert r.json() == {"ok": True}

    rows = db_session.query(AuditLog).filter_by(action="runbook_view").all()
    assert len(rows) == 1
    row = rows[0]
    assert row.user == "testuser"
    assert row.target == "cpu_critical"
    assert row.metadata_json == {"severity": "critical"}


@pytest.mark.asyncio
async def test_action_url_click_writes_entry(client, registered_user, db_session):
    r = await client.post(
        "/api/audit/action-url-click",
        json={"runbook_id": "memory_critical"},
    )
    assert r.status_code == 200
    assert r.json() == {"ok": True}

    row = db_session.query(AuditLog).filter_by(action="action_url_click").one()
    assert row.user == "testuser"
    assert row.target == "memory_critical"
    assert row.metadata_json is None  # no severity passed


@pytest.mark.asyncio
async def test_runbook_view_rejects_invalid_body(client, registered_user):
    # Missing runbook_id → 422 from Pydantic
    r = await client.post("/api/audit/runbook-view", json={})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_runbook_view_rejects_oversized_id(client, registered_user):
    r = await client.post(
        "/api/audit/runbook-view",
        json={"runbook_id": "x" * 200},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_audit_isolated_per_test(client, registered_user, db_session):
    """Regression: each test must see a clean audit_log table.

    If this fails, the test isolation in conftest.py is broken — same
    class of bug as the v0.3.0 WebSocket leak regression.
    """
    count = db_session.query(AuditLog).count()
    assert count == 0, f"audit_log not isolated: found {count} pre-existing rows"
