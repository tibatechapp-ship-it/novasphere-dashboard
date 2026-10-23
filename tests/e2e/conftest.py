"""Playwright fixtures — simple navigation."""

import os

import pytest

BASE_URL = os.getenv("E2E_BASE_URL", "http://127.0.0.1:8080")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "base_url": BASE_URL}


@pytest.fixture
def logged_in_page(page):
    """Navigate to page and wait for load."""
    page.goto("/")
    page.wait_for_load_state("domcontentloaded", timeout=20000)
    page.wait_for_timeout(1000)
    return page
