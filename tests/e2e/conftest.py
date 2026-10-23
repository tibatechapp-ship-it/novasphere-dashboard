"""Playwright fixtures — login via API token + extra headers."""

import os

import httpx
import pytest

BASE_URL = os.getenv("E2E_BASE_URL", "http://127.0.0.1:8080")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "base_url": BASE_URL}


@pytest.fixture
def logged_in_page(page):
    """Login via API, set cookie via headers, navigate."""

    # Login (user is seeded by CI workflow)
    with httpx.Client(timeout=10.0) as client:
        r = client.post(
            f"{BASE_URL}/api/auth/login",
            data={"username": "e2euser", "password": "secret123"},
        )
    r.raise_for_status()
    token = r.json()["token"]

    # Set cookie via extra headers (more reliable than add_cookies for localhost)
    page.set_extra_http_headers({"Cookie": f"ns_token={token}"})

    # Also try add_cookies
    page.context.add_cookies(
        [
            {
                "name": "ns_token",
                "value": token,
                "domain": "127.0.0.1",
                "path": "/",
            }
        ]
    )

    # Navigate and wait
    page.goto("/")
    page.wait_for_load_state("domcontentloaded", timeout=20000)

    return page
