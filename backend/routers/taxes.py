"""Tax endpoints (thin adapter over services/tax_service.py).

  GET /api/tax-config/options        dropdown choices (years, states)
  GET /api/budgets/{id}/taxes        computed annual tax breakdown

Setting a budget's tax config lives on the budgets router
(PATCH /api/budgets/{id}/tax-config) so it can return the refreshed summary.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_session
from schemas.taxes import TaxBreakdown, TaxConfigOptions
from services import budget_service, tax_service

router = APIRouter(prefix="/api", tags=["taxes"])


@router.get("/tax-config/options", response_model=TaxConfigOptions)
async def tax_config_options(
    session: AsyncSession = Depends(get_session),
) -> TaxConfigOptions:
    return TaxConfigOptions(
        years=await tax_service.available_years(session),
        states=await tax_service.available_states(session),
    )


@router.get("/budgets/{budget_id}/taxes", response_model=TaxBreakdown)
async def get_taxes(
    budget_id: int, session: AsyncSession = Depends(get_session)
) -> TaxBreakdown:
    if await budget_service.get_budget(session, budget_id) is None:
        raise HTTPException(status_code=404, detail="budget not found")
    return TaxBreakdown(**await tax_service.compute_for_budget(session, budget_id))
