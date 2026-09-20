from __future__ import annotations

import json
import pandas as pd
from .analytics import budget_signals, category_spending, finance_snapshot, monthly_summary, recurring_transactions, unusual_transactions


def build_finance_tools(df: pd.DataFrame):
    def get_finance_snapshot() -> str:
        """Return total income, expenses, net cash flow, date range, transaction count, and savings rate."""
        return json.dumps(finance_snapshot(df), indent=2)
    def get_category_spending() -> str:
        """Return expense totals and percentages by spending category."""
        return json.dumps(category_spending(df), indent=2)
    def get_monthly_trends() -> str:
        """Return month-by-month income, expenses, net cash flow, and savings rate."""
        return json.dumps(monthly_summary(df), indent=2)
    def get_recurring_transactions() -> str:
        """Return merchants that repeat with roughly similar transaction amounts."""
        return json.dumps(recurring_transactions(df), indent=2)
    def get_unusual_transactions() -> str:
        """Return statistically large or fee-like transactions worth reviewing. This does not detect fraud."""
        return json.dumps(unusual_transactions(df), indent=2)
    def get_budget_signals() -> str:
        """Return deterministic budget signals such as discretionary share, fees, cash flow, and savings rate."""
        return json.dumps(budget_signals(df), indent=2)
    return {"snapshot": get_finance_snapshot, "categories": get_category_spending, "monthly": get_monthly_trends,
            "recurring": get_recurring_transactions, "unusual": get_unusual_transactions, "budget": get_budget_signals}
