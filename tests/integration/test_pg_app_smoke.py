"""App imports and runs against Postgres (not just SQLite)."""

import pytest

pytestmark = pytest.mark.integration


def test_writes_visible_across_sessions(pg_engine):
    """A commit in one session is visible to another — pool is real."""
    from sqlalchemy.orm import sessionmaker

    from app.models.event import Event

    Session = sessionmaker(bind=pg_engine, future=True)

    s1 = Session()
    s1.add(Event(level="info", severity="info", message="cross-session"))
    s1.commit()
    s1.close()

    s2 = Session()
    try:
        count = s2.query(Event).filter_by(message="cross-session").count()
        assert count == 1
    finally:
        s2.close()
