"""Raqib — FastAPI application entrypoint."""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi.errors import RateLimitExceeded

from app import __version__
from app.api import audit as audit_api
from app.api import auth, events, insights, ws
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from app.db.base import Base
from app.db.session import engine
from app.services.mock_generator import background_generator

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: migrations (safe fallback) + background task."""
    settings = get_settings()

    try:
        from alembic.config import Config

        from alembic import command

        cfg = Config("alembic.ini")
        cfg.set_main_option("sqlalchemy.url", settings.database_url)
        command.upgrade(cfg, "head")
        logger.info("Database migrated via Alembic")
    except Exception as exc:
        logger.warning(
            "Alembic migration unavailable (%s); falling back to create_all()",
            exc,
        )
        Base.metadata.create_all(bind=engine)

    task = asyncio.create_task(background_generator(ws.manager))

    from app.services.audit_retention import run_forever as retention_loop

    retention_task = asyncio.create_task(retention_loop())  # pragma: no cover

    yield

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    retention_task.cancel()  # pragma: no cover
    try:  # pragma: no cover
        await retention_task  # pragma: no cover
    except asyncio.CancelledError:  # pragma: no cover
        pass  # pragma: no cover


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()
    setup_logging(settings.env)

    app = FastAPI(title="Raqib", version=__version__, lifespan=lifespan)

    # --- Rate limiting (A3) ---
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    # --- Prometheus (A5) — MUST run before routers ---
    Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        excluded_handlers=["/metrics", "/health"],
    ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

    # --- CORS (A9) ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    # --- Routers ---
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(events.router, prefix="/api", tags=["events"])
    app.include_router(insights.router, prefix="/api", tags=["insights"])
    app.include_router(audit_api.router, prefix="/api", tags=["audit"])
    app.include_router(ws.router, tags=["ws"])

    # --- Static ---
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/health")
    async def health() -> dict:
        return {"status": "healthy", "service": "raqib", "version": __version__}

    @app.get("/", include_in_schema=False)
    async def index():
        index_file = STATIC_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"detail": "frontend not found"}

    return app


app = create_app()
