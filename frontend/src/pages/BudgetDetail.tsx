import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useActivateBudget, useBudget } from "../api/budgets";
import CloneBudgetDialog from "../components/CloneBudgetDialog";
import DeleteBudgetDialog from "../components/DeleteBudgetDialog";
import BudgetOverview from "../components/BudgetOverview";
import EarningsPanel from "../components/EarningsPanel";
import PretaxSavingsPanel from "../components/PretaxSavingsPanel";
import SavingsPanel from "../components/SavingsPanel";
import SpendingPanel from "../components/SpendingPanel";
import TaxesPanel from "../components/TaxesPanel";
import { CheckIcon, CopyIcon, TrashIcon } from "../components/icons";

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
              <h2>{budget.name}</h2>
              <p className="muted">
                Created {new Date(budget.created_at).toLocaleDateString()}
              </p>
            </div>
            <div className="detail-actions">
              <button
                className={`btn-icon success${budget.status === "active" ? " on" : ""}`}
                aria-label={
                  budget.status === "active" ? "Budget is active" : "Set budget active"
                }
                aria-pressed={budget.status === "active"}
                onClick={() => {
                  if (budget.status !== "active") activateBudget.mutate(budgetId);
                }}
                disabled={activateBudget.isPending}
              >
                <CheckIcon />
              </button>
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

          <BudgetOverview budgetId={budgetId} summary={budget.summary} />

          <EarningsPanel budgetId={budgetId} />
          <PretaxSavingsPanel budgetId={budgetId} />
          <TaxesPanel budgetId={budgetId} />
          <SpendingPanel budgetId={budgetId} />
          <SavingsPanel budgetId={budgetId} />

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
