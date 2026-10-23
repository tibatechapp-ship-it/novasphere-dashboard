"""Playwright fixtures — login via HTTP, not via broken UI."""

import os
from urllib.parse import urlparse

import httpx
import pytest

BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:8080")
_HOSTNAME = urlparse(BASE_URL).hostname or "localhost"


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "base_url": BASE_URL}


@pytest.fixture
def logged_in_page(page):
    """Login via API, inject cookie for the correct host."""
    with httpx.Client(timeout=10.0) as client:
        r = client.post(
            f"{BASE_URL}/api/auth/signup",
            data={"username": "e2euser", "password": "secret123"},
        )
        if r.status_code == 400:
            r = client.post(
                f"{BASE_URL}/api/auth/login",
                data={"username": "e2euser", "password": "secret123"},
            )
    r.raise_for_status()
    token = r.json()["token"]

    page.context.add_cookies(
        [
            {
                "name": "ns_token",
                "value": token,
                "domain": _HOSTNAME,
                "path": "/",
                "httpOnly": True,
                "secure": False,
                "sameSite": "Lax",
            }
        ]
    )

    page.goto("/")
    page.wait_for_selector('[data-testid="dashboard"]', timeout=20000)
    return page
