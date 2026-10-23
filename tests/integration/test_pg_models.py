"""Model behavior on real Postgres."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password
from app.models.audit_log import AuditLog
from app.models.event import Event
from app.models.user import User

pytestmark = pytest.mark.integration


def test_user_unique_username_constraint(pg_session):
    pg_session.add(User(username="dup", password_hash=hash_password("secret123")))
    pg_session.commit()

    pg_session.add(User(username="dup", password_hash=hash_password("other123")))
    with pytest.raises(IntegrityError):
        pg_session.commit()
    pg_session.rollback()


def test_event_severity_index(pg_session):
    for sev in ("info", "warn", "error", "critical"):
        pg_session.add(Event(level="error", severity=sev, message=f"test {sev}"))
    pg_session.commit()

    assert pg_session.query(Event).filter(Event.severity == "critical").count() == 1


def test_audit_log_json_metadata_roundtrip(pg_session):
    entry = AuditLog(
        user="alice",
        action="runbook_view",
        target="cpu_critical",
        metadata_json={"severity": "critical", "region": "eu-west-1"},
    )
    pg_session.add(entry)
    pg_session.commit()
    pg_session.expire(entry)

    row = pg_session.query(AuditLog).filter_by(user="alice").one()
    assert row.metadata_json == {"severity": "critical", "region": "eu-west-1"}


def test_audit_log_no_fk_on_user(pg_session):
    pg_session.add(User(username="tempuser", password_hash=hash_password("secret123")))
    pg_session.commit()

    pg_session.add(AuditLog(user="tempuser", action="login_success", target="login"))
    pg_session.commit()

    pg_session.query(User).filter_by(username="tempuser").delete()
    pg_session.commit()

    survivors = pg_session.query(AuditLog).filter_by(user="tempuser").all()
    assert len(survivors) == 1


def test_event_timezone_preserved(pg_session):
    ev = Event(level="info", severity="info", message="tz test")
    pg_session.add(ev)
    pg_session.commit()
    pg_session.expire(ev)

    reloaded = pg_session.query(Event).filter_by(message="tz test").one()
    assert reloaded.ts.tzinfo is not None
