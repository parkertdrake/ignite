"""Request/response schemas for budgets."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BudgetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class BudgetSummary(BaseModel):
    """Monthly roll-up across the trickle-down flow (all figures per month).

    Populated panel by panel; spending stays 0 until that panel exists.
    `net` = income - savings - taxes - spending (target $0)."""

    income: float
    savings: float
    taxes: float
    spending: float
    net: float


class BudgetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    status: str
    created_at: datetime
    tax_year: int | None = None
    state: str | None = None
    filing_status: str
    summary: BudgetSummary
