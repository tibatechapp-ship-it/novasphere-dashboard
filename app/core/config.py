"""Central configuration via pydantic-settings."""

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_SECRET_PLACEHOLDER = "dev-only-insecure-secret-change-me-32chars-min"


class Settings(BaseSettings):
    """Application settings loaded from environment / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- Runtime ----
    env: str = Field(default="development", description="development | production")
    mock_data: bool = Field(default=True)

    # ---- Database ----
    database_url: str = Field(default="sqlite:///./raqib.db")

    # ---- Redis ----
    redis_url: str = Field(default="redis://localhost:6379/0")

    # ---- Security ----
    jwt_secret_key: str = Field(default=DEV_SECRET_PLACEHOLDER)
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=60 * 24)

    # ---- CORS ----
    cors_origins: str = Field(default="http://localhost:8080,http://127.0.0.1:8080")

    # ---- Remediation ----
    remediation_platform_url: str = Field(default="")

    # ---- Runbooks ----
    runbooks_dir: str = Field(default="")

    # ---- Rate limiting (legacy, to be replaced in Phase 2) ----
    legacy_rate_limit_requests: int = Field(default=20)
    legacy_rate_limit_window_seconds: int = Field(default=60)

    # ---- Validators ----
    @model_validator(mode="after")
    def _validate_production_security(self) -> "Settings":
        if self.env.lower() == "production":
            if self.jwt_secret_key == DEV_SECRET_PLACEHOLDER:
                raise ValueError(
                    "JWT_SECRET_KEY must be set in production (currently using dev placeholder)"
                )
            if len(self.jwt_secret_key) < 32:
                raise ValueError("JWT_SECRET_KEY must be >= 32 characters in production")
        return self

    # ---- Audit retention ----
    audit_retention_days: int = 90
    audit_cleanup_interval_hours: int = 24

    # ---- Helpers ----
    @property
    def is_production(self) -> bool:
        return self.env.lower() == "production"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Singleton settings accessor."""
    return Settings()
