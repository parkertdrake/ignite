"""Cash-flow model for a budget — nodes and links for a Sankey diagram.

All figures are monthly. Each earner's gross income pools into a single
`household` node, which then flows out to pre-tax savings, taxes, spending,
post-tax savings, and any unallocated remainder (`net`). Pre-tax savings is
emitted as its own outflow so the diagram shows the untaxed chunk leaving
the household (the "levers" story) without inventing a synthetic taxable
cash node.

When a budget is over-allocated (net < 0) a `deficit` inflow balances the
diagram so outflows never exceed inflows — a Sankey cannot represent a
negative link, so the shortfall is shown as money flowing *in*.

Node `tone` mirrors the frontend colour tokens (income/savings/taxes/
spending/net/deficit) so the chart obeys the trickle-down colour scheme.
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from persistence.models import Earning, Saving
from services import expense_service, tax_service

MONTHS_PER_YEAR = 12
HOUSEHOLD = "household"


async def _monthly_income_by_person(
    session: AsyncSession, budget_id: int
) -> list[tuple[str, float]]:
    """Monthly gross income per earner, ordered by name."""
    result = await session.execute(
        select(Earning.person, func.coalesce(func.sum(Earning.gross_annual), 0))
        .where(Earning.budget_id == budget_id)
        .group_by(Earning.person)
        .order_by(Earning.person)
    )
    return [(person, float(total) / MONTHS_PER_YEAR) for person, total in result.all()]


async def _monthly_savings_split(
    session: AsyncSession, budget_id: int
) -> tuple[float, float]:
    """(pre-tax, post-tax) monthly savings for a budget."""
    result = await session.execute(
        select(Saving.pretax, func.coalesce(func.sum(Saving.amount_annual), 0))
        .where(Saving.budget_id == budget_id)
        .group_by(Saving.pretax)
    )
    pretax = 0.0
    posttax = 0.0
    for is_pretax, total in result.all():
        monthly = float(total) / MONTHS_PER_YEAR
        if is_pretax:
            pretax = monthly
        else:
            posttax = monthly
    return pretax, posttax


async def build_flow(session: AsyncSession, budget_id: int) -> dict:
    """Sankey nodes + links (monthly $) for a budget's trickle-down cash flow."""
    per_person = await _monthly_income_by_person(session, budget_id)
    pretax_savings, posttax_savings = await _monthly_savings_split(session, budget_id)
    taxes = (
        await tax_service.compute_for_budget(session, budget_id)
    )["total_annual"] / MONTHS_PER_YEAR
    spending = (
        await expense_service.monthly_spending_by_budget(session, [budget_id])
    ).get(budget_id, 0.0)

    total_income = sum(amount for _, amount in per_person)
    net = total_income - pretax_savings - posttax_savings - taxes - spending

    nodes: list[dict] = []
    links: list[dict] = []

    for person, amount in per_person:
        node_id = f"person:{person}"
        nodes.append({"id": node_id, "label": person, "tone": "income"})
        if amount > 0:
            links.append({"source": node_id, "target": HOUSEHOLD, "value": amount})

    # Whole-dollar display, so treat sub-dollar remainders as balanced ($0)
    # rather than emitting a stray Unallocated/Deficit node from float dust.
    over_allocated = net < -0.5

    if per_person or over_allocated:
        nodes.append({"id": HOUSEHOLD, "label": "Household", "tone": "income"})

    outflows = [
        ("pretax_savings", "Pre-tax Savings", "savings", pretax_savings),
        ("taxes", "Taxes", "taxes", taxes),
        ("spending", "Spending", "spending", spending),
        ("posttax_savings", "Post-tax Savings", "savings", posttax_savings),
    ]
    if net > 0.5:
        outflows.append(("net", "Unallocated", "net", net))

    for node_id, label, tone, value in outflows:
        if value > 0:
            nodes.append({"id": node_id, "label": label, "tone": tone})
            links.append({"source": HOUSEHOLD, "target": node_id, "value": value})

    if over_allocated:
        nodes.append({"id": "deficit", "label": "Deficit", "tone": "deficit"})
        links.append({"source": "deficit", "target": HOUSEHOLD, "value": -net})

    return {"nodes": nodes, "links": links}
