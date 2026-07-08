"""Request/response schemas for the computed Taxes panel."""
from pydantic import BaseModel, ConfigDict, Field


class TaxBreakdown(BaseModel):
    """Annual household tax breakdown. The frontend divides by 12 for the
    monthly trickle-down and shows the line items + effective rate."""

    model_config = ConfigDict(from_attributes=True)

    year: int | None
    state: str | None
    filing_status: str
    gross: float
    pretax_deductions: float
    federal_taxable: float
    state_taxable: float
    federal_income: float
    social_security: float
    medicare: float
    state_income: float
    total_annual: float
    effective_rate: float


class TaxConfigOptions(BaseModel):
    """Dropdown choices sourced from the seeded reference data."""

    years: list[int]
    states: list[str]


class TaxConfigUpdate(BaseModel):
    tax_year: int | None = None
    # Empty string clears the state (federal-only); a code selects a state.
    state: str | None = Field(default=None, max_length=2)
    filing_status: str | None = Field(default=None, max_length=10)
