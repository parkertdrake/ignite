import SavingsLedgerPanel from "./SavingsLedgerPanel";

// Trickle-down step 5 (blue): post-tax savings goals.
export default function SavingsPanel({ budgetId }: { budgetId: number }) {
  return (
    <SavingsLedgerPanel
      budgetId={budgetId}
      pretax={false}
      title="Savings"
      subtitle="Post-tax savings goals — brokerage, cash, sinking funds."
      addLabel="+ Add savings goal"
    />
  );
}
