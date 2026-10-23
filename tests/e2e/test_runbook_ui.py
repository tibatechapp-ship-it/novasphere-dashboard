"""E2E — Runbook card rendering, copy, ARIA, audit hooks."""

import json

import pytest

pytest.importorskip("playwright")
from playwright.sync_api import Page, expect

CRITICAL_PAYLOAD = {
    "ok": True,
    "summary": "CPU critical (95%)",
    "insights": ["CPU critical (95%)"],
    "runbook": {
        "title": "CPU Critical",
        "severity": "critical",
        "steps": [
            {"step": "Check top processes", "command": "top -o %CPU", "platform_hint": "linux"},
            {"step": "Restart service", "command": None, "platform_hint": "generic"},
            {
                "step": "Verify recovery",
                "command": "curl -s localhost:8080/health",
                "platform_hint": "generic",
            },
        ],
        "action_url": "https://awx.example.com/runbook/cpu_critical",
    },
    "stats": {},
}


def _intercept_insights(page: Page, payload: dict) -> None:
    """Force deterministic /api/insights response."""
    page.route(
        "**/api/insights",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(payload),
        ),
    )


def test_runbook_card_renders(logged_in_page: Page):
    """Card must appear with correct severity badge and step count."""
    page = logged_in_page
    _intercept_insights(page, CRITICAL_PAYLOAD)
    page.reload()
    page.wait_for_timeout(5000)
    expect(page.locator('[data-testid="severity-badge"]')).to_have_text("CRITICAL")
    steps = page.locator('[data-testid="runbook-step"]')
    expect(steps).to_have_count(3)


def test_empty_state_when_healthy(logged_in_page: Page):
    """No runbook → 'All systems healthy' message appears."""
    page = logged_in_page
    _intercept_insights(
        page,
        {
            "ok": True,
            "summary": "healthy",
            "insights": ["healthy"],
            "runbook": None,
            "stats": {},
        },
    )
    page.reload()
    expect(page.locator('[data-testid="empty-state"]')).to_be_visible(timeout=10000)


def test_severity_color_critical(logged_in_page: Page):
    """Critical severity must apply red border class."""
    page = logged_in_page
    _intercept_insights(page, CRITICAL_PAYLOAD)
    page.reload()
    card = page.locator('[data-testid="runbook-card"]').first
    card.wait_for(timeout=10000)
    assert "border-red-500" in (card.get_attribute("class") or "")


def test_copy_button_copies_command(logged_in_page: Page):
    """Clicking copy button copies the command to clipboard."""
    page = logged_in_page
    _intercept_insights(page, CRITICAL_PAYLOAD)
    page.context.grant_permissions(["clipboard-read", "clipboard-write"])
    page.reload()
    copy_btn = page.locator('[data-testid="copy-button"]').first
    copy_btn.wait_for(state="visible", timeout=10000)
    copy_btn.click()
    clip = page.evaluate("navigator.clipboard.readText()")
    assert clip == "top -o %CPU"


def test_aria_labels_present(logged_in_page: Page):
    """Every copy button has an aria-label; live region exists."""
    page = logged_in_page
    _intercept_insights(page, CRITICAL_PAYLOAD)
    page.reload()
    page.wait_for_selector('[data-testid="copy-button"]', timeout=10000)
    btns = page.locator('[data-testid="copy-button"]').all()
    assert len(btns) == 2
    for btn in btns:
        label = btn.get_attribute("aria-label")
        assert (label and label.startswith("Copy command")) or label.startswith("نسخ")
    assert page.locator('[role="status"][aria-live="polite"]').count() >= 1


def test_action_click_fires_audit(logged_in_page: Page):
    """Clicking action button POSTs to /api/audit/action-url-click."""
    page = logged_in_page
    _intercept_insights(page, CRITICAL_PAYLOAD)
    page.reload()
    page.wait_for_selector('[data-testid="action-button"]', timeout=10000)
    audit_calls = []
    page.on(
        "request",
        lambda req: (
            audit_calls.append(req.url) if "/api/audit/action-url-click" in req.url else None
        ),
    )
    page.route("https://awx.example.com/**", lambda route: route.abort())
    btn = page.locator('[data-testid="action-button"]').first
    btn.click()
    page.wait_for_timeout(500)
    assert any("action-url-click" in url for url in audit_calls), (
        f"no audit call fired; captured: {audit_calls}"
    )
