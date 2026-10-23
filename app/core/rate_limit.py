"""Single-source rate limiting via slowapi + Redis.

Replaces the legacy in-memory limiter. Falls back to in-memory storage
when Redis is unavailable (dev only — logs a warning).
"""

import logging

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _storage_uri() -> str:
    """Return a storage URI string for slowapi (Redis preferred)."""
    settings = get_settings()
    try:
        import redis

        client = redis.from_url(settings.redis_url, decode_responses=True)
        client.ping()
        logger.info("Rate limiter backend: Redis (%s)", settings.redis_url)
        return settings.redis_url
    except Exception as exc:
        logger.warning(
            "Redis unavailable for rate limiting (%s); falling back to memory",
            exc,
        )
        return "memory://"


limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=_storage_uri(),
    default_limits=[],
    in_memory_fallback_enabled=True,
)


def rate_limit_key_user_or_ip(request: Request) -> str:
    """Key function: per-user if authenticated, else per-IP."""
    from app.core.security import decode_token

    token = request.cookies.get("ns_token")
    claims = decode_token(token)
    if claims and claims.get("sub"):
        return f"user:{claims['sub']}"
    return f"ip:{get_remote_address(request)}"


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return 429 with a Retry-After header."""
    retry_after = getattr(exc, "retry_after", 60) or 60
    return JSONResponse(
        status_code=429,
        content={"detail": "too many requests"},
        headers={"Retry-After": str(int(retry_after))},
    )
