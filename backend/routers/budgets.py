"""Budget endpoints (thin adapter over services/budget_service.py).

  GET  /api/budgets                list budgets (newest first)
  POST /api/budgets                create a budget
  GET  /api/budgets/{id}           fetch one
  POST /api/budgets/{id}/activate  mark as the current budget
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_session
from schemas.budgets import BudgetCreate, BudgetOut
from services import budget_service

router = APIRouter(prefix="/api/budgets", tags=["budgets"])


@router.get("", response_model=list[BudgetOut])
async def list_budgets(session: AsyncSession = Depends(get_session)) -> list[BudgetOut]:
    return await budget_service.list_budgets(session)


@router.post("", response_model=BudgetOut, status_code=201)
async def create_budget(
    payload: BudgetCreate, session: AsyncSession = Depends(get_session)
) -> BudgetOut:
    return await budget_service.create_budget(session, payload.name)


@router.get("/{budget_id}", response_model=BudgetOut)
async def get_budget(
    budget_id: int, session: AsyncSession = Depends(get_session)
) -> BudgetOut:
    budget = await budget_service.get_budget(session, budget_id)
    if budget is None:
        raise HTTPException(status_code=404, detail="budget not found")
    return budget


@router.post("/{budget_id}/activate", response_model=BudgetOut)
async def activate_budget(
    budget_id: int, session: AsyncSession = Depends(get_session)
) -> BudgetOut:
    budget = await budget_service.activate_budget(session, budget_id)
    if budget is None:
        raise HTTPException(status_code=404, detail="budget not found")
    return budget
