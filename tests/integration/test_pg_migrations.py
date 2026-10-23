"""Migrations apply cleanly on Postgres — catches SQLite-only drift."""

import pytest
from sqlalchemy import inspect, text

pytestmark = pytest.mark.integration


def test_migrations_apply_head(pg_engine):
    """`alembic upgrade head` succeeded in the session fixture."""
    with pg_engine.connect() as conn:
        version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    assert version == "001_audit_log"


def test_all_expected_tables_exist(pg_engine):
    inspector = inspect(pg_engine)
    tables = set(inspector.get_table_names())
    assert {"users", "events", "audit_log", "alembic_version"} <= tables


def test_users_schema(pg_engine):
    cols = {c["name"]: c for c in inspect(pg_engine).get_columns("users")}
    assert cols["id"]["primary_key"] is True
    assert cols["username"]["nullable"] is False
    assert cols["password_hash"]["nullable"] is False
    assert cols["created_at"]["nullable"] is False


def test_audit_log_json_column(pg_engine):
    """`metadata_json` must be a JSON/JSONB column on Postgres."""
    cols = {c["name"]: c for c in inspect(pg_engine).get_columns("audit_log")}
    assert "JSON" in str(cols["metadata_json"]["type"]).upper()


def test_downgrade_to_base_and_back(pg_engine, pg_url):
    """Downgrade must remove tables; upgrade restores them. Reversible migrations."""
    from alembic.config import Config

    from alembic import command

    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", pg_url)

    command.downgrade(cfg, "base")
    tables_after_down = set(inspect(pg_engine).get_table_names())
    assert "audit_log" not in tables_after_down
    assert "events" not in tables_after_down
    assert "users" not in tables_after_down

    command.upgrade(cfg, "head")
    tables_after_up = set(inspect(pg_engine).get_table_names())
    assert {"audit_log", "events", "users"} <= tables_after_up
