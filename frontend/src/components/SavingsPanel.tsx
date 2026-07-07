import { formatCurrency } from "../lib/format";
import CollapsiblePanel from "./CollapsiblePanel";

// Trickle-down step 5 (blue): post-tax savings goals. Stub for now.
export default function SavingsPanel() {
  return (
    <CollapsiblePanel
      title="Savings"
      subtitle="Post-tax savings goals."
      tone="savings"
      collapsedSummary={<span className="collapsed-total">{formatCurrency(0)}/mo</span>}
    >
      <p className="muted panel-stub">Coming soon.</p>
    </CollapsiblePanel>
  );
}
