"""Playwright fixtures — login via API token cookie."""

import os

import httpx
import pytest

BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:8080")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "base_url": BASE_URL}


@pytest.fixture
def logged_in_page(page):
    """Login via API, inject cookie, navigate."""

    # Login (user is seeded by CI workflow)
    with httpx.Client(timeout=10.0) as client:
        r = client.post(
            f"{BASE_URL}/api/auth/login",
            data={"username": "e2euser", "password": "secret123"},
        )
    r.raise_for_status()
    token = r.json()["token"]

    # Inject cookie using URL (Playwright derives domain + path)
    page.context.add_cookies(
        [
            {
                "name": "ns_token",
                "value": token,
                "url": BASE_URL,
            }
        ]
    )

    # Navigate and wait
    page.goto("/")
    page.wait_for_load_state("domcontentloaded", timeout=20000)

    # Give Alpine time to initialize
    page.wait_for_timeout(2000)

    return page
