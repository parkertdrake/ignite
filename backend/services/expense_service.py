"""Expense logic — spending line items (item / amount / category / payer)."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from persistence.models import Expense


async def list_expenses(session: AsyncSession, budget_id: int) -> list[Expense]:
    result = await session.execute(
        select(Expense).where(Expense.budget_id == budget_id).order_by(Expense.id)
    )
    return list(result.scalars().all())


async def get_expense(
    session: AsyncSession, budget_id: int, expense_id: int
) -> Expense | None:
    expense = await session.get(Expense, expense_id)
    if expense is None or expense.budget_id != budget_id:
        return None
    return expense


async def create_expense(
    session: AsyncSession,
    budget_id: int,
    item: str,
    amount_annual: float,
    period: str,
    category_id: int | None,
    payer_type: str,
    payer_person: str | None,
) -> Expense:
    expense = Expense(
        budget_id=budget_id,
        item=item,
        amount_annual=amount_annual,
        period=period,
        category_id=category_id,
        payer_type=payer_type,
        payer_person=payer_person,
    )
    session.add(expense)
    await session.commit()
    await session.refresh(expense)
    return expense


async def update_expense(
    session: AsyncSession,
    budget_id: int,
    expense_id: int,
    item: str | None,
    amount_annual: float | None,
    period: str | None,
    category_id: int | None,
    clear_category: bool,
    payer_type: str | None,
    payer_person: str | None,
) -> Expense | None:
    expense = await get_expense(session, budget_id, expense_id)
    if expense is None:
        return None
    if item is not None:
        expense.item = item
    if amount_annual is not None:
        expense.amount_annual = amount_annual
    if period is not None:
        expense.period = period
    if clear_category:
        expense.category_id = None
    elif category_id is not None:
        expense.category_id = category_id
    if payer_type is not None:
        expense.payer_type = payer_type
        # An individual expense needs an owner; joint expenses never do.
        if payer_type != "individual":
            expense.payer_person = None
    if payer_person is not None:
        expense.payer_person = payer_person
    await session.commit()
    await session.refresh(expense)
    return expense


async def delete_expense(session: AsyncSession, budget_id: int, expense_id: int) -> bool:
    expense = await get_expense(session, budget_id, expense_id)
    if expense is None:
        return False
    await session.delete(expense)
    await session.commit()
    return True


async def monthly_spending_by_budget(
    session: AsyncSession, budget_ids: list[int]
) -> dict[int, float]:
    """Monthly spending (annual expenses / 12) keyed by budget id."""
    if not budget_ids:
        return {}
    result = await session.execute(
        select(Expense.budget_id, func.coalesce(func.sum(Expense.amount_annual), 0))
        .where(Expense.budget_id.in_(budget_ids))
        .group_by(Expense.budget_id)
    )
    return {budget_id: float(total) / 12 for budget_id, total in result.all()}
