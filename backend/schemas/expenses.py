"""Request/response schemas for budget expenses."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ExpensePeriod = Literal["monthly", "yearly"]
PayerType = Literal["individual", "joint_fixed", "joint_variable"]


class ExpenseCreate(BaseModel):
    item: str = Field(min_length=1, max_length=200)
    amount_annual: float = Field(ge=0)
    period: ExpensePeriod = "yearly"
    category_id: int | None = None
    payer_type: PayerType = "joint_variable"
    payer_person: str | None = Field(default=None, max_length=120)


class ExpenseUpdate(BaseModel):
    item: str | None = Field(default=None, min_length=1, max_length=200)
    amount_annual: float | None = Field(default=None, ge=0)
    period: ExpensePeriod | None = None
    # category_id is nullable; use the sentinel below to distinguish "not
    # provided" from "clear the category".
    category_id: int | None = None
    clear_category: bool = False
    payer_type: PayerType | None = None
    payer_person: str | None = Field(default=None, max_length=120)


class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    budget_id: int
    item: str
    amount_annual: float
    period: ExpensePeriod
    category_id: int | None
    payer_type: PayerType
    payer_person: str | None
