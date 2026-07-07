import { Budget, useDeleteBudget } from "../api/budgets";
import Modal from "./Modal";

interface DeleteBudgetDialogProps {
  budget: Budget;
  onClose: () => void;
  onDeleted?: () => void;
}

export default function DeleteBudgetDialog({ budget, onClose, onDeleted }: DeleteBudgetDialogProps) {
  const deleteBudget = useDeleteBudget();

  const confirm = () => {
    deleteBudget.mutate(budget.id, {
      onSuccess: () => {
        onDeleted?.();
        onClose();
      },
    });
  };

  return (
    <Modal title={`Delete “${budget.name}”?`} onClose={onClose}>
      <p className="muted modal-text">
        This permanently deletes the budget and all of its contents. This can’t be undone.
      </p>
      {deleteBudget.isError && <p className="error-text">{deleteBudget.error.message}</p>}
      <div className="modal-actions">
        <button className="btn btn-ghost" onClick={onClose}>
          Cancel
        </button>
        <button className="btn btn-danger" onClick={confirm} disabled={deleteBudget.isPending}>
          {deleteBudget.isPending ? "Deleting…" : "Delete"}
        </button>
      </div>
    </Modal>
  );
}
