"""Audit log — governance trail for runbook interactions.

Design notes:
- `user` is the JWT `sub` (username) — no FK, because users can be deleted
  while their audit trail must be preserved for governance.
- `metadata_json` must NEVER contain secrets. `audit_service._sanitize()`
  enforces this at write time, but the column type is JSON for flexibility.
- Indexes on (ts, user, action) support the three common queries:
  "recent activity", "what did user X do", "who did action Y".
"""

from datetime import UTC, datetime

from sqlalchemy import JSON, Column, DateTime, Integer, String

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    ts = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )
    user = Column(String(32), nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)
    target = Column(String(200), nullable=False)
    metadata_json = Column(JSON, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AuditLog {self.action} by {self.user} on {self.target}>"
