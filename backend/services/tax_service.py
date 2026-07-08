"""Tax engine — computes household taxes from income and pre-tax savings.

Household-aggregated (not per-person): federal income tax on combined
taxable income (gross − pre-tax deductions − standard deduction) using
progressive MFJ brackets, FICA (Social Security + Medicare) per earner, and
optional state income tax. Pure functions do the math; the async helpers
load the seeded reference data (see migration 0006).

Assumptions (v1, documented on purpose):
- Filing status is MFJ; brackets are joint, so no per-person allocation.
- FICA is levied on gross wages — pre-tax 401(k)/HSA do NOT reduce the FICA
  base (true for 401(k); slightly conservative for payroll HSA).
- State taxable income reuses the federal pre-tax treatment (state conformity
  to 401(k)/HSA varies — revisit per state if it matters).
"""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from persistence.models import (
    FILING_MFJ,
    JURISDICTION_FEDERAL,
    Earning,
    Saving,
    TaxBracket,
    TaxParams,
)


def progressive_tax(taxable: float, brackets: list[tuple[float, float]]) -> float:
    """Tax on `taxable` given brackets as (lower_bound, rate) sorted ascending.
    Each bracket's rate applies to income between its floor and the next
    bracket's floor. Empty brackets → 0 (a no-income-tax jurisdiction)."""
    if taxable <= 0 or not brackets:
        return 0.0
    ordered = sorted(brackets, key=lambda bracket: bracket[0])
    total = 0.0
    for index, (lower, rate) in enumerate(ordered):
        if taxable <= lower:
            break
        upper = ordered[index + 1][0] if index + 1 < len(ordered) else float("inf")
        total += (min(taxable, upper) - lower) * rate
    return total


def fica_tax(gross_by_person: list[float], params: TaxParams) -> tuple[float, float]:
    """(social_security, medicare) across all earners. SS caps at the wage
    base per person; the additional Medicare rate applies to combined wages
    above the MFJ threshold."""
    if params.ss_wage_base is None:
        return 0.0, 0.0
    wage_base = float(params.ss_wage_base)
    ss_rate = float(params.ss_rate or 0)
    social_security = sum(min(gross, wage_base) * ss_rate for gross in gross_by_person)

    total_wages = sum(gross_by_person)
    medicare_rate = float(params.medicare_rate or 0)
    addl_rate = float(params.medicare_addl_rate or 0)
    addl_threshold = float(params.medicare_addl_threshold or 0)
    medicare = total_wages * medicare_rate + max(0.0, total_wages - addl_threshold) * addl_rate
    return social_security, medicare


async def latest_year(session: AsyncSession) -> int | None:
    """Newest seeded federal tax year, or None if nothing is seeded."""
    result = await session.execute(
        select(func.max(TaxParams.year)).where(
            TaxParams.jurisdiction == JURISDICTION_FEDERAL
        )
    )
    return result.scalar_one_or_none()


async def available_years(session: AsyncSession) -> list[int]:
    result = await session.execute(
        select(TaxParams.year)
        .where(TaxParams.jurisdiction == JURISDICTION_FEDERAL)
        .distinct()
        .order_by(TaxParams.year.desc())
    )
    return list(result.scalars().all())


async def available_states(session: AsyncSession) -> list[str]:
    """State jurisdiction codes that have seeded params (any year)."""
    result = await session.execute(
        select(TaxParams.jurisdiction)
        .where(TaxParams.jurisdiction != JURISDICTION_FEDERAL)
        .distinct()
        .order_by(TaxParams.jurisdiction)
    )
    return list(result.scalars().all())


async def _load_params(
    session: AsyncSession, year: int, jurisdiction: str, filing_status: str
) -> TaxParams | None:
    result = await session.execute(
        select(TaxParams).where(
            TaxParams.year == year,
            TaxParams.jurisdiction == jurisdiction,
            TaxParams.filing_status == filing_status,
        )
    )
    return result.scalar_one_or_none()


