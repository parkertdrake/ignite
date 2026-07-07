import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Budget as BudgetModel, useActivateBudget, useBudgets, useCreateBudget } from "../api/budgets";
import CloneBudgetDialog from "../components/CloneBudgetDialog";
import DeleteBudgetDialog from "../components/DeleteBudgetDialog";
import SummaryHeader from "../components/SummaryHeader";
import { CheckIcon, CopyIcon, TrashIcon } from "../components/icons";

export default function Budget() {
  const navigate = useNavigate();
  const budgetsQuery = useBudgets();
  const createBudget = useCreateBudget();
  const activateBudget = useActivateBudget();

  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [cloneTarget, setCloneTarget] = useState<BudgetModel | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<BudgetModel | null>(null);

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
            const open = () => navigate(`/budget/${budget.id}`);
            return (
              <div
                key={budget.id}
                className={`budget-card${isActive ? " active" : ""}`}
                role="button"
                tabIndex={0}
                onClick={open}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    open();
                  }
                }}
              >
                <div className="budget-card-head">
                  <h3 className="budget-card-name">{budget.name}</h3>
                  <div className="card-head-right">
                    <div className="card-icons">
                      <button
                        className={`btn-icon success${isActive ? " on" : ""}`}
                        aria-label={
                          isActive ? `${budget.name} is active` : `Set ${budget.name} active`
                        }
                        aria-pressed={isActive}
                        onClick={(event) => {
                          event.stopPropagation();
                          if (!isActive) activateBudget.mutate(budget.id);
                        }}
                        disabled={activateBudget.isPending}
                      >
                        <CheckIcon />
                      </button>
                      <button
                        className="btn-icon"
                        aria-label={`Duplicate ${budget.name}`}
                        onClick={(event) => {
                          event.stopPropagation();
                          setCloneTarget(budget);
                        }}
                      >
                        <CopyIcon />
                      </button>
                      <button
                        className="btn-icon danger"
                        aria-label={`Delete ${budget.name}`}
                        onClick={(event) => {
                          event.stopPropagation();
                          setDeleteTarget(budget);
                        }}
                      >
                        <TrashIcon />
                      </button>
                    </div>
                  </div>
                </div>
                <SummaryHeader summary={budget.summary} variant="card" />
              </div>
            );
          })}
        </div>
      )}

      {cloneTarget && (
        <CloneBudgetDialog budget={cloneTarget} onClose={() => setCloneTarget(null)} />
      )}
      {deleteTarget && (
        <DeleteBudgetDialog budget={deleteTarget} onClose={() => setDeleteTarget(null)} />
      )}
    </section>
  );
}
