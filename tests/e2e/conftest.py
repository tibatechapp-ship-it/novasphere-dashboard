"""Playwright fixtures — element-based waits."""

import os

import pytest

BASE_URL = os.getenv("E2E_BASE_URL", "http://127.0.0.1:8080")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "base_url": BASE_URL}


@pytest.fixture
def logged_in_page(page):
    page.context.clear_cookies()
    page.goto("/", wait_until="networkidle")

    page.wait_for_selector(
        'input[name="username"]:visible, [data-testid="dashboard"]:visible',
        state="visible",
        timeout=15000,
    )

    login_input = page.locator('input[name="username"]:visible')
    if login_input.count() > 0:
        login_input.fill("e2euser")
        page.locator('input[name="password"]:visible').fill("secret123")
        page.locator('button[type="submit"]:visible').click()

    page.locator('[data-testid="dashboard"]:visible').wait_for(state="visible", timeout=15000)
    return page
