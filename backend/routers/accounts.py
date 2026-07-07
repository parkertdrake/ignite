"""Accounts endpoint (stub — see services/accounts_service.py)."""
from fastapi import APIRouter

from schemas.accounts import AccountList
from services import accounts_service

router = APIRouter(prefix="/api")


@router.get("/accounts", response_model=AccountList)
def list_accounts() -> AccountList:
    """Stub endpoint — returns a placeholder account list."""
    return AccountList(accounts=accounts_service.list_accounts())
