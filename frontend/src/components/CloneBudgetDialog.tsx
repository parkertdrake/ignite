import { useState } from "react";
import { Budget, useCloneBudget } from "../api/budgets";
import Modal from "./Modal";

interface CloneBudgetDialogProps {
  budget: Budget;
  onClose: () => void;
  onCloned?: (clone: Budget) => void;
}

export default function CloneBudgetDialog({ budget, onClose, onCloned }: CloneBudgetDialogProps) {
  const cloneBudget = useCloneBudget();
  const [name, setName] = useState(`${budget.name} copy`);

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return;
    cloneBudget.mutate(
      { id: budget.id, name: trimmed },
      {
        onSuccess: (clone) => {
          onCloned?.(clone);
          onClose();
        },
      },
    );
  };

  return (
    <Modal title={`Duplicate “${budget.name}”`} onClose={onClose}>
      <form onSubmit={submit}>
        <p className="muted modal-text">Copies all contents into a new budget.</p>
        <input
          className="text-input modal-input"
          autoFocus
          value={name}
          maxLength={120}
          placeholder="New budget name"
          onChange={(event) => setName(event.target.value)}
        />
        {cloneBudget.isError && <p className="error-text">{cloneBudget.error.message}</p>}
        <div className="modal-actions">
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Cancel
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={cloneBudget.isPending || !name.trim()}
          >
            {cloneBudget.isPending ? "Duplicating…" : "Duplicate"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
