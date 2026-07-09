"""Expense endpoints, nested under a budget.

  GET    /api/budgets/{budget_id}/expenses
  POST   /api/budgets/{budget_id}/expenses
  PATCH  /api/budgets/{budget_id}/expenses/{expense_id}
  DELETE /api/budgets/{budget_id}/expenses/{expense_id}
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_session
from schemas.expenses import ExpenseCreate, ExpenseOut, ExpenseUpdate
from services import budget_service, expense_service

router = APIRouter(prefix="/api/budgets/{budget_id}/expenses", tags=["expenses"])


async def _require_budget(session: AsyncSession, budget_id: int) -> None:
    if await budget_service.get_budget(session, budget_id) is None:
        raise HTTPException(status_code=404, detail="budget not found")


@router.get("", response_model=list[ExpenseOut])
async def list_expenses(
    budget_id: int, session: AsyncSession = Depends(get_session)
) -> list[ExpenseOut]:
    await _require_budget(session, budget_id)
    return await expense_service.list_expenses(session, budget_id)


@router.post("", response_model=ExpenseOut, status_code=201)
async def create_expense(
    budget_id: int,
    payload: ExpenseCreate,
    session: AsyncSession = Depends(get_session),
) -> ExpenseOut:
    await _require_budget(session, budget_id)
    return await expense_service.create_expense(
        session,
        budget_id,
        payload.item,
        payload.amount_annual,
        payload.period,
        payload.category_id,
        payload.payer_type,
        payload.payer_person,
    )


@router.patch("/{expense_id}", response_model=ExpenseOut)
async def update_expense(
    budget_id: int,
    expense_id: int,
    payload: ExpenseUpdate,
    session: AsyncSession = Depends(get_session),
) -> ExpenseOut:
    expense = await expense_service.update_expense(
        session,
        budget_id,
        expense_id,
        payload.item,
        payload.amount_annual,
        payload.period,
        payload.category_id,
        payload.clear_category,
        payload.payer_type,
        payload.payer_person,
    )
    if expense is None:
        raise HTTPException(status_code=404, detail="expense not found")
    return expense


@router.delete("/{expense_id}", status_code=204)
async def delete_expense(
    budget_id: int, expense_id: int, session: AsyncSession = Depends(get_session)
) -> None:
    if not await expense_service.delete_expense(session, budget_id, expense_id):
        raise HTTPException(status_code=404, detail="expense not found")
