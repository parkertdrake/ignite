"""Service layer — all business logic lives here.

Services take their inputs explicitly (an AsyncSession, typed args) and
return typed results, with no HTTP concerns. Routers are thin adapters
over these functions; a future MCP server wraps the same services
directly (Cross-cutting #18).
"""
