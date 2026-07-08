"""Savings endpoints, nested under a budget.

  GET    /api/budgets/{budget_id}/savings[?pretax=true|false]
  POST   /api/budgets/{budget_id}/savings
  PATCH  /api/budgets/{budget_id}/savings/{saving_id}
  DELETE /api/budgets/{budget_id}/savings/{saving_id}
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_session
from schemas.savings import SavingCreate, SavingOut, SavingUpdate
from services import budget_service, saving_service

router = APIRouter(prefix="/api/budgets/{budget_id}/savings", tags=["savings"])


async def _require_budget(session: AsyncSession, budget_id: int) -> None:
    if await budget_service.get_budget(session, budget_id) is None:
        raise HTTPException(status_code=404, detail="budget not found")


@router.get("", response_model=list[SavingOut])
async def list_savings(
    budget_id: int,
    pretax: bool | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[SavingOut]:
    await _require_budget(session, budget_id)
    return await saving_service.list_savings(session, budget_id, pretax)


@router.post("", response_model=SavingOut, status_code=201)
async def create_saving(
    budget_id: int,
    payload: SavingCreate,
    session: AsyncSession = Depends(get_session),
) -> SavingOut:
    await _require_budget(session, budget_id)
    return await saving_service.create_saving(
        session,
        budget_id,
        payload.person,
        payload.account,
        payload.amount_annual,
        payload.period,
        payload.pretax,
    )


@router.patch("/{saving_id}", response_model=SavingOut)
async def update_saving(
    budget_id: int,
    saving_id: int,
    payload: SavingUpdate,
    session: AsyncSession = Depends(get_session),
) -> SavingOut:
    saving = await saving_service.update_saving(
        session,
        budget_id,
        saving_id,
        payload.person,
        payload.account,
        payload.amount_annual,
        payload.period,
    )
    if saving is None:
        raise HTTPException(status_code=404, detail="saving not found")
    return saving


@router.delete("/{saving_id}", status_code=204)
async def delete_saving(
    budget_id: int,
    saving_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    if not await saving_service.delete_saving(session, budget_id, saving_id):
        raise HTTPException(status_code=404, detail="saving not found")
