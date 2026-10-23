"""Events endpoint."""

from fastapi import APIRouter, Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models.event import Event
from app.schemas.event import EventListResponse, EventOut

router = APIRouter()


@router.get("/events", response_model=EventListResponse)
async def recent_events(
    limit: int = 10,
    ns_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    claims = decode_token(ns_token)
    if not claims:
        raise HTTPException(status_code=401, detail="not authenticated")

    limit = max(1, min(limit, 100))
    rows = db.query(Event).order_by(Event.ts.desc()).limit(limit).all()

    return EventListResponse(
        events=[
            EventOut(
                id=r.id,
                ts=r.ts.timestamp(),
                level=r.level,
                severity=r.severity,  # type: ignore[arg-type]
                msg=r.message,
            )
            for r in rows
        ]
    )
