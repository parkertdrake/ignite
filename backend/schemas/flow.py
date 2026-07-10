"""Response schemas for the budget cash-flow (Sankey) endpoint."""
from pydantic import BaseModel


class FlowNode(BaseModel):
    id: str
    label: str
    tone: str


class FlowLink(BaseModel):
    source: str
    target: str
    value: float


class BudgetFlow(BaseModel):
    nodes: list[FlowNode]
    links: list[FlowLink]
