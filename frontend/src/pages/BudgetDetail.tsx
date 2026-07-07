import { Link, useParams } from "react-router-dom";
import { useActivateBudget, useBudget } from "../api/budgets";

export default function BudgetDetail() {
  const params = useParams();
  const budgetId = Number(params.budgetId);
  const budgetQuery = useBudget(budgetId);
  const activateBudget = useActivateBudget();

  if (Number.isNaN(budgetId)) {
    return <p className="error-text">Invalid budget id.</p>;
  }

  return (
    <section className="page-section">
      <Link className="back-link" to="/budget">
        ← All budgets
      </Link>

      {budgetQuery.isLoading && <p className="muted">Loading…</p>}
      {budgetQuery.isError && (
        <p className="error-text">Could not load budget: {budgetQuery.error.message}</p>
      )}

      {budgetQuery.data && (
        <>
          <div className="section-head">
            <div>
              <h2>
                {budgetQuery.data.name}
                {budgetQuery.data.status === "active" && <span className="badge">Active</span>}
              </h2>
              <p className="muted">
                Created {new Date(budgetQuery.data.created_at).toLocaleDateString()}
              </p>
            </div>
            {budgetQuery.data.status !== "active" && (
              <button
                className="btn btn-primary"
                onClick={() => activateBudget.mutate(budgetId)}
                disabled={activateBudget.isPending}
              >
                Set active
              </button>
            )}
          </div>

          <div className="card">
            <h3>Contents</h3>
            <p className="muted">
              Income, expenses, and savings goals land here next. This is the budget shell —
              the editor is coming.
            </p>
          </div>
        </>
      )}
    </section>
  );
}
