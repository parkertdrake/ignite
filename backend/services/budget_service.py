"""Budget logic — create, list, fetch, and activate.

Invariant: at most one budget is `active`. Activating a budget demotes
any other active budget to `inactive`. The first budget created (when
none is active yet) is auto-activated so the app always has a current
budget once one exists.
"""
from __future__ import annotations

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from persistence.models import (
    BUDGET_STATUS_ACTIVE,
    BUDGET_STATUS_INACTIVE,
    Budget,
    Category,
    Earning,
    Expense,
    Saving,
)
from services import expense_service, tax_service

MONTHS_PER_YEAR = 12


async def list_budgets(session: AsyncSession) -> list[Budget]:
    """All budgets, newest first."""
    result = await session.execute(
        select(Budget).order_by(Budget.created_at.desc(), Budget.id.desc())
    )
    return list(result.scalars().all())


async def get_budget(session: AsyncSession, budget_id: int) -> Budget | None:
    return await session.get(Budget, budget_id)


async def create_budget(session: AsyncSession, name: str) -> Budget:
    """Create a budget; auto-activate it if none is currently active."""
    active_exists = await session.execute(
        select(Budget.id).where(Budget.status == BUDGET_STATUS_ACTIVE).limit(1)
    )
    status = BUDGET_STATUS_INACTIVE if active_exists.first() else BUDGET_STATUS_ACTIVE
    budget = Budget(name=name, status=status)
    session.add(budget)
    await session.commit()
    await session.refresh(budget)
    return budget


async def monthly_income_by_budget(
    session: AsyncSession, budget_ids: list[int]
) -> dict[int, float]:
    """Monthly gross income (annual earnings / 12) keyed by budget id."""
    if not budget_ids:
        return {}
    result = await session.execute(
        select(Earning.budget_id, func.coalesce(func.sum(Earning.gross_annual), 0))
        .where(Earning.budget_id.in_(budget_ids))
        .group_by(Earning.budget_id)
    )
    return {budget_id: float(total) / MONTHS_PER_YEAR for budget_id, total in result.all()}


async def monthly_savings_by_budget(
    session: AsyncSession, budget_ids: list[int]
) -> dict[int, float]:
    """Monthly savings (annual contributions / 12) keyed by budget id."""
    if not budget_ids:
        return {}
    result = await session.execute(
        select(Saving.budget_id, func.coalesce(func.sum(Saving.amount_annual), 0))
        .where(Saving.budget_id.in_(budget_ids))
        .group_by(Saving.budget_id)
    )
    return {budget_id: float(total) / MONTHS_PER_YEAR for budget_id, total in result.all()}


def summary_from(
    monthly_income: float,
    savings: float = 0.0,
    taxes: float = 0.0,
    spending: float = 0.0,
) -> dict:
    """Assemble the monthly trickle-down summary. Panels fill in each line as
    they are built; net is the leftover after savings, taxes, and spending
    (target $0)."""
    return {
        "income": monthly_income,
        "savings": savings,
        "taxes": taxes,
        "spending": spending,
        "net": monthly_income - savings - taxes - spending,
    }


async def summaries_for(
    session: AsyncSession, budget_ids: list[int]
) -> dict[int, dict]:
    """Monthly summaries keyed by budget id (aggregates computed once)."""
    income = await monthly_income_by_budget(session, budget_ids)
    savings = await monthly_savings_by_budget(session, budget_ids)
    spending = await expense_service.monthly_spending_by_budget(session, budget_ids)
    taxes = {
        budget_id: (await tax_service.compute_for_budget(session, budget_id))["total_annual"]
        / MONTHS_PER_YEAR
        for budget_id in budget_ids
    }
    return {
        budget_id: summary_from(
            income.get(budget_id, 0.0),
            savings.get(budget_id, 0.0),
            taxes.get(budget_id, 0.0),
            spending.get(budget_id, 0.0),
        )
        for budget_id in budget_ids
    }


async def summarize(session: AsyncSession, budget_id: int) -> dict:
    """Monthly summary for a single budget."""
    return (await summaries_for(session, [budget_id]))[budget_id]


