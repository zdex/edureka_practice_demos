from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = {"date", "description", "amount"}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    aliases = {
        "transaction date": "date",
        "txn date": "date",
        "transaction_date": "date",
        "narration": "description",
        "merchant": "description",
        "details": "description",
        "transaction details": "description",
        "value": "amount",
        "transaction amount": "amount",
    }
    df = df.rename(columns={c: aliases.get(str(c).strip().lower(), str(c).strip().lower()) for c in df.columns})
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            "Missing required column(s): " + ", ".join(sorted(missing)) + ". Required: date, description, amount."
        )

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["description"] = df["description"].astype(str).str.strip()
    amount_text = (
        df["amount"].astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("₹", "", regex=False)
        .str.replace("$", "", regex=False)
        .str.replace("€", "", regex=False)
        .str.strip()
    )
    parentheses = amount_text.str.match(r"^\(.*\)$")
    amount_text = amount_text.str.replace("(", "", regex=False).str.replace(")", "", regex=False)
    df["amount"] = pd.to_numeric(amount_text, errors="coerce")
    df.loc[parentheses, "amount"] = -df.loc[parentheses, "amount"].abs()
    df = df.dropna(subset=["date", "amount"])
    df = df[df["description"].str.len() > 0]
    if "category" not in df.columns:
        df["category"] = ""
    else:
        df["category"] = df["category"].fillna("").astype(str).str.strip()
    return df.sort_values("date").reset_index(drop=True)


def load_transactions(uploaded_file) -> pd.DataFrame:
    name = getattr(uploaded_file, "name", "").lower()
    raw = uploaded_file.getvalue() if hasattr(uploaded_file, "getvalue") else uploaded_file.read()
    if name.endswith(".csv"):
        df = pd.read_csv(BytesIO(raw))
    elif name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(BytesIO(raw))
    else:
        raise ValueError("Please upload a CSV or XLSX bank-transaction export.")
    return _normalize_columns(df)


def load_sample(path: str | Path = "sample_data/sample_transactions.csv") -> pd.DataFrame:
    return _normalize_columns(pd.read_csv(path))
