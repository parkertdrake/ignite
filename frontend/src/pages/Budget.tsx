import { useState } from "react";
import { Link } from "react-router-dom";
import { useActivateBudget, useBudgets, useCreateBudget } from "../api/budgets";

export default function Budget() {
  const budgetsQuery = useBudgets();
  const createBudget = useCreateBudget();
  const activateBudget = useActivateBudget();

  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");

  const submitCreate = (event: React.FormEvent) => {
    event.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return;
    createBudget.mutate(trimmed, {
      onSuccess: () => {
        setName("");
        setCreating(false);
      },
    });
  };

  return (
    <section className="page-section">
      <div className="section-head">
        <div>
          <h2>Budget</h2>
          <p className="muted">Manage your yearly budgets.</p>
        </div>
        {!creating && (
          <button className="btn btn-primary" onClick={() => setCreating(true)}>
            + New Budget
          </button>
        )}
      </div>

      {creating && (
        <form className="create-row" onSubmit={submitCreate}>
          <input
            className="text-input"
            autoFocus
            placeholder="Budget name (e.g. 2026)"
            value={name}
            onChange={(event) => setName(event.target.value)}
            maxLength={120}
          />
          <button className="btn btn-primary" type="submit" disabled={createBudget.isPending}>
            {createBudget.isPending ? "Creating…" : "Create"}
          </button>
          <button
            className="btn btn-ghost"
            type="button"
            onClick={() => {
              setCreating(false);
              setName("");
            }}
          >
            Cancel
          </button>
        </form>
      )}

      {createBudget.isError && (
        <p className="error-text">Could not create budget: {createBudget.error.message}</p>
      )}

      {budgetsQuery.isLoading && <p className="muted">Loading budgets…</p>}
      {budgetsQuery.isError && (
        <p className="error-text">Could not load budgets: {budgetsQuery.error.message}</p>
      )}

      {budgetsQuery.data && budgetsQuery.data.length === 0 && !creating && (
        <p className="muted">No budgets yet. Create your first one to get started.</p>
      )}

      {budgetsQuery.data && budgetsQuery.data.length > 0 && (
        <div className="card-grid">
          {budgetsQuery.data.map((budget) => {
            const isActive = budget.status === "active";
            return (
              <div key={budget.id} className={`budget-card${isActive ? " active" : ""}`}>
                <div className="budget-card-head">
                  <h3 className="budget-card-name">{budget.name}</h3>
                  {isActive && <span className="badge">Active</span>}
                </div>
                <div className="budget-card-actions">
                  <Link className="btn btn-ghost" to={`/budget/${budget.id}`}>
                    Open →
                  </Link>
                  {!isActive && (
                    <button
                      className="btn btn-ghost"
                      onClick={() => activateBudget.mutate(budget.id)}
                      disabled={activateBudget.isPending}
                    >
                      Activate
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
