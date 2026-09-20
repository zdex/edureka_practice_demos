from __future__ import annotations

import re
import numpy as np
import pandas as pd

DISCRETIONARY = {"Dining", "Shopping", "Entertainment", "Travel"}


def _expense_rows(df: pd.DataFrame) -> pd.DataFrame:
    out = df[df["amount"] < 0].copy()
    out["expense"] = out["amount"].abs()
    return out


def finance_snapshot(df: pd.DataFrame) -> dict:
    income = float(df.loc[df["amount"] > 0, "amount"].sum())
    expenses = float(df.loc[df["amount"] < 0, "amount"].abs().sum())
    net = float(df["amount"].sum())
    return {
        "transactions": int(len(df)),
        "start_date": df["date"].min().date().isoformat(),
        "end_date": df["date"].max().date().isoformat(),
        "total_income": round(income, 2),
        "total_expenses": round(expenses, 2),
        "net_cash_flow": round(net, 2),
        "savings_rate_percent": round((net / income * 100.0) if income > 0 else 0.0, 1),
    }


def category_spending(df: pd.DataFrame) -> list[dict]:
    expenses = _expense_rows(df)
    if expenses.empty:
        return []
    grouped = expenses.groupby("category", dropna=False)["expense"].sum().sort_values(ascending=False)
    total = grouped.sum()
    return [
        {"category": str(category), "amount": round(float(amount), 2),
         "percent_of_expenses": round(float(amount / total * 100), 1) if total else 0}
        for category, amount in grouped.items()
    ]


def monthly_summary(df: pd.DataFrame) -> list[dict]:
    work = df.copy()
    work["month"] = work["date"].dt.to_period("M").astype(str)
    rows = []
    for month, grp in work.groupby("month"):
        income = grp.loc[grp["amount"] > 0, "amount"].sum()
        expenses = grp.loc[grp["amount"] < 0, "amount"].abs().sum()
        net = grp["amount"].sum()
        rows.append({
            "month": month,
            "income": round(float(income), 2),
            "expenses": round(float(expenses), 2),
            "net_cash_flow": round(float(net), 2),
            "savings_rate_percent": round(float(net / income * 100), 1) if income > 0 else 0.0,
        })
    return rows


def _merchant_key(description: str) -> str:
    text = description.lower()
    text = re.sub(r"\b\d{2,}\b", "", text)
    text = re.sub(r"[^a-z ]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def recurring_transactions(df: pd.DataFrame) -> list[dict]:
    expenses = _expense_rows(df)
    if expenses.empty:
        return []
    expenses["merchant_key"] = expenses["description"].map(_merchant_key)
    rows = []
    for merchant, grp in expenses.groupby("merchant_key"):
        if len(grp) < 2 or not merchant:
            continue
        amounts = grp["expense"].astype(float)
        mean = float(amounts.mean())
        spread = float(amounts.std(ddof=0) / mean) if mean else 99
        if spread <= 0.20:
            rows.append({"merchant": merchant.title(), "count": int(len(grp)),
                         "average_amount": round(mean, 2), "total_amount": round(float(amounts.sum()), 2)})
    return sorted(rows, key=lambda x: x["total_amount"], reverse=True)[:10]


def unusual_transactions(df: pd.DataFrame, limit: int = 8) -> list[dict]:
    expenses = _expense_rows(df)
    if len(expenses) < 3:
        return []
    values = expenses["expense"].astype(float)
    median = float(values.median())
    mad = float(np.median(np.abs(values - median)))
    robust_z = pd.Series([0.0] * len(values), index=values.index) if mad == 0 else 0.6745 * (values - median) / mad
    expenses["robust_z"] = robust_z
    candidates = expenses.sort_values(["robust_z", "expense"], ascending=False).head(limit)
    result = []
    for _, row in candidates.iterrows():
        reasons = []
        if float(row["robust_z"]) >= 3.5:
            reasons.append("much larger than typical expense")
        if float(row["expense"]) >= values.quantile(0.90):
            reasons.append("top 10% expense")
        if str(row["category"]) == "Fees":
            reasons.append("bank/transaction fee")
        if reasons:
            result.append({"date": row["date"].date().isoformat(), "description": str(row["description"]),
                           "amount": round(float(row["expense"]), 2), "category": str(row["category"]),
                           "reason": ", ".join(reasons)})
    return result[:limit]


def budget_signals(df: pd.DataFrame) -> dict:
    snap = finance_snapshot(df)
    cats = category_spending(df)
    discretionary = sum(x["amount"] for x in cats if x["category"] in DISCRETIONARY)
    expenses = snap["total_expenses"]
    fees = sum(x["amount"] for x in cats if x["category"] == "Fees")
    return {
        "discretionary_spend": round(discretionary, 2),
        "discretionary_percent_of_expenses": round(discretionary / expenses * 100.0, 1) if expenses else 0.0,
        "fees_paid": round(fees, 2),
        "net_cash_flow": snap["net_cash_flow"],
        "savings_rate_percent": snap["savings_rate_percent"],
    }


def deterministic_report(df: pd.DataFrame, currency: str = "₹") -> dict:
    snap = finance_snapshot(df)
    cats = category_spending(df)
    months = monthly_summary(df)
    unusual = unusual_transactions(df)
    signals = budget_signals(df)
    positives, needs, actions = [], [], []
    if snap["net_cash_flow"] > 0:
        positives.append(f"Cash flow is positive by {currency}{snap['net_cash_flow']:,.0f} over the selected period.")
    else:
        needs.append(f"Expenses exceed income by {currency}{abs(snap['net_cash_flow']):,.0f}.")
    if snap["savings_rate_percent"] >= 20:
        positives.append(f"Observed savings rate is about {snap['savings_rate_percent']:.1f}%.")
    elif snap["total_income"] > 0:
        needs.append(f"Observed savings rate is about {snap['savings_rate_percent']:.1f}%; review flexible spending.")
    if cats:
        top = cats[0]
        needs.append(f"Largest expense category is {top['category']} at {currency}{top['amount']:,.0f} ({top['percent_of_expenses']:.1f}% of expenses).")
    if signals["fees_paid"] > 0:
        actions.append(f"Review avoidable bank/transaction fees totaling about {currency}{signals['fees_paid']:,.0f}.")
    actions.append("Set a monthly cap for discretionary categories and review it weekly.")
    actions.append("Automate savings soon after income arrives, then spend from the remaining balance.")
    monthly_obs = []
    if len(months) >= 2:
        prev, current = months[-2], months[-1]
        delta = current["expenses"] - prev["expenses"]
        monthly_obs.append(f"Expenses {'increased' if delta > 0 else 'decreased'} by {currency}{abs(delta):,.0f} from {prev['month']} to {current['month']}.")
    return {
        "executive_summary": f"Income was {currency}{snap['total_income']:,.0f}, expenses were {currency}{snap['total_expenses']:,.0f}, and net cash flow was {currency}{snap['net_cash_flow']:,.0f}.",
        "positives": positives,
        "needs_attention": needs,
        "unusual_transactions": [f"{x['date']}: {x['description']} ({currency}{x['amount']:,.0f}) — {x['reason']}" for x in unusual],
        "budget_actions": actions,
        "monthly_observations": monthly_obs,
        "savings_target": "Start with a target near 15–20% of monthly income if realistic after essential expenses.",
        "disclaimer": "Educational budgeting analysis only; it is not financial, tax, or investment advice.",
    }
