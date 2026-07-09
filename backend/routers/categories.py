"""Category endpoints, nested under a budget.

  GET    /api/budgets/{budget_id}/categories
  POST   /api/budgets/{budget_id}/categories        (inline create)
  DELETE /api/budgets/{budget_id}/categories/{id}   (expenses fall back to uncategorized)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_session
from schemas.categories import CategoryCreate, CategoryOut
from services import budget_service, category_service

router = APIRouter(prefix="/api/budgets/{budget_id}/categories", tags=["categories"])


async def _require_budget(session: AsyncSession, budget_id: int) -> None:
    if await budget_service.get_budget(session, budget_id) is None:
        raise HTTPException(status_code=404, detail="budget not found")


@router.get("", response_model=list[CategoryOut])
async def list_categories(
    budget_id: int, session: AsyncSession = Depends(get_session)
) -> list[CategoryOut]:
    await _require_budget(session, budget_id)
    return await category_service.list_categories(session, budget_id)


@router.post("", response_model=CategoryOut, status_code=201)
async def create_category(
    budget_id: int,
    payload: CategoryCreate,
    session: AsyncSession = Depends(get_session),
) -> CategoryOut:
    await _require_budget(session, budget_id)
    return await category_service.create_category(session, budget_id, payload.name.strip())


@router.delete("/{category_id}", status_code=204)
async def delete_category(
    budget_id: int, category_id: int, session: AsyncSession = Depends(get_session)
) -> None:
    if not await category_service.delete_category(session, budget_id, category_id):
        raise HTTPException(status_code=404, detail="category not found")
