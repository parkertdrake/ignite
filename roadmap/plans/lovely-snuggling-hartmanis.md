# Ignite — Broad-Stroke Roadmap & Issue Set

## Context

Ignite is a personal-finance app for a two-person (generalizing to N-person) household.
Today it is a clean, fully-wired **scaffold with zero domain logic**: FastAPI +
async SQLAlchemy + Alembic harness + bundled Postgres + Helm + Concourse CI are all
working, but there are **no models, no tables, and all three pages render `$0`
placeholders**. There is no frontend API client, no react-query, no shared types.

This document sets the broad-stroke direction for the three screens — **Budget → FIRE
→ Investments**, built in that order — plus the shared foundation they all need, and
enumerates the exact Gitea issues to create in `parkertdrake/ignite` (repo id 18).

### Decisions locked (this session)

- **People:** household of **N members** (not hardcoded 2). People are shared across screens.
- **Accounts:** Budget savings-goal destinations and Investments accounts stay **separate for
  now** — build screens in isolation; unify the data model later.
- **Taxes:** **computed** from gross income minus pre-tax deductions (its own engine).
- **Division strategies:** Manual %, Income-proportional, and **"Levers"** (tax-advantaged
  optimization — see below). Per-expense override deferred.
- **FIRE engine:** **Monte Carlo**.
- **Ingestion:** **deferred** R&D — leading idea is AI-powered PDF statement parsing.
- **Frontend data layer:** **@tanstack/react-query + a typed API client** (OpenAPI-generated
  from FastAPI so contracts can't drift). Backend owns all data + math; frontend renders.
- **MCP/agentic:** **deferred**, but design the backend **service layer** so an MCP server
  can wrap it cleanly later.

### The "Levers" concept (why division isn't just income-proportional)

Parker has work-provided tax-advantaged buckets (401k, HSA, ESPP, Backdoor Roth) the
partner lacks. Household after-tax wealth is maximized by funneling Parker's income into
those pre-tax buckets while the partner covers a larger share of living expenses to
compensate. So the division % is a **tuned lever**, and ultimately an **optimization
problem** (maximize tax-advantaged savings subject to expenses staying covered). v1 is a
manual lever with this reasoning documented; a solver can come later.

## Architecture principles

1. **Backend owns data + math.** All computation (splits, rollups, tax, Monte Carlo) lives
   in pure, unit-tested service functions — never in the frontend.
2. **Service layer separate from routers.** Routers are thin HTTP adapters over a
   `services/` layer. This is what an MCP server will later wrap. (Currently everything is
   in `backend/main.py` — must be split.)
3. **Typed contract end-to-end.** Pydantic schemas → OpenAPI → generated TS client. No
   hand-duplicated types across the language boundary.
4. **Migrations for every model change.** `alembic revision --autogenerate` (no migrations
   exist yet — Budget will create the first).

## Milestones & issues

Create these as Gitea issues in `parkertdrake/ignite`, grouped under milestones
`M0 Foundation`, `M1 Budget`, `M2 FIRE`, `M3 Investments`, `Cross-cutting`.

### M0 — Foundation (do first; unblocks every screen)

- **Restructure backend into routers/services/schemas + `get_session` dependency.**
  Split `backend/main.py` into `routers/`, `services/`, `schemas/`. Add a FastAPI
  `get_session` dependency over the existing `Database.sessionmaker()`
  (`backend/persistence/db.py`). Establish the service-layer pattern (MCP-wrappable).
- **Frontend data layer: react-query + typed API client.** Add `@tanstack/react-query`
  and a `QueryClientProvider` in `frontend/src/main.tsx`. Generate the TS client + types
  from FastAPI's OpenAPI schema; wire a small `api/` module. Convert the existing
  `Sidebar` health poll to the new pattern as the reference example.
- **Household / People domain model (shared, N-person).** First real SQLAlchemy models in
  `backend/persistence/models.py` (`Household`, `Person`) + first Alembic migration.
  Shared by Budget (payers/incomes) and FIRE (incomes).

### M1 — Budget (screen 1, the meatiest)

- **Budget domain model + migration.** `Budget` (name, status `active|archived`, year),
  `Income`, `Expense` (item, cost, category, payer enum `JointFixed|JointVariable|<person>`),
  `Category` (user-defined), `SavingsGoal` (item, amount, payer, destination label,
  pre-tax flag). Parameters block (effective rate, division strategy + per-person %).
- **Budget math engine.** Pure functions: monthly usable = Σ remainders / 12; split joint
  costs by division %; individual costs whole; category spend + %; per-person breakdown;
  joint fixed vs variable buckets; **Budget Remainder (target $0)**. Fully unit-tested —
  this is the heart of the screen.
- **Tax engine — compute taxes from income.** Derive per-person taxes from gross income
  minus pre-tax deductions (401k/HSA), via brackets and/or effective-rate model. Feeds the
  Income → remainder calc. Note: bracket data goes stale yearly — design for annual params.
- **"Levers" division strategy.** Implement Manual %, Income-proportional, and the Levers
  strategy (tax-advantaged optimization; see Context). v1 = manual lever with documented
  reasoning; capture the optimization-solver idea as a stretch goal in the issue.
- **Budget CRUD API — create / edit / activate / archive / clone.** Endpoints over the
  service layer, incl. clone-for-new-year (you make a fresh budget yearly) and small edits.
- **Budget frontend — sheet-like editor.** UI resembling the Google Sheet: Parameters,
  Income, Expenses table, Savings Goals table, live-computed rollups (category %,
  breakdowns, joint allocations, remainder). Data via react-query; math from backend.

### M2 — FIRE

- **FIRE parameters model.** COL, number of kids, your income, projected income, partner
  income, projected partner income, growth/return assumptions, withdrawal rate, current net
  worth. Standalone inputs for now (accounts kept separate); may later pull savings rate
  from Budget and net worth from Investments.
- **FIRE Monte Carlo engine.** Simulate many return sequences; report probability of FI by
  year, FI-number, and estimated FI date with confidence bands. **Evaluate the existing
  `fire-simulator` repo (Gitea id 3) for reusable math before rebuilding.**
- **FIRE API + results endpoints.** Run-simulation endpoint returning distributional results
  for charting.
- **FIRE frontend.** Params form + charts: net-worth fan chart, probability-of-FI-by-year,
  FI-date estimate. (Charts: load the `dataviz` skill before building.)

### M3 — Investments

- **Investments domain model.** `Account` (type, institution), `Holding` (what it's invested
  in), `Event` (contribution, trade, income/earning, dividend) as a real-time timeline.
- **Market data / real-time pricing.** Decide + integrate a quote source for holding values
  and day-change. Own issue — cost/rate-limit/provider tradeoffs.
- **Investment data ingestion (deferred R&D).** The hard problem: unify holdings across many
  institutions. Leading idea: **AI-powered ingestion — dump account statement PDFs, have an
  LLM parse them into normalized events.** Also consider CSV import + (later) aggregators.
  Capture ideas; no build commitment yet.
- **Investments frontend.** Portfolio value/holdings/day-change + event timeline.

### Cross-cutting

- **MCP server (deferred).** Do not build now. Ensure the M0 service layer is cleanly
  wrappable so budget/FIRE/investment operations can later be exposed as MCP tools
  (e.g. "add expense", "run FIRE sim", "what's my net worth", "import statement").

## Key files

- `backend/main.py` — to be split into `backend/routers/`, `backend/services/`, `backend/schemas/`.
- `backend/persistence/models.py` — currently only `Base`; all models land here (or a models package).
- `backend/persistence/db.py` — add `get_session` FastAPI dependency here.
- `backend/alembic/versions/` — empty; first migration created by M0/M1.
- `frontend/src/main.tsx` — add `QueryClientProvider`.
- `frontend/src/` — new `api/` module (generated client + hooks); `pages/{Budget,Fire,Investments}.tsx` gain real data.
- `frontend/vite.config.ts` — `/api` proxy already points at `:8000`.

## Verification

- **Backend math:** unit tests per engine (budget splits, tax, Monte Carlo) with known
  fixtures — e.g. reproduce the sheet's numbers ($20,766 monthly usable, $0 remainder) as a
  golden test. `cd backend && pytest -q`.
- **Contracts:** OpenAPI schema generates the TS client without type errors; `npm run build`
  (runs `tsc`) stays green.
- **Frontend:** `cd frontend && npx vitest run`; drive each screen against a running backend
  with local hot-reload (user evaluates interactively).
- **End-to-end per milestone:** run the app locally, exercise the new screen's flow, confirm
  computed values match hand-calc / the sheet. Use the `/run` and `/verify` skills.

## Immediate next action (post-approval)

Create the milestones and the issues above in Gitea `parkertdrake/ignite` via the
`mcp__cairn__gitea_*` tools, then begin M0.
