"""Config validation tests."""

import pytest
from pydantic import ValidationError


def test_prod_requires_strong_jwt():
    from app.core.config import Settings

    with pytest.raises(ValidationError):
        Settings(env="production", jwt_secret_key="short")


def test_prod_rejects_dev_placeholder():
    from app.core.config import DEV_SECRET_PLACEHOLDER, Settings

    with pytest.raises(ValidationError):
        Settings(env="production", jwt_secret_key=DEV_SECRET_PLACEHOLDER)


def test_cors_origins_parsed():
    from app.core.config import Settings

    s = Settings(cors_origins="http://a,http://b")
    assert s.cors_origins_list == ["http://a", "http://b"]
