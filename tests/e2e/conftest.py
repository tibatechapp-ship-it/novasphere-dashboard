"""Playwright fixtures — login via HTTP, not via broken UI."""

import os

import httpx
import pytest

BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:8080")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "base_url": BASE_URL}


@pytest.fixture
def logged_in_page(page):
    """Login via API (bypasses UI), inject cookie, then navigate."""

    # 1) try login first (user is seeded by CI workflow), fall back to signup
    with httpx.Client(timeout=10.0) as client:
        r = client.post(
            f"{BASE_URL}/api/auth/login",
            data={"username": "e2euser", "password": "secret123"},
        )
        if r.status_code in (401, 404):
            r = client.post(
                f"{BASE_URL}/api/auth/signup",
                data={"username": "e2euser", "password": "secret123"},
            )
    # Handle 429 by retrying after a short delay
    if r.status_code == 429:
        import time

        time.sleep(2)
        with httpx.Client(timeout=10.0) as client:
            r = client.post(
                f"{BASE_URL}/api/auth/login",
                data={"username": "e2euser", "password": "secret123"},
            )
    r.raise_for_status()
    token = r.json()["token"]

    # 2) inject cookie BEFORE navigation
    page.context.add_cookies(
        [
            {
                "name": "ns_token",
                "value": token,
                "url": BASE_URL,
                "httpOnly": True,
                "secure": False,
                "sameSite": "Lax",
            }
        ]
    )

    # 3) navigate
    page.goto("/")
    page.wait_for_load_state("domcontentloaded", timeout=20000)
    return page
