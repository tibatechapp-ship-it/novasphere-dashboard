"""Playwright fixtures — login via API token cookie."""

import os

import pytest

BASE_URL = os.getenv("E2E_BASE_URL", "http://127.0.0.1:8080")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "base_url": BASE_URL}


@pytest.fixture
def logged_in_page(page):
    """Login via API, inject cookie, navigate."""

    # Intercept /api/events to simulate authenticated user
    page.route(
        "**/api/events*",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='{"events": [], "total": 0}',
        ),
    )

    # Navigate and wait
    page.goto("/")
    page.wait_for_load_state("domcontentloaded", timeout=20000)

    # Give Alpine time to initialize
    page.wait_for_timeout(2000)

    return page
