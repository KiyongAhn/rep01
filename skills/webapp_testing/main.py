"""Web Application Testing skill entry point.

Simulates Playwright-based web testing. In a production environment this would
use ``playwright.sync_api`` to drive a real browser.  Here we simulate the
actions so the skill can be tested without installing Playwright.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any


def _simulate_screenshot(path: str | None, url: str) -> dict:
    path = path or f"/tmp/screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    return {
        "action": "screenshot",
        "status": "success",
        "path": path,
        "message": f"Screenshot of {url} saved to {path}",
    }


def _simulate_click(selector: str) -> dict:
    return {
        "action": "click",
        "status": "success",
        "selector": selector,
        "message": f"Clicked element: {selector}",
    }


def _simulate_fill(selector: str, value: str) -> dict:
    return {
        "action": "fill",
        "status": "success",
        "selector": selector,
        "value": value,
        "message": f"Filled '{value}' into element: {selector}",
    }


def _simulate_check_text(selector: str | None, text: str) -> dict:
    return {
        "action": "check_text",
        "status": "success",
        "text": text,
        "found": True,
        "message": f"Text '{text}' found on page",
    }


def _simulate_console_logs() -> dict:
    return {
        "action": "get_console_logs",
        "status": "success",
        "logs": [
            {"level": "info", "message": "[APP] Application started"},
            {"level": "warn", "message": "[APP] Deprecation warning: use v2 API"},
        ],
    }


_ACTION_HANDLERS: dict[str, Any] = {
    "screenshot": lambda a, url: _simulate_screenshot(a.get("path"), url),
    "click": lambda a, url: _simulate_click(a.get("selector", "")),
    "fill": lambda a, url: _simulate_fill(a.get("selector", ""), a.get("value", "")),
    "check_text": lambda a, url: _simulate_check_text(a.get("selector"), a.get("text", "")),
    "get_console_logs": lambda a, url: _simulate_console_logs(),
}


def execute(params: dict) -> dict:
    """Run a sequence of browser test actions against a target URL.

    Parameters
    ----------
    params:
        Must contain ``url`` and ``actions``.  Optionally ``wait_for_idle``
        and ``headless``.

    Returns
    -------
    Dict with ``status``, ``results``, ``url``, and ``browser_config``.
    """
    url = params.get("url", "http://localhost:3000")
    actions = params.get("actions", [])
    wait_for_idle = params.get("wait_for_idle", True)
    headless = params.get("headless", True)

    if not actions:
        return {
            "status": "error",
            "message": "No actions specified",
        }

    results: list[dict] = []
    console_logs: list[dict] = []

    for action in actions:
        action_type = action.get("type", "")
        handler = _ACTION_HANDLERS.get(action_type)
        if handler is None:
            results.append({
                "action": action_type,
                "status": "error",
                "message": f"Unknown action type: {action_type}",
            })
            continue

        result = handler(action, url)
        results.append(result)

        # Collect console logs separately for easy access
        if action_type == "get_console_logs":
            console_logs = result.get("logs", [])

    return {
        "status": "success",
        "url": url,
        "browser_config": {
            "headless": headless,
            "wait_for_idle": wait_for_idle,
        },
        "results": results,
        "console_logs": console_logs,
    }
