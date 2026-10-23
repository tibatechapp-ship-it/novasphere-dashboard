"""Audit endpoints — record runbook interactions.

Two endpoints, both authenticated, both rate-limited per user:
- POST /api/audit/runbook-view
- POST /api/audit/action-url-click

Both are fire-and-forget from the frontend's perspective: they return
{"ok": true} regardless of whether the DB write succeeded (audit is
best-effort). HTTP errors are only returned for auth/validation failure.
"""

from datetime import datetime

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.rate_limit import limiter, rate_limit_key_user_or_ip
from app.core.security import decode_token
from app.db.session import get_db
from app.schemas.audit import AuditLogOut, AuditPage
from app.services import audit_service

router = APIRouter()


class RunbookEventIn(BaseModel):
    runbook_id: str = Field(min_length=1, max_length=100)
    severity: str | None = Field(default=None, max_length=20)


def _require_user(ns_token: str | None) -> str:
    claims = decode_token(ns_token)
    if not claims or not claims.get("sub"):
        raise HTTPException(status_code=401, detail="not authenticated")
    return claims["sub"]


@router.post("/audit/runbook-view")
@limiter.limit("60/minute", key_func=rate_limit_key_user_or_ip)
async def log_runbook_view(
    request: Request,
    body: RunbookEventIn,
    ns_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    user = _require_user(ns_token)
    audit_service.record(
        db,
        user=user,
        action="runbook_view",
        target=body.runbook_id,
        metadata={"severity": body.severity} if body.severity else None,
    )
    return {"ok": True}


@router.post("/audit/action-url-click")
@limiter.limit("60/minute", key_func=rate_limit_key_user_or_ip)
async def log_action_url_click(
    request: Request,
    body: RunbookEventIn,
    ns_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    user = _require_user(ns_token)
    audit_service.record(
        db,
        user=user,
        action="action_url_click",
        target=body.runbook_id,
    )
    return {"ok": True}


# ─────────────────────────────────────────────────────────────
# Read endpoint (v0.4.1)
# ─────────────────────────────────────────────────────────────


@router.get("/audit/log", response_model=AuditPage)
@limiter.limit("30/minute", key_func=rate_limit_key_user_or_ip)
async def list_audit_log(
    request: Request,
    user: str | None = Query(default=None, max_length=32),
    action: str | None = Query(default=None, max_length=50),
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
    page: int = Query(default=1, ge=1, le=10_000),
    page_size: int = Query(default=50, ge=1, le=200),
    ns_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    claims = decode_token(ns_token)
    if not claims or not claims.get("sub"):
        raise HTTPException(status_code=401, detail="not authenticated")

    current_user = claims["sub"]
    if user is not None and user != current_user:
        raise HTTPException(status_code=403, detail="cannot view other users' audit")

    effective_user = user if user else current_user

    from app.models.audit_log import AuditLog

    q = db.query(AuditLog).filter(AuditLog.user == effective_user)
    if action:
        q = q.filter(AuditLog.action == action)
    if since:
        q = q.filter(AuditLog.ts >= since)
    if until:
        q = q.filter(AuditLog.ts <= until)

    total = q.count()
    rows = q.order_by(AuditLog.ts.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return AuditPage(
        total=total,
        page=page,
        page_size=page_size,
        rows=[
            AuditLogOut(
                id=r.id,
                ts=r.ts,
                user=r.user,
                action=r.action,
                target=r.target,
                metadata_json=r.metadata_json,
            )
            for r in rows
        ],
    )
