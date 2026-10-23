"""Playwright fixtures — deterministic tests via route interception."""

import os

import pytest

BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:8080")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "base_url": BASE_URL}


@pytest.fixture
def logged_in_page(page):
    """Log in via UI. Assumes e2euser exists (seeded by CI)."""
    page.goto("/")
    page.fill('input[name="username"]', "e2euser")
    page.fill('input[name="password"]', "secret123")
    page.click('button[type="submit"]')
    page.wait_for_selector('[data-testid="runbook-card"]', timeout=10000)
    return page
