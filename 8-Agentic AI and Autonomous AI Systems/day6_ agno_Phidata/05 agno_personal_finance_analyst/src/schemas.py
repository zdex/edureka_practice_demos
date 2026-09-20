from __future__ import annotations

from pydantic import BaseModel, Field


class FinanceReport(BaseModel):
    """Validated final output produced by the Agno team leader."""

    executive_summary: str = Field(
        description="A concise summary of cash flow and the overall financial picture."
    )
    positives: list[str] = Field(
        default_factory=list,
        description="Healthy patterns or positive observations supported by the data.",
    )
    needs_attention: list[str] = Field(
        default_factory=list,
        description="Spending patterns, fees, cash-flow issues, or risks that deserve attention.",
    )
    unusual_transactions: list[str] = Field(
        default_factory=list,
        description="Potentially unusual transactions. Never claim fraud; describe them as items to review.",
    )
    budget_actions: list[str] = Field(
        default_factory=list,
        description="Specific, realistic actions the user can take next month.",
    )
    monthly_observations: list[str] = Field(
        default_factory=list,
        description="Month-to-month trends when more than one month of data is present.",
    )
    savings_target: str = Field(
        description="A practical savings target or range based only on supplied cash-flow data."
    )
    disclaimer: str = Field(
        description="A short statement that this is educational budgeting analysis, not financial advice."
    )
