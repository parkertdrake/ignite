import { formatCurrency } from "../lib/format";
import CollapsiblePanel from "./CollapsiblePanel";

// Trickle-down step 2 (blue): pre-tax contributions. Stub for now.
export default function PretaxSavingsPanel() {
  return (
    <CollapsiblePanel
      title="Pre-tax Savings"
      subtitle="Pre-tax contributions — 401(k), HSA."
      tone="savings"
      collapsedSummary={<span className="collapsed-total">{formatCurrency(0)}/mo</span>}
    >
      <p className="muted panel-stub">Coming soon.</p>
    </CollapsiblePanel>
  );
}
