"""Postgres fixtures — skip cleanly when no PG is available."""

import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

PG_URL = os.getenv("POSTGRES_TEST_URL")

pytestmark = pytest.mark.integration


@pytest.fixture(scope="session")
def pg_url() -> str:
    if not PG_URL:
        pytest.skip("POSTGRES_TEST_URL not set — skipping Postgres integration tests")
    return PG_URL


@pytest.fixture(scope="session")
def pg_engine(pg_url: str):
    """Session-scoped engine. Applies Alembic migrations once."""
    from alembic.config import Config

    from alembic import command

    engine = create_engine(pg_url, pool_pre_ping=True, future=True)

    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))

    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", pg_url)
    command.upgrade(cfg, "head")

    yield engine

    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    engine.dispose()


@pytest.fixture
def pg_session(pg_engine):
    """Per-test session. Rolls back on teardown — guarantees isolation."""
    SessionLocal = sessionmaker(bind=pg_engine, future=True, expire_on_commit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
