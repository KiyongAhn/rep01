"""Report Generator skill entry point."""


def execute(params: dict) -> dict:
    """Generate a report based on the given parameters.

    Parameters
    ----------
    params:
        Must contain ``report_type`` and ``period``.  Optionally
        ``data_source``.

    Returns
    -------
    Dict with ``status``, ``report_path``, and ``summary``.
    """
    report_type = params.get("report_type", "sales")
    period = params.get("period", "Q4")
    data_source = params.get("data_source")

    # Simulated report generation logic
    summary_map = {
        "sales": {
            "total_sales": 1_000_000,
            "growth_rate": "12%",
            "top_product": "Widget A",
        },
        "analytics": {
            "total_visits": 500_000,
            "bounce_rate": "35%",
            "avg_session": "4m 32s",
        },
        "performance": {
            "uptime": "99.9%",
            "avg_response_ms": 120,
            "error_rate": "0.1%",
        },
    }

    summary = summary_map.get(report_type, {"note": "unknown report type"})

    return {
        "status": "success",
        "report_path": f"/tmp/{report_type}_{period}.pdf",
        "summary": summary,
    }
