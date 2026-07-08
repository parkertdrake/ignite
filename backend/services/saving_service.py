"""Savings logic — per-person, per-account monthly contributions.

`pretax` distinguishes pre-tax (401k/HSA) from post-tax savings; both
live in one table and are filtered per panel.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from persistence.models import Saving


async def list_savings(
    session: AsyncSession, budget_id: int, pretax: bool | None = None
) -> list[Saving]:
    query = select(Saving).where(Saving.budget_id == budget_id)
    if pretax is not None:
        query = query.where(Saving.pretax == pretax)
    result = await session.execute(query.order_by(Saving.id))
    return list(result.scalars().all())


async def get_saving(
    session: AsyncSession, budget_id: int, saving_id: int
) -> Saving | None:
    saving = await session.get(Saving, saving_id)
    if saving is None or saving.budget_id != budget_id:
        return None
    return saving


async def create_saving(
    session: AsyncSession,
    budget_id: int,
    person: str,
    account: str,
    amount_annual: float,
    period: str,
    pretax: bool,
) -> Saving:
    saving = Saving(
        budget_id=budget_id,
        person=person,
        account=account,
        amount_annual=amount_annual,
        period=period,
        pretax=pretax,
    )
    session.add(saving)
    await session.commit()
    await session.refresh(saving)
    return saving


async def update_saving(
    session: AsyncSession,
    budget_id: int,
    saving_id: int,
    person: str | None,
    account: str | None,
    amount_annual: float | None,
    period: str | None,
) -> Saving | None:
    saving = await get_saving(session, budget_id, saving_id)
    if saving is None:
        return None
    if person is not None:
        saving.person = person
    if account is not None:
        saving.account = account
    if amount_annual is not None:
        saving.amount_annual = amount_annual
    if period is not None:
        saving.period = period
    await session.commit()
    await session.refresh(saving)
    return saving


async def delete_saving(session: AsyncSession, budget_id: int, saving_id: int) -> bool:
    saving = await get_saving(session, budget_id, saving_id)
    if saving is None:
        return False
    await session.delete(saving)
    await session.commit()
    return True
