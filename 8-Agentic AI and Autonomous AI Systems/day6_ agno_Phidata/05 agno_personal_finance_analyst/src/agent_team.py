from pathlib import Path
import pandas as pd
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.google import Gemini
from agno.team import Team, TeamMode
from .config import settings
from .finance_tools import build_finance_tools
from .schemas import FinanceReport

def build_finance_team(df: pd.DataFrame, debug_mode: bool=False) -> Team:
    Path('data').mkdir(exist_ok=True)
    t = build_finance_tools(df)
    model = Gemini(id=settings.gemini_model)
    members = [
        Agent(id='transaction-analyst', name='Transaction Analyst', 
              role='Establish factual cash flow.', model=model,
              tools=[t['snapshot'], t['monthly']], 
              instructions=['Use tools for every number. Do not invent data.']),
        Agent(id='spending-analyst', name='Spending Pattern Analyst', 
              role='Find category and recurring-spend patterns.', model=model,
              tools=[t['categories'], t['recurring']], 
              instructions=['Identify largest categories and recurring merchants.']),
        Agent(id='anomaly-analyst', name='Unusual Transaction Reviewer', 
              role='Highlight transactions for manual review.', model=model,
              tools=[t['unusual']],
              instructions=['Never label a transaction as fraud.']),
        Agent(id='budget-advisor', name='Budget Advisor', role='Turn evidence into practical budgeting actions.', model=model,
              tools=[t['snapshot'], t['categories'], t['budget']], 
              instructions=['Avoid investment, tax, credit or legal advice.']),
        Agent(id='finance-coach', name='Finance Coach', role='Create a simple next-month action plan.', model=model,
              tools=[t['monthly'], t['budget'], t['recurring']], 
              instructions=['Prioritize 3-5 actions in plain language.']),
    ]
    return Team(
        id='personal-finance-team', name='Personal Finance Analysis Team', 
        model=model, members=members,
        mode=TeamMode.coordinate,
        instructions=[
            'Create a complete cash-flow and spending report.',
            'Delegate to specialists and use tool evidence for numerical claims.',
            'Flag unusual transactions only as items for review; never claim fraud.',
            'Keep the result concise, practical, and educational.',
        ],
        output_schema=FinanceReport,
        db=SqliteDb(db_file=settings.db_file), add_history_to_context=True, num_history_runs=2,
        show_members_responses=debug_mode, debug_mode=debug_mode,
    )
