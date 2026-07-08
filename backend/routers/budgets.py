"""Budget endpoints (thin adapter over services/budget_service.py).

  GET  /api/budgets                list budgets (newest first)
  POST /api/budgets                create a budget
  GET  /api/budgets/{id}           fetch one
  POST /api/budgets/{id}/activate  mark as the current budget

Each response embeds a monthly `summary` (income/savings/spending/net).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_session
from persistence.models import Budget
from schemas.budgets import BudgetCreate, BudgetOut, BudgetSummary
from schemas.taxes import TaxConfigUpdate
from services import budget_service

router = APIRouter(prefix="/api/budgets", tags=["budgets"])


def _to_out(budget: Budget, summary: dict) -> BudgetOut:
    return BudgetOut(
        id=budget.id,
        name=budget.name,
        status=budget.status,
        created_at=budget.created_at,
        tax_year=budget.tax_year,
        state=budget.state,
        filing_status=budget.filing_status,
        summary=BudgetSummary(**summary),
    )


@router.get("", response_model=list[BudgetOut])
async def list_budgets(session: AsyncSession = Depends(get_session)) -> list[BudgetOut]:
    budgets = await budget_service.list_budgets(session)
    summaries = await budget_service.summaries_for(session, [budget.id for budget in budgets])
    return [_to_out(budget, summaries[budget.id]) for budget in budgets]


@router.post("", response_model=BudgetOut, status_code=201)
async def create_budget(
    payload: BudgetCreate, session: AsyncSession = Depends(get_session)
) -> BudgetOut:
    budget = await budget_service.create_budget(session, payload.name)
    return _to_out(budget, await budget_service.summarize(session, budget.id))


@router.get("/{budget_id}", response_model=BudgetOut)
async def get_budget(
    budget_id: int, session: AsyncSession = Depends(get_session)
) -> BudgetOut:
    budget = await budget_service.get_budget(session, budget_id)
    if budget is None:
        raise HTTPException(status_code=404, detail="budget not found")
    return _to_out(budget, await budget_service.summarize(session, budget.id))


@router.post("/{budget_id}/activate", response_model=BudgetOut)
async def activate_budget(
    budget_id: int, session: AsyncSession = Depends(get_session)
) -> BudgetOut:
    budget = await budget_service.activate_budget(session, budget_id)
    if budget is None:
        raise HTTPException(status_code=404, detail="budget not found")
    return _to_out(budget, await budget_service.summarize(session, budget.id))


@router.post("/{budget_id}/copy", response_model=BudgetOut, status_code=201)
async def copy_budget(
    budget_id: int,
    payload: BudgetCreate,
    session: AsyncSession = Depends(get_session),
) -> BudgetOut:
    clone = await budget_service.clone_budget(session, budget_id, payload.name)
    if clone is None:
        raise HTTPException(status_code=404, detail="budget not found")
    return _to_out(clone, await budget_service.summarize(session, clone.id))


@router.patch("/{budget_id}/tax-config", response_model=BudgetOut)
async def update_tax_config(
    budget_id: int,
    payload: TaxConfigUpdate,
    session: AsyncSession = Depends(get_session),
) -> BudgetOut:
    budget = await budget_service.set_tax_config(
        session, budget_id, payload.tax_year, payload.state, payload.filing_status
    )
    if budget is None:
        raise HTTPException(status_code=404, detail="budget not found")
    return _to_out(budget, await budget_service.summarize(session, budget.id))


@router.delete("/{budget_id}", status_code=204)
async def delete_budget(
    budget_id: int, session: AsyncSession = Depends(get_session)
) -> None:
    if not await budget_service.delete_budget(session, budget_id):
        raise HTTPException(status_code=404, detail="budget not found")
