# ignite

Personal finance web application.

## Structure

- `frontend/` — React + Vite SPA (TypeScript, vitest).
- `backend/` — FastAPI stub (Python 3.12, pytest).
- `deployment/` — Helm chart, Concourse CI, secrets bootstrap.

## Local development

```sh
# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python main.py          # serves on :8000

# frontend (separate shell)
cd frontend
npm install             # also generates package-lock.json (needed by CI)
npm run dev             # serves on :5173, proxies /api → :8000
```

## Deployment

Push to `main` → Concourse builds images + chart to Harbor → the
home-kubernetes `deploy-ignite` job rolls it out to
https://finance.cluster.brindledev.com. See `deployment/README.md`.