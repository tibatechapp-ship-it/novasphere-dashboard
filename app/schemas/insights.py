"""Insights request/response schemas."""

from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["info", "warn", "error", "critical"]


class InsightsRequest(BaseModel):
    events: list[dict] = Field(default_factory=list)
    metrics: dict = Field(default_factory=dict)


class RunbookStep(BaseModel):
    step: str
    command: str | None = None
    platform_hint: str = "generic"


class Runbook(BaseModel):
    title: str
    severity: Severity
    steps: list[RunbookStep]
    action_url: str | None = None


class InsightsResponse(BaseModel):
    ok: bool = True
    summary: str
    insights: list[str]
    runbook: Runbook | None = None
    stats: dict
