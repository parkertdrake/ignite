"""Request/response schemas for budget earnings."""
from pydantic import BaseModel, ConfigDict, Field


class EarningCreate(BaseModel):
    person: str = Field(min_length=1, max_length=120)
    gross_annual: float = Field(ge=0)


class EarningUpdate(BaseModel):
    person: str | None = Field(default=None, min_length=1, max_length=120)
    gross_annual: float | None = Field(default=None, ge=0)


class EarningOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    budget_id: int
    person: str
    gross_annual: float
