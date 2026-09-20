"""LEVEL 1 - Simple Agno Research Agent

Concepts demonstrated:
1. Agent
2. LLM/model
3. Instructions
4. Tool use
5. Streaming response

Only GROQ_API_KEY is required for this level.
DuckDuckGo search does not require an API key.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.websearch import WebSearchTools

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

if not os.getenv("GROQ_API_KEY"):
    raise RuntimeError("Missing GROQ_API_KEY. Copy .env.example to .env and add your key.")

research_agent = Agent(
    name="Research Assistant",
    model=Groq(id=GROQ_MODEL),
    tools=[
        WebSearchTools(
            backend="duckduckgo",
            enable_search=True,
            enable_news=True,
            fixed_max_results=5,
        )
    ],
    description="A beginner-friendly web research agent.",
    instructions=[
        "Search the web when the question needs current or externally verifiable information.",
        "Prefer credible sources and compare more than one source for important claims.",
        "Give a concise answer with a short Sources section containing the URLs returned by the search tool.",
        "If reliable information is not found, say so rather than inventing an answer.",
    ],
    markdown=True,
    add_datetime_to_context=True,
)


def main() -> None:
    print("\n=== LEVEL 1: Agno Research Assistant ===")
    print("Type 'exit' to stop.\n")
    while True:
        question = input("You: ").strip()
        if question.lower() in {"exit", "quit", "q"}:
            break
        if not question:
            continue
        research_agent.print_response(question, stream=True)
        print()


if __name__ == "__main__":
    main()
