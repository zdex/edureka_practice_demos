"""LEVEL 3 - Multi-agent business research team

Concepts demonstrated:
1. Specialist agents
2. Different tools per specialist
3. Team leader / delegation
4. Dynamic coordination and synthesis
5. Free/no-key data sources beyond Groq itself

Required:
- GROQ_API_KEY

External resources:
- DuckDuckGo via ddgs: no API key
- Yahoo Finance via yfinance: no API key
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.groq import Groq
from agno.team.mode import TeamMode
from agno.team.team import Team
from agno.tools.websearch import WebSearchTools
from agno.tools.yfinance import YFinanceTools

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

if not os.getenv("GROQ_API_KEY"):
    raise RuntimeError("Missing GROQ_API_KEY. Copy .env.example to .env and add your key.")

model = Groq(id=GROQ_MODEL)

company_researcher = Agent(
    name="Company Researcher",
    role="Research a company's products, strategy, competitors, market position, and major business developments.",
    model=model,
    tools=[WebSearchTools(backend="duckduckgo", enable_search=True, enable_news=False, fixed_max_results=5)],
    instructions=[
        "Use web search for factual company and market information.",
        "Separate verified facts from interpretation.",
        "Return URLs for the most important sources.",
    ],
)

financial_analyst = Agent(
    name="Financial Analyst",
    role="Analyze public-market financial information and stock data for listed companies.",
    model=model,
    tools=[YFinanceTools()],
    instructions=[
        "Use Yahoo Finance tools instead of guessing financial figures.",
        "Focus on metrics useful for an executive briefing: price, market capitalization, valuation, growth/profitability information when available, and analyst signals.",
        "State when a requested metric is unavailable.",
    ],
)

news_risk_analyst = Agent(
    name="News and Risk Analyst",
    role="Find recent news, controversies, regulatory issues, competitive threats, and other material risks.",
    model=model,
    tools=[WebSearchTools(backend="duckduckgo", enable_search=False, enable_news=True, fixed_max_results=6)],
    instructions=[
        "Search recent news relevant to the company.",
        "Distinguish reported facts from possible implications.",
        "Prioritize material business risks rather than general headlines.",
        "Return URLs for important news items.",
    ],
)

research_team = Team(
    name="Executive Research Team",
    mode=TeamMode.coordinate,
    model=model,
    members=[company_researcher, financial_analyst, news_risk_analyst],
    instructions=[
        "Act as the lead analyst.",
        "Delegate company/market research to Company Researcher.",
        "Delegate public financial analysis to Financial Analyst when the target is publicly listed.",
        "Delegate current news and risk research to News and Risk Analyst.",
        "Use multiple members when the user's request spans their specialties.",
        "Synthesize the member findings into one executive briefing.",
        "Use these headings where relevant: Executive Summary, Business & Market, Financial Snapshot, Recent Developments, Risks, Opportunities, Bottom Line, Sources.",
        "Do not invent missing data and do not present the briefing as investment advice.",
    ],
    show_members_responses=True,
    markdown=True,
)


def main() -> None:
    print("\n=== LEVEL 3: Multi-Agent Executive Research Team ===")
    print("Example: 'Prepare an executive briefing on NVIDIA (NVDA).'\n")
    prompt = input("Research request: ").strip()
    if not prompt:
        prompt = "Prepare an executive briefing on NVIDIA (NVDA), including market position, financial snapshot, recent news, risks, and opportunities."
    research_team.print_response(prompt, stream=True)


if __name__ == "__main__":
    main()
