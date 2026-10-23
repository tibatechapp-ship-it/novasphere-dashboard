"""Insights endpoint — per-user rate limit + Prometheus metrics."""

import time

from fastapi import APIRouter, Cookie, HTTPException, Request

from app.core.metrics import (
    insights_duration_seconds,
    insights_requests_total,
    runbook_generated_total,
)
from app.core.rate_limit import limiter, rate_limit_key_user_or_ip
from app.core.security import decode_token
from app.schemas.insights import InsightsRequest, InsightsResponse
from app.services.insights_service import analyze

router = APIRouter()


@router.post("/insights", response_model=InsightsResponse)
@limiter.limit("30/minute", key_func=rate_limit_key_user_or_ip)
async def get_insights(
    request: Request,
    payload: InsightsRequest,
    ns_token: str | None = Cookie(default=None),
):
    claims = decode_token(ns_token)
    if not claims:
        raise HTTPException(status_code=401, detail="not authenticated")

    insights_requests_total.inc()
    start = time.perf_counter()

    response = analyze(payload)

    insights_duration_seconds.observe(time.perf_counter() - start)
    if response.runbook:
        runbook_generated_total.labels(severity=response.runbook.severity).inc()

    return response
