"""Earnings logic — per-person gross income rows within a budget."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from persistence.models import Earning


async def list_earnings(session: AsyncSession, budget_id: int) -> list[Earning]:
    result = await session.execute(
        select(Earning).where(Earning.budget_id == budget_id).order_by(Earning.id)
    )
    return list(result.scalars().all())


async def get_earning(
    session: AsyncSession, budget_id: int, earning_id: int
) -> Earning | None:
    earning = await session.get(Earning, earning_id)
    if earning is None or earning.budget_id != budget_id:
        return None
    return earning


async def create_earning(
    session: AsyncSession, budget_id: int, person: str, gross_annual: float
) -> Earning:
    earning = Earning(budget_id=budget_id, person=person, gross_annual=gross_annual)
    session.add(earning)
    await session.commit()
    await session.refresh(earning)
    return earning


async def update_earning(
    session: AsyncSession,
    budget_id: int,
    earning_id: int,
    person: str | None,
    gross_annual: float | None,
) -> Earning | None:
    earning = await get_earning(session, budget_id, earning_id)
    if earning is None:
        return None
    if person is not None:
        earning.person = person
    if gross_annual is not None:
        earning.gross_annual = gross_annual
    await session.commit()
    await session.refresh(earning)
    return earning


async def delete_earning(session: AsyncSession, budget_id: int, earning_id: int) -> bool:
    earning = await get_earning(session, budget_id, earning_id)
    if earning is None:
        return False
    await session.delete(earning)
    await session.commit()
    return True
