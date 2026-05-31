from __future__ import annotations

import os

import pytest


def test_browser_can_reach_running_app():
    base_url = os.getenv("MOCK_INTERVIEW_BASE_URL")
    if not base_url:
        pytest.skip("Set MOCK_INTERVIEW_BASE_URL to run the Playwright browser smoke test.")

    playwright = pytest.importorskip("playwright.sync_api")

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(base_url, wait_until="networkidle")

        health = page.evaluate(
            """async () => {
                const response = await fetch('/api/health');
                return response.json();
            }"""
        )

        browser.close()

    assert health == {"status": "running", "app": "Mock Interview MVP"}
