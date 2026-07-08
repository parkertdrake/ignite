import SavingsLedgerPanel from "./SavingsLedgerPanel";

// Trickle-down step 2 (blue): pre-tax contributions (401k, HSA).
export default function PretaxSavingsPanel({ budgetId }: { budgetId: number }) {
  return (
    <SavingsLedgerPanel
      budgetId={budgetId}
      pretax
      title="Pre-tax Savings"
      subtitle="Pre-tax contributions — 401(k), HSA."
      addLabel="+ Add pre-tax savings"
    />
  );
}