async def activate_budget(session: AsyncSession, budget_id: int) -> Budget | None:
    """Mark a budget active, demoting any other active budget. None if missing."""
    budget = await session.get(Budget, budget_id)
    if budget is None:
        return None
    await session.execute(
        update(Budget)
        .where(Budget.status == BUDGET_STATUS_ACTIVE, Budget.id != budget_id)
        .values(status=BUDGET_STATUS_INACTIVE)
    )
    budget.status = BUDGET_STATUS_ACTIVE
    await session.commit()
    await session.refresh(budget)
    return budget


async def set_tax_config(
    session: AsyncSession,
    budget_id: int,
    tax_year: int | None,
    state: str | None,
    filing_status: str | None,
    tax_override_monthly: float | None = None,
) -> Budget | None:
    """Update a budget's tax config (year / state / filing status / override).
    Only the provided fields change; state is cleared by passing an empty
    string. The override is entered per month and stored annualized."""
    budget = await session.get(Budget, budget_id)
    if budget is None:
        return None
    if tax_year is not None:
        budget.tax_year = tax_year
    if state is not None:
        budget.state = state or None
    if filing_status is not None:
        budget.filing_status = filing_status
    if tax_override_monthly is not None:
        budget.tax_override_annual = tax_override_monthly * MONTHS_PER_YEAR
    await session.commit()
    await session.refresh(budget)
    return budget


async def delete_budget(session: AsyncSession, budget_id: int) -> bool:
    """Delete a budget and its children. False if it does not exist.

    Children are removed explicitly rather than via FK cascade, since
    SQLite does not enforce ON DELETE CASCADE by default.
    """
    budget = await session.get(Budget, budget_id)
    if budget is None:
        return False
    await session.execute(delete(Earning).where(Earning.budget_id == budget_id))
    await session.execute(delete(Saving).where(Saving.budget_id == budget_id))
    await session.execute(delete(Expense).where(Expense.budget_id == budget_id))
    await session.execute(delete(Category).where(Category.budget_id == budget_id))
    await session.delete(budget)
    await session.commit()
    return True


async def clone_budget(
    session: AsyncSession, budget_id: int, new_name: str
) -> Budget | None:
    """Duplicate a budget (and its earnings) under a new name. The clone is
    created inactive so it never steals the active slot. None if missing."""
    source = await session.get(Budget, budget_id)
    if source is None:
        return None
    clone = Budget(
        name=new_name,
        status=BUDGET_STATUS_INACTIVE,
        tax_year=source.tax_year,
        state=source.state,
        filing_status=source.filing_status,
        tax_override_annual=source.tax_override_annual,
    )
    session.add(clone)
    await session.flush()  # assign clone.id before copying children

    source_earnings = await session.execute(
        select(Earning).where(Earning.budget_id == budget_id)
    )
    for earning in source_earnings.scalars().all():
        session.add(
            Earning(
                budget_id=clone.id,
                person=earning.person,
                gross_annual=earning.gross_annual,
            )
        )

    source_savings = await session.execute(
        select(Saving).where(Saving.budget_id == budget_id)
    )
    for saving in source_savings.scalars().all():
        session.add(
            Saving(
                budget_id=clone.id,
                person=saving.person,
                account=saving.account,
                amount_annual=saving.amount_annual,
                period=saving.period,
                pretax=saving.pretax,
            )
        )

    # Categories are per-budget: copy them, then remap expense category ids
    # onto the clone's fresh category rows.
    category_id_map: dict[int, int] = {}
    source_categories = await session.execute(
        select(Category).where(Category.budget_id == budget_id)
    )
    for category in source_categories.scalars().all():
        clone_category = Category(
            budget_id=clone.id, name=category.name, sort_order=category.sort_order
        )
        session.add(clone_category)
        await session.flush()
        category_id_map[category.id] = clone_category.id

    source_expenses = await session.execute(
        select(Expense).where(Expense.budget_id == budget_id)
    )
    for expense in source_expenses.scalars().all():
        session.add(
            Expense(
                budget_id=clone.id,
                item=expense.item,
                amount_annual=expense.amount_annual,
                period=expense.period,
                category_id=category_id_map.get(expense.category_id),
                payer_type=expense.payer_type,
                payer_person=expense.payer_person,
            )
        )
    await session.commit()
    await session.refresh(clone)
    return clone
