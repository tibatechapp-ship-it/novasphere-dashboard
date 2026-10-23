"""SQLAlchemy engine + session factory."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

settings = get_settings()

_connect_args = {}
if settings.database_url.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.database_url,
    connect_args=_connect_args,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


def get_db():
    """FastAPI dependency for a per-request session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
