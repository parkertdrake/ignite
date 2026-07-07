import { formatCurrency } from "../lib/format";
import CollapsiblePanel from "./CollapsiblePanel";

// Trickle-down step 4 (red): expenses. Stub for now.
export default function SpendingPanel() {
  return (
    <CollapsiblePanel
      title="Spending"
      subtitle="Expenses by category."
      tone="spending"
      collapsedSummary={<span className="collapsed-total">{formatCurrency(0)}/mo</span>}
    >
      <p className="muted panel-stub">Coming soon.</p>
    </CollapsiblePanel>
  );
}
