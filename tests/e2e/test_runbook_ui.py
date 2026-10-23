"""E2E — Runbook UI (deterministic, no network race)."""

import pytest
from playwright.sync_api import Page, expect

CRITICAL = {
    "ok": True,
    "summary": "CPU critical (95%)",
    "insights": ["CPU critical"],
    "runbook": {
        "title": "CPU Critical",
        "severity": "critical",
        "steps": [
            {"step": "Check top", "command": "top -o %CPU", "platform_hint": "linux"},
            {"step": "Restart", "command": None, "platform_hint": "generic"},
        ],
        "action_url": "https://awx.example.com/rb",
    },
    "stats": {},
}

HEALTHY = {
    "ok": True,
    "summary": "healthy",
    "insights": ["healthy"],
    "runbook": None,
    "stats": {},
}


def _inject(page: Page, payload: dict) -> None:
    """زرع بيانات insights مباشرة في Alpine — لا شبكة، لا race."""
    page.evaluate(
        """(data) => {
            const root = document.querySelector('[data-testid="dashboard"]');
            if (!root || !window.Alpine) throw new Error('Alpine not loaded');
            // Alpine reactive setter عبر $data
            const el = document.body;
            const state = window.Alpine.$data(el);
            state.insights = data;
            state.insightsLoaded = true;
        }""",
        payload,
    )


def test_runbook_card_renders(logged_in_page: Page):
    page = logged_in_page
    _inject(page, CRITICAL)

    badge = page.locator('[data-testid="severity-badge"]')
    expect(badge).to_have_text("CRITICAL", timeout=10000)

    steps = page.locator('[data-testid="runbook-step"]')
    expect(steps).to_have_count(2)


def test_empty_state_when_healthy(logged_in_page: Page):
    page = logged_in_page
    _inject(page, HEALTHY)

    expect(page.locator('[data-testid="empty-state"]')).to_be_visible(timeout=10000)


def test_severity_color_critical(logged_in_page: Page):
    page = logged_in_page
    _inject(page, CRITICAL)

    card = page.locator('[data-testid="runbook-card"]')
    expect(card).to_be_visible(timeout=10000)
    expect(card).to_have_class(pytest.mark.parametrize if False else ".*border-red-500.*")


def test_copy_button_present(logged_in_page: Page):
    page = logged_in_page
    _inject(page, CRITICAL)

    btns = page.locator('[data-testid="copy-button"]')
    expect(btns).to_have_count(1, timeout=10000)  # خطوة واحدة فيها command


def test_aria_labels_present(logged_in_page: Page):
    page = logged_in_page
    _inject(page, CRITICAL)

    page.locator('[data-testid="copy-button"]').first.wait_for(state="visible", timeout=10000)
    label = page.locator('[data-testid="copy-button"]').first.get_attribute("aria-label")
    assert label and label.startswith("نسخ الأمر")


def test_action_click_fires_audit(logged_in_page: Page):
    page = logged_in_page
    _inject(page, CRITICAL)

    calls = []
    page.on("request", lambda r: calls.append(r.url) if "/api/audit/" in r.url else None)
    page.route("https://awx.example.com/**", lambda r: r.abort())

    btn = page.locator('[data-testid="action-button"]')
    expect(btn).to_be_visible(timeout=10000)
    btn.click()
    page.wait_for_timeout(500)
    assert any("action-url-click" in u for u in calls), f"no audit: {calls}"
