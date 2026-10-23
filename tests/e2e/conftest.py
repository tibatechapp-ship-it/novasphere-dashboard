"""Playwright fixtures — login via UI form (server sets proper cookie)."""

import os

import pytest

BASE_URL = os.getenv("E2E_BASE_URL", "http://127.0.0.1:8080")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "base_url": BASE_URL}


@pytest.fixture
def logged_in_page(page):
    """Login via UI form — tests full flow, cookie set by server."""
    page.goto("/")
    page.wait_for_selector('input[name="username"]', state="visible", timeout=20000)
    page.fill('input[name="username"]', "e2euser")
    page.fill('input[name="password"]', "secret123")
    page.click('button[type="submit"]')
    page.wait_for_selector('[data-testid="dashboard"]', state="visible", timeout=20000)
    return page
