from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    hf_embedding_model: str = os.getenv(
        "HF_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    db_file: str = "data/finance_agents.db"


settings = Settings()
