"""E2E: runbook UI tests."""

import os

import pytest

BASE_URL = os.getenv("E2E_BASE_URL", "http://127.0.0.1:8080")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "base_url": BASE_URL}


@pytest.fixture
def logged_in_page(page):
    page.context.clear_cookies()
    page.goto("/", wait_until="domcontentloaded")
    page.wait_for_timeout(2000)

    login_input = page.locator('input[name="username"]')
    if login_input.count() > 0:
        login_input.fill("e2euser")
        page.locator('input[name="password"]').fill("secret123")
        page.locator('button[type="submit"]').click()
        page.wait_for_timeout(2000)

    return page


def test_page_renders(page):
    """Page renders with expected content."""
    page.goto("/", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    content = page.content()
    assert "raqib" in content.lower() or "رقيب" in content


def test_health_endpoint(page):
    """Health endpoint works."""
    page.goto("/health")
    assert "healthy" in page.content()
