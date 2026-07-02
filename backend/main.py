"""Ignite backend — FastAPI stub for the personal finance app.

Serves a liveness endpoint at /health (hit directly on the pod by the
Kubernetes readiness probe) and the public API under /api, which the
ingress HTTPRoute routes to this service. The frontend calls /api/*
through the same host, so everything user-facing lives under that prefix.
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Ignite", version="0.1.0")

# Dev-only convenience: the Vite dev server runs on a different origin
# than the API. In-cluster both are served from the same host via the
# ingress, so this is a no-op there.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    """Liveness/readiness probe target. Hit directly on the pod."""
    return {"status": "ok"}


@app.get("/api/health")
def api_health():
    """Same check, reachable through the ingress /api prefix."""
    return {"status": "ok", "service": "ignite-backend"}


@app.get("/api/accounts")
def list_accounts():
    """Stub endpoint — returns a placeholder account list."""
    return {
        "accounts": [
            {"id": 1, "name": "Checking", "balance": 0.0},
            {"id": 2, "name": "Savings", "balance": 0.0},
        ]
    }


def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
