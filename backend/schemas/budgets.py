"""Request/response schemas for budgets."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BudgetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class BudgetSummary(BaseModel):
    """Monthly roll-up across the trickle-down flow (all figures per month).

    Populated panel by panel; savings/spending stay 0 until those panels
    exist. `net` = income - savings - spending (taxes fold in with M1 #6).
    """

    income: float
    savings: float
    spending: float
    net: float


class BudgetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    status: str
    created_at: datetime
    summary: BudgetSummary
