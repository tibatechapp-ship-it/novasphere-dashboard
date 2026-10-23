"""Playwright fixtures — resilient login (fresh state, handles both)."""

import os

import pytest

BASE_URL = os.getenv("E2E_BASE_URL", "http://127.0.0.1:8080")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "base_url": BASE_URL}


@pytest.fixture
def logged_in_page(page):
    """Clear cookies → navigate → login if needed → wait for dashboard."""
    page.context.clear_cookies()
    page.goto("/")
    page.wait_for_load_state("networkidle", timeout=10000)
    page.wait_for_timeout(500)

    login_input = page.locator('input[name="username"]')
    if login_input.is_visible(timeout=2000):
        login_input.fill("e2euser")
        page.fill('input[name="password"]', "secret123")
        page.click('button[type="submit"]')

    page.wait_for_selector('[data-testid="dashboard"]', state="visible", timeout=20000)
    return page
