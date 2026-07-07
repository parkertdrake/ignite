"""Budget logic — create, list, fetch, and activate.

Invariant: at most one budget is `active`. Activating a budget demotes
any other active budget to `inactive`. The first budget created (when
none is active yet) is auto-activated so the app always has a current
budget once one exists.
"""
from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from persistence.models import (
    BUDGET_STATUS_ACTIVE,
    BUDGET_STATUS_INACTIVE,
    Budget,
)


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
