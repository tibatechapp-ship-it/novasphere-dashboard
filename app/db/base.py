"""Declarative base + eager model imports for Alembic & create_all."""

from sqlalchemy.orm import declarative_base

Base = declarative_base()


def _import_all_models() -> None:
    """Ensure all models are registered on Base.metadata."""
    from app.models import audit_log, event, user  # noqa: F401


_import_all_models()
