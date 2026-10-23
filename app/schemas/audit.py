"""Audit query schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class AuditLogOut(BaseModel):
    id: int
    ts: datetime
    user: str
    action: str
    target: str
    metadata_json: dict | None = None


class AuditPage(BaseModel):
    ok: bool = True
    total: int
    page: int
    page_size: int
    rows: list[AuditLogOut]


class AuditQuery(BaseModel):
    user: str | None = Field(default=None, max_length=32)
    action: str | None = Field(default=None, max_length=50)
    since: datetime | None = None
    until: datetime | None = None
    page: int = Field(default=1, ge=1, le=10_000)
    page_size: int = Field(default=50, ge=1, le=200)
