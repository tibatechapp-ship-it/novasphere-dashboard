"""E2E: smoke tests — page loads."""

import os

import pytest

BASE_URL = os.getenv("E2E_BASE_URL", "http://127.0.0.1:8080")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "base_url": BASE_URL}


def test_page_loads(page):
    """Page renders with content."""
    page.goto("/", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    content = page.content()
    assert len(content) > 100


def test_health_endpoint(page):
    """Health endpoint works."""
    page.goto("/health")
    assert "healthy" in page.content()
