"""Request/response schemas for budget savings."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SavingPeriod = Literal["monthly", "yearly"]


class SavingCreate(BaseModel):
    person: str = Field(min_length=1, max_length=120)
    account: str = Field(min_length=1, max_length=120)
    amount_annual: float = Field(ge=0)
    period: SavingPeriod = "yearly"
    pretax: bool


class SavingUpdate(BaseModel):
    person: str | None = Field(default=None, min_length=1, max_length=120)
    account: str | None = Field(default=None, min_length=1, max_length=120)
    amount_annual: float | None = Field(default=None, ge=0)
    period: SavingPeriod | None = None


class SavingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    budget_id: int
    person: str
    account: str
    amount_annual: float
    period: SavingPeriod
    pretax: bool
