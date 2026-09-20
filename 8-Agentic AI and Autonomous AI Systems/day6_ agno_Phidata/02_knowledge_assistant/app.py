"""LEVEL 2 - Knowledge + persistent conversation context

Concepts demonstrated:
1. Everything from Level 1
2. Agentic RAG over a local document
3. Google Gemini embeddings (free tier where available)
4. Local Chroma vector database
5. SQLite-backed chat history

Required:
- GROQ_API_KEY: generation/reasoning
- GOOGLE_API_KEY: embeddings
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.knowledge.embedder.google import GeminiEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.models.groq import Groq
from agno.vectordb.chroma import ChromaDb
from agno.vectordb.search import SearchType

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

for key in ("GROQ_API_KEY", "GOOGLE_API_KEY"):
    if not os.getenv(key):
        raise RuntimeError(f"Missing {key}. Copy .env.example to .env and add your key.")

TMP = HERE / "tmp"
TMP.mkdir(exist_ok=True)

knowledge = Knowledge(
    vector_db=ChromaDb(
        collection="novaworks_policy",
        path=str(TMP / "chromadb"),
        persistent_client=True,
        search_type=SearchType.vector,
        embedder=GeminiEmbedder(
            id="gemini-embedding-001",
            dimensions=3072,
        ),
    )
)

# Insert the local classroom document. skip_if_exists makes repeated runs convenient.
knowledge.insert(
    path=str(HERE / "data" / "company_policy.md"),
    name="NovaWorks Travel Policy",
    skip_if_exists=True,
)

assistant = Agent(
    name="NovaWorks Policy Assistant",
    model=Groq(id=GROQ_MODEL),
    knowledge=knowledge,
    db=SqliteDb(db_file=str(TMP / "sessions.db")),
    session_id="classroom_demo",
    add_history_to_context=True,
    num_history_runs=4,
    instructions=[
        "Answer questions about NovaWorks policy from the knowledge base.",
        "Search the knowledge base before answering policy-specific questions.",
        "Quote policy limits and approval conditions precisely.",
        "If the policy does not contain the answer, explicitly say that it is not stated in the provided policy.",
        "Use recent chat history to resolve follow-up questions such as 'what about meals?' or 'and for Europe?'.",
    ],
    markdown=True,
)


def main() -> None:
    print("\n=== LEVEL 2: Knowledge + Context Assistant ===")
    print("Ask about the fictional NovaWorks travel policy. Type 'exit' to stop.\n")
    while True:
        question = input("You: ").strip()
        if question.lower() in {"exit", "quit", "q"}:
            break
        if not question:
            continue
        assistant.print_response(question, stream=True)
        print()


if __name__ == "__main__":
    main()
