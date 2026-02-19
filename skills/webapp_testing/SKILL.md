---
name: webapp_testing
description: Test local web applications using Playwright - verify frontend functionality, capture screenshots, and view browser logs
---

# Web Application Testing Skill

## Purpose
Test local web applications using Playwright. Supports verifying frontend
functionality, debugging UI behaviour, capturing browser screenshots, and
viewing browser console logs.

Based on the [Anthropic official webapp-testing skill](https://github.com/anthropics/skills/tree/main/skills/webapp-testing).

## Parameters
- `url`: Target URL to test (e.g. `http://localhost:3000`).
- `actions`: List of actions to perform. Each action is a dict:
  - `type`: One of `screenshot`, `click`, `fill`, `check_text`, `get_console_logs`.
  - `selector`: (for click/fill/check_text) CSS or text selector.
  - `value`: (for fill) Text value to enter.
  - `text`: (for check_text) Expected text on the page.
  - `path`: (for screenshot) File path to save the screenshot.
- `wait_for_idle`: (optional) Whether to wait for `networkidle` before running
  actions. Defaults to `true`.
- `headless`: (optional) Run in headless mode. Defaults to `true`.

## Output
Returns a dict with:
- `status`: `"success"` or `"error"`
- `results`: List of results, one per action
- `console_logs`: Browser console messages collected during the session (if requested)
