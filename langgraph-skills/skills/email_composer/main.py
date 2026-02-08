"""Email Composer skill entry point."""


_TEMPLATES = {
    "follow_up": (
        "Following Up on Our Previous Discussion",
        (
            "Dear {recipient},\n\n"
            "I wanted to follow up on our recent conversation. "
            "{points_text}"
            "Please let me know if you have any questions or need further information.\n\n"
            "Best regards"
        ),
    ),
    "meeting_request": (
        "Meeting Request: {subject_hint}",
        (
            "Dear {recipient},\n\n"
            "I would like to schedule a meeting to discuss the following:\n"
            "{points_text}\n"
            "Please let me know your availability.\n\n"
            "Best regards"
        ),
    ),
    "status_update": (
        "Status Update: {subject_hint}",
        (
            "Hi {recipient},\n\n"
            "Here is the latest status update:\n"
            "{points_text}\n"
            "Let me know if you have any questions.\n\n"
            "Best regards"
        ),
    ),
    "introduction": (
        "Introduction: {subject_hint}",
        (
            "Dear {recipient},\n\n"
            "I hope this email finds you well. I am reaching out to introduce myself. "
            "{points_text}"
            "I look forward to connecting with you.\n\n"
            "Best regards"
        ),
    ),
}


def execute(params: dict) -> dict:
    """Compose an email based on the given parameters.

    Parameters
    ----------
    params:
        Must contain ``email_type`` and ``recipient``.  Optionally
        ``subject``, ``key_points``, and ``tone``.

    Returns
    -------
    Dict with ``status``, ``subject``, and ``body``.
    """
    email_type = params.get("email_type", "follow_up")
    recipient = params.get("recipient", "Team")
    subject_hint = params.get("subject", email_type.replace("_", " ").title())
    key_points = params.get("key_points", [])
    tone = params.get("tone", "formal")

    if key_points:
        points_text = "\n".join(f"- {p}" for p in key_points) + "\n\n"
    else:
        points_text = ""

    template_pair = _TEMPLATES.get(email_type, _TEMPLATES["follow_up"])
    subject_line = template_pair[0].format(
        recipient=recipient, subject_hint=subject_hint
    )
    body = template_pair[1].format(
        recipient=recipient,
        points_text=points_text,
        subject_hint=subject_hint,
    )

    if tone == "casual":
        body = body.replace("Dear", "Hey").replace("Best regards", "Cheers")
    elif tone == "friendly":
        body = body.replace("Dear", "Hi").replace("Best regards", "Warm regards")

    return {
        "status": "success",
        "subject": subject_line,
        "body": body,
    }
