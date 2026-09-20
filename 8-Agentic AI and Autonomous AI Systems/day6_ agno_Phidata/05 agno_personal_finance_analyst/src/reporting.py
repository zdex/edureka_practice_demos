from __future__ import annotations

from typing import Any


def report_to_dict(content: Any) -> dict:
    if hasattr(content, "model_dump"):
        return content.model_dump()
    if isinstance(content, dict):
        return content
    return {
        "executive_summary": str(content),
        "positives": [],
        "needs_attention": [],
        "unusual_transactions": [],
        "budget_actions": [],
        "monthly_observations": [],
        "savings_target": "",
        "disclaimer": "Educational budgeting analysis only; not financial advice.",
    }
