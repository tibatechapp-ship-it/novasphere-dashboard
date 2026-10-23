"""Playwright fixtures — wait for Alpine hydration, login if needed."""

import os

import pytest

BASE_URL = os.getenv("E2E_BASE_URL", "http://127.0.0.1:8080")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "base_url": BASE_URL}


@pytest.fixture
def logged_in_page(page):
    """Wait for Alpine ready, then login via UI if form is visible."""
    page.context.clear_cookies()
    page.goto("/")

    # 1) انتظر إشارة hydration من Alpine (بدل timeout أعمى)
    page.wait_for_function(
        "() => window.__alpineReady === true",
        timeout=15000,
    )

    # 2) إن كان نموذج الدخول ظاهراً، سجّل الدخول
    login_input = page.locator('input[name="username"]:visible')
    if login_input.count() > 0:
        login_input.fill("e2euser")
        page.locator('input[name="password"]:visible').fill("secret123")
        page.locator('button[type="submit"]:visible').click()

    # 3) انتظر الـ dashboard (web-first — يعيد المحاولة تلقائياً)
    page.locator('[data-testid="dashboard"]:visible').wait_for(state="visible", timeout=15000)
    return page
