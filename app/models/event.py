"""Event model with Smart Runbook fields."""

from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Float, Integer, String

from app.db.base import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    ts = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )
    level = Column(String(20), nullable=False, default="info")
    severity = Column(String(20), nullable=False, default="info", index=True)
    message = Column(String(500), nullable=False)

    # Smart Runbook fields (populated in Phase 3)
    remediation_hint = Column(String(1000), nullable=True)
    runbook_id = Column(String(100), nullable=True)

    # Metric correlation snapshot
    metric_cpu = Column(Float, nullable=True)
    metric_mem = Column(Float, nullable=True)
    metric_rps = Column(Float, nullable=True)
