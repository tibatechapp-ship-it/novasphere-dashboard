"""Audit logging service — write-only, secret-free, allowlist-gated.

Design:
- Allowlist of actions prevents accidental logging of free-form strings
  from leaking sensitive context into the audit trail.
- `_sanitize()` strips known-sensitive keys from metadata. This is a
  defense-in-depth layer — callers should NOT pass secrets, but we
  belt-and-suspenders anyway.
- Writes are best-effort: on failure we log and rollback. We never break
  a user flow because the audit table is temporarily unavailable.
- The service does NOT commit transactions it didn't open. Callers that
  need transactional audit + business logic must pass their own session
  and rely on their own commit.
"""

import logging

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


# Allowlist — any action not in this set is rejected.
# Expand deliberately; never accept arbitrary user input here.
ALLOWED_ACTIONS: frozenset[str] = frozenset(
    {
        "runbook_view",
        "action_url_click",
        "login_success",
        "signup_success",
    }
)


# Fields that must never appear in `metadata_json`, case-insensitive.
_FORBIDDEN_METADATA_KEYS: frozenset[str] = frozenset(
    {
        "password",
        "password_hash",
        "token",
        "access_token",
        "refresh_token",
        "secret",
        "cookie",
        "authorization",
        "api_key",
        "private_key",
    }
)


def record(
    db: Session,
    *,
    user: str,
    action: str,
    target: str,
    metadata: dict | None = None,
    commit: bool = True,
) -> AuditLog | None:
    """Append one audit entry.

    Args:
        db: SQLAlchemy session.
        user: JWT `sub` (username).
        action: must be in ALLOWED_ACTIONS.
        target: runbook id, endpoint name, etc. (truncated to 200 chars).
        metadata: optional, sanitized before storage.
        commit: whether to commit immediately. Set False to join an
            existing transaction managed by the caller.

    Returns:
        The created AuditLog, or None if rejected/failed.
    """
    if action not in ALLOWED_ACTIONS:
        logger.warning("audit: rejected unknown action %r", action)
        return None

    if not user or not target:
        logger.warning("audit: empty user or target — skipping")
        return None

    entry = AuditLog(
        user=user[:32],
        action=action,
        target=target[:200],
        metadata_json=_sanitize(metadata),
    )

    try:
        db.add(entry)
        if commit:
            db.commit()
            db.refresh(entry)
        else:
            db.flush()
    except Exception as exc:  # pragma: no cover
        logger.error("audit: write failed: %s", exc)
        if commit:
            db.rollback()
        return None

    return entry


def _sanitize(metadata: dict | None) -> dict | None:
    """Strip forbidden keys, normalize types. Returns None if empty."""
    if not metadata:
        return None

    clean: dict = {}
    for key, value in metadata.items():
        if not isinstance(key, str):
            continue
        if key.lower() in _FORBIDDEN_METADATA_KEYS:
            continue
        # Only allow JSON-safe scalars; drop nested structures.
        if isinstance(value, (str, int, float, bool)) or value is None:
            clean[key[:50]] = value

    return clean or None
