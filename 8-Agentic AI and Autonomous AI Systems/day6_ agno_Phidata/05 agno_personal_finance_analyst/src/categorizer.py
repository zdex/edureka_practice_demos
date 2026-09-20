from __future__ import annotations

from functools import lru_cache
import numpy as np
import pandas as pd

CATEGORY_PROFILES = {
    "Housing": "rent apartment home housing landlord mortgage",
    "Groceries": "supermarket grocery vegetables household food store",
    "Dining": "restaurant cafe coffee takeaway food delivery dining",
    "Transport": "taxi cab metro bus train fuel petrol parking transport",
    "Shopping": "shopping ecommerce clothes electronics retail purchase",
    "Utilities": "electricity water gas internet mobile phone utility bill",
    "Entertainment": "movie cinema streaming games entertainment subscription",
    "Health": "doctor pharmacy medicine hospital healthcare fitness gym",
    "Education": "course tuition books training education school",
    "Travel": "flight hotel airline holiday travel accommodation",
    "Fees": "bank fee charge penalty atm fee service charge",
    "Transfers": "transfer upi transfer bank transfer wallet transfer",
    "Income": "salary payroll refund cashback interest income credit",
    "Other": "other miscellaneous transaction",
}

KEYWORDS = {
    "Housing": ["rent", "landlord", "mortgage"],
    "Groceries": ["grocery", "supermarket", "bigbasket", "dmart", "reliance fresh"],
    "Dining": ["swiggy", "zomato", "restaurant", "cafe", "coffee", "starbucks"],
    "Transport": ["uber", "ola", "metro", "bus", "fuel", "petrol", "parking", "cab"],
    "Shopping": ["amazon", "flipkart", "myntra", "shopping", "retail"],
    "Utilities": ["electric", "electricity", "airtel", "jio", "internet", "mobile", "water"],
    "Entertainment": ["netflix", "spotify", "prime video", "cinema", "movie"],
    "Health": ["pharmacy", "apollo", "hospital", "clinic", "doctor", "gym", "medical"],
    "Education": ["udemy", "coursera", "course", "tuition", "books"],
    "Travel": ["air india", "indigo", "hotel", "booking.com", "airbnb", "flight"],
    "Fees": ["fee", "penalty", "service charge"],
    "Transfers": ["transfer", "upi transfer"],
    "Income": ["salary", "payroll", "refund", "cashback", "interest credit"],
}


def _keyword_category(description: str, amount: float) -> str | None:
    text = description.lower()
    if amount > 0 and any(x in text for x in KEYWORDS["Income"]):
        return "Income"
    for category, words in KEYWORDS.items():
        if category == "Income":
            continue
        if any(word in text for word in words):
            return category
    return None


@lru_cache(maxsize=1)
def _load_embedding_model(model_name: str):
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(model_name)


@lru_cache(maxsize=4)
def _category_embeddings(model_name: str):
    model = _load_embedding_model(model_name)
    labels = list(CATEGORY_PROFILES.keys())
    vectors = model.encode([CATEGORY_PROFILES[k] for k in labels], normalize_embeddings=True)
    return labels, vectors


def classify_description(description: str, amount: float, model_name: str) -> str:
    keyword = _keyword_category(description, amount)
    if keyword:
        return keyword
    candidate_labels = ["Income", "Transfers", "Other"] if amount > 0 else [
        "Housing", "Groceries", "Dining", "Transport", "Shopping", "Utilities",
        "Entertainment", "Health", "Education", "Travel", "Fees", "Transfers", "Other"
    ]
    labels, category_vectors = _category_embeddings(model_name)
    query = _load_embedding_model(model_name).encode([description], normalize_embeddings=True)[0]
    indices = [labels.index(label) for label in candidate_labels]
    sims = np.dot(category_vectors[indices], query)
    return candidate_labels[int(np.argmax(sims))]


def add_categories(df: pd.DataFrame, model_name: str, use_embeddings: bool = True) -> pd.DataFrame:
    df = df.copy()
    results = []
    for _, row in df.iterrows():
        existing = str(row.get("category", "") or "").strip()
        if existing:
            results.append(existing)
        elif use_embeddings:
            results.append(classify_description(str(row["description"]), float(row["amount"]), model_name))
        else:
            results.append(_keyword_category(str(row["description"]), float(row["amount"])) or "Other")
    df["category"] = results
    return df
