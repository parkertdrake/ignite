"""Category logic — per-budget spending categories, created inline."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from persistence.models import Category, Expense


async def list_categories(session: AsyncSession, budget_id: int) -> list[Category]:
    result = await session.execute(
        select(Category)
        .where(Category.budget_id == budget_id)
        .order_by(Category.sort_order, Category.name)
    )
    return list(result.scalars().all())


async def get_category(
    session: AsyncSession, budget_id: int, category_id: int
) -> Category | None:
    category = await session.get(Category, category_id)
    if category is None or category.budget_id != budget_id:
        return None
    return category


async def find_by_name(
    session: AsyncSession, budget_id: int, name: str
) -> Category | None:
    result = await session.execute(
        select(Category).where(Category.budget_id == budget_id, Category.name == name)
    )
    return result.scalar_one_or_none()


async def create_category(
    session: AsyncSession, budget_id: int, name: str
) -> Category:
    """Create a category, or return the existing one with the same name
    (idempotent so inline-add never trips the uniqueness constraint)."""
    existing = await find_by_name(session, budget_id, name)
    if existing is not None:
        return existing
    next_order = (
        await session.execute(
            select(func.coalesce(func.max(Category.sort_order), 0) + 1).where(
                Category.budget_id == budget_id
            )
        )
    ).scalar_one()
    category = Category(budget_id=budget_id, name=name, sort_order=next_order)
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category


async def delete_category(
    session: AsyncSession, budget_id: int, category_id: int
) -> bool:
    """Delete a category; expenses referencing it fall back to uncategorized
    (FK ON DELETE SET NULL)."""
    category = await get_category(session, budget_id, category_id)
    if category is None:
        return False
    await session.execute(
        Expense.__table__.update()
        .where(Expense.category_id == category_id)
        .values(category_id=None)
    )
    await session.delete(category)
    await session.commit()
    return True
