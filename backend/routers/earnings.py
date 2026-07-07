"""Earnings endpoints, nested under a budget.

  GET    /api/budgets/{budget_id}/earnings
  POST   /api/budgets/{budget_id}/earnings
  PATCH  /api/budgets/{budget_id}/earnings/{earning_id}
  DELETE /api/budgets/{budget_id}/earnings/{earning_id}
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_session
from schemas.earnings import EarningCreate, EarningOut, EarningUpdate
from services import budget_service, earning_service

router = APIRouter(prefix="/api/budgets/{budget_id}/earnings", tags=["earnings"])


async def _require_budget(session: AsyncSession, budget_id: int) -> None:
    if await budget_service.get_budget(session, budget_id) is None:
        raise HTTPException(status_code=404, detail="budget not found")


@router.get("", response_model=list[EarningOut])
async def list_earnings(
    budget_id: int, session: AsyncSession = Depends(get_session)
) -> list[EarningOut]:
    await _require_budget(session, budget_id)
    return await earning_service.list_earnings(session, budget_id)


@router.post("", response_model=EarningOut, status_code=201)
async def create_earning(
    budget_id: int,
    payload: EarningCreate,
    session: AsyncSession = Depends(get_session),
) -> EarningOut:
    await _require_budget(session, budget_id)
    return await earning_service.create_earning(
        session, budget_id, payload.person, payload.gross_annual
    )


@router.patch("/{earning_id}", response_model=EarningOut)
async def update_earning(
    budget_id: int,
    earning_id: int,
    payload: EarningUpdate,
    session: AsyncSession = Depends(get_session),
) -> EarningOut:
    earning = await earning_service.update_earning(
        session, budget_id, earning_id, payload.person, payload.gross_annual
    )
    if earning is None:
        raise HTTPException(status_code=404, detail="earning not found")
    return earning


@router.delete("/{earning_id}", status_code=204)
async def delete_earning(
    budget_id: int,
    earning_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    if not await earning_service.delete_earning(session, budget_id, earning_id):
        raise HTTPException(status_code=404, detail="earning not found")
