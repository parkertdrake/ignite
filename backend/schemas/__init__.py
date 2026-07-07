"""Pydantic request/response schemas — the typed HTTP contract.

These shapes drive FastAPI's OpenAPI document, which the frontend
generates its typed client from, so the contract can't drift across the
language boundary.
"""
