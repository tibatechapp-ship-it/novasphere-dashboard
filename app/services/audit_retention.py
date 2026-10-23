"""Audit log retention — periodic cleanup of old rows.

Design:
- Runs as an async background task in the app's lifespan.
- Uses a separate session to avoid interfering with request handlers.
- Logs the number of rows deleted so operators can spot anomalies.
- `retention_days=0` disables cleanup (keep forever).
"""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


def prune_once() -> int:
    """Delete rows older than retention_days. Returns count deleted.

    No-op if retention_days == 0.
    """
    settings = get_settings()
    days = getattr(settings, "audit_retention_days", 90)
    if days <= 0:
        return 0

    cutoff = datetime.now(UTC) - timedelta(days=days)
    db = SessionLocal()
    try:
        stmt = delete(AuditLog).where(AuditLog.ts < cutoff)
        result = db.execute(stmt)
        db.commit()
        deleted = result.rowcount or 0
        if deleted > 0:
            logger.info("audit retention: deleted %d rows older than %s", deleted, cutoff.date())
        return deleted
    except Exception as exc:
        logger.error("audit retention failed: %s", exc)
        db.rollback()
        return 0
    finally:
        db.close()


async def run_forever() -> None:  # pragma: no cover
    """Background loop — run prune_once every N hours."""
    settings = get_settings()
    days = getattr(settings, "audit_retention_days", 90)
    if days <= 0:
        logger.info("audit retention: disabled (retention_days=0)")
        return

    interval_hours = getattr(settings, "audit_cleanup_interval_hours", 24)
    interval = max(interval_hours, 1) * 3600
    logger.info("audit retention: enabled (%d days, every %d h)", days, interval_hours)

    await asyncio.sleep(60)
    while True:
        try:
            prune_once()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error("retention loop error: %s", exc)
        await asyncio.sleep(interval)
