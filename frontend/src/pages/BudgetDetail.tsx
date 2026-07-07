import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useActivateBudget, useBudget } from "../api/budgets";
import CloneBudgetDialog from "../components/CloneBudgetDialog";
import DeleteBudgetDialog from "../components/DeleteBudgetDialog";
import EarningsPanel from "../components/EarningsPanel";
import SummaryHeader from "../components/SummaryHeader";
import { CopyIcon, TrashIcon } from "../components/icons";

export default function BudgetDetail() {
  const params = useParams();
  const navigate = useNavigate();
  const budgetId = Number(params.budgetId);
  const budgetQuery = useBudget(budgetId);
  const activateBudget = useActivateBudget();
  const [cloning, setCloning] = useState(false);
  const [deleting, setDeleting] = useState(false);

  if (Number.isNaN(budgetId)) {
    return <p className="error-text">Invalid budget id.</p>;
  }

  const budget = budgetQuery.data;

  return (
    <section className="page-section">
      <Link className="back-link" to="/budget">
        ← All budgets
      </Link>

      {budgetQuery.isLoading && <p className="muted">Loading…</p>}
      {budgetQuery.isError && (
        <p className="error-text">Could not load budget: {budgetQuery.error.message}</p>
      )}

      {budget && (
        <>
          <div className="section-head">
            <div>
              <h2>
                {budget.name}
                {budget.status === "active" && <span className="badge">Active</span>}
              </h2>
              <p className="muted">
                Created {new Date(budget.created_at).toLocaleDateString()}
              </p>
            </div>
            <div className="detail-actions">
              {budget.status !== "active" && (
                <button
                  className="btn btn-primary"
                  onClick={() => activateBudget.mutate(budgetId)}
                  disabled={activateBudget.isPending}
                >
                  Set active
                </button>
              )}
              <button
                className="btn-icon"
                aria-label="Duplicate budget"
                onClick={() => setCloning(true)}
              >
                <CopyIcon />
              </button>
              <button
                className="btn-icon danger"
                aria-label="Delete budget"
                onClick={() => setDeleting(true)}
              >
                <TrashIcon />
              </button>
            </div>
          </div>

          <SummaryHeader summary={budget.summary} />

          <EarningsPanel budgetId={budgetId} />

          {cloning && (
            <CloneBudgetDialog
              budget={budget}
              onClose={() => setCloning(false)}
              onCloned={(clone) => navigate(`/budget/${clone.id}`)}
            />
          )}
          {deleting && (
            <DeleteBudgetDialog
              budget={budget}
              onClose={() => setDeleting(false)}
              onDeleted={() => navigate("/budget")}
            />
          )}
        </>
      )}
    </section>
  );
}