async def _load_brackets(
    session: AsyncSession, year: int, jurisdiction: str, filing_status: str
) -> list[tuple[float, float]]:
    result = await session.execute(
        select(TaxBracket.lower_bound, TaxBracket.rate)
        .where(
            TaxBracket.year == year,
            TaxBracket.jurisdiction == jurisdiction,
            TaxBracket.filing_status == filing_status,
        )
        .order_by(TaxBracket.lower_bound)
    )
    return [(float(lower), float(rate)) for lower, rate in result.all()]


def _to_float(value: Decimal | float | None) -> float:
    return float(value) if value is not None else 0.0


async def compute_for_budget(session: AsyncSession, budget_id: int) -> dict:
    """Annual household tax breakdown for a budget. Returns zeros (with the
    resolved config) when there is no income or no seeded tax year."""
    earnings = (
        await session.execute(select(Earning).where(Earning.budget_id == budget_id))
    ).scalars().all()
    gross_by_person = [float(earning.gross_annual) for earning in earnings]
    total_gross = sum(gross_by_person)

    pretax_total = float(
        (
            await session.execute(
                select(func.coalesce(func.sum(Saving.amount_annual), 0)).where(
                    Saving.budget_id == budget_id, Saving.pretax.is_(True)
                )
            )
        ).scalar_one()
    )

    budget = await _load_budget_config(session, budget_id)
    filing_status = budget["filing_status"] or FILING_MFJ
    year = budget["tax_year"] or await latest_year(session)
    state = budget["state"]

    empty = _empty_breakdown(year, state, filing_status, total_gross)
    if year is None:
        return empty

    federal_params = await _load_params(session, year, JURISDICTION_FEDERAL, filing_status)
    if federal_params is None:
        return empty

    federal_deduction = _to_float(federal_params.standard_deduction)
    federal_taxable = max(0.0, total_gross - pretax_total - federal_deduction)
    federal_brackets = await _load_brackets(
        session, year, JURISDICTION_FEDERAL, filing_status
    )
    federal_income = progressive_tax(federal_taxable, federal_brackets)
    social_security, medicare = fica_tax(gross_by_person, federal_params)

    state_income = 0.0
    state_taxable = 0.0
    if state:
        state_params = await _load_params(session, year, state, filing_status)
        if state_params is not None:
            num_earners = len(gross_by_person)
            state_deduction = _to_float(state_params.standard_deduction) + _to_float(
                state_params.personal_exemption
            ) * num_earners
            state_taxable = max(0.0, total_gross - pretax_total - state_deduction)
            state_brackets = await _load_brackets(session, year, state, filing_status)
            state_income = progressive_tax(state_taxable, state_brackets)

    total = federal_income + social_security + medicare + state_income
    return {
        "year": year,
        "state": state,
        "filing_status": filing_status,
        "gross": total_gross,
        "pretax_deductions": pretax_total,
        "federal_taxable": federal_taxable,
        "state_taxable": state_taxable,
        "federal_income": federal_income,
        "social_security": social_security,
        "medicare": medicare,
        "state_income": state_income,
        "total_annual": total,
        "effective_rate": (total / total_gross) if total_gross else 0.0,
    }


async def _load_budget_config(session: AsyncSession, budget_id: int) -> dict:
    from persistence.models import Budget

    budget = await session.get(Budget, budget_id)
    if budget is None:
        return {"tax_year": None, "state": None, "filing_status": FILING_MFJ}
    return {
        "tax_year": budget.tax_year,
        "state": budget.state,
        "filing_status": budget.filing_status,
    }


def _empty_breakdown(
    year: int | None, state: str | None, filing_status: str, gross: float
) -> dict:
    return {
        "year": year,
        "state": state,
        "filing_status": filing_status,
        "gross": gross,
        "pretax_deductions": 0.0,
        "federal_taxable": 0.0,
        "state_taxable": 0.0,
        "federal_income": 0.0,
        "social_security": 0.0,
        "medicare": 0.0,
        "state_income": 0.0,
        "total_annual": 0.0,
        "effective_rate": 0.0,
    }
