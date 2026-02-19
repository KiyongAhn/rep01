---
name: email_composer
description: Compose professional emails for various purposes
---

# Email Composer Skill

## Purpose
Compose professional emails for various business purposes such as follow-ups, meeting requests, and status updates.

## Parameters
- `email_type`: Type of email to compose. One of: `follow_up`, `meeting_request`, `status_update`, `introduction`.
- `recipient`: Name or role of the recipient (e.g. "John Smith", "Engineering Team").
- `subject`: (optional) Email subject line. Auto-generated if omitted.
- `key_points`: (optional) List of key points to include in the email body.
- `tone`: (optional) Tone of the email. One of: `formal`, `casual`, `friendly`. Defaults to `formal`.

## Output
Returns a dict with:
- `status`: `"success"` or `"error"`
- `subject`: The email subject line
- `body`: The composed email body text
