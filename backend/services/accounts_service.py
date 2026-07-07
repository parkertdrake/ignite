"""Accounts logic — stub until the Account model lands (M3 #14).

Deliberately session-free for now: there is no Account table yet, so
this route does not depend on `get_session` and keeps working in local
dev without a database.
"""
from __future__ import annotations


def list_accounts() -> list[dict]:
    """Return placeholder accounts until real persistence exists."""
    return [
        {"id": 1, "name": "Checking", "balance": 0.0},
        {"id": 2, "name": "Savings", "balance": 0.0},
    ]
