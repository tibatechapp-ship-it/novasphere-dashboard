"""Event response schemas."""

from typing import Literal

from pydantic import BaseModel

Severity = Literal["info", "warn", "error", "critical"]


class EventOut(BaseModel):
    id: int
    ts: float
    level: str
    severity: Severity
    msg: str


class EventListResponse(BaseModel):
    ok: bool = True
    events: list[EventOut]
