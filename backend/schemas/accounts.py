"""Response schemas for the (stub) accounts endpoint."""
from pydantic import BaseModel


class Account(BaseModel):
    id: int
    name: str
    balance: float


class AccountList(BaseModel):
    accounts: list[Account]
