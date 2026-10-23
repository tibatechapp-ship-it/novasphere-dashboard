"""Structured logging setup."""

import logging
import sys


def setup_logging(env: str = "development") -> None:
    """Configure root logger once."""
    level = logging.INFO
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

    logging.basicConfig(
        level=level,
        format=fmt,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    # Silence noisy third-party loggers
    for name in ("uvicorn.access", "sqlalchemy.engine.Engine"):
        logging.getLogger(name).setLevel(logging.WARNING)
