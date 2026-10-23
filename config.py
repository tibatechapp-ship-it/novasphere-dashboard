"""NovaSphere configuration loaded from .env."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "novasphere-dev-secret-change-me")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./novasphere.db")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
MOCK_DATA = os.getenv("MOCK_DATA", "true").lower() in ("1", "true", "yes", "on")