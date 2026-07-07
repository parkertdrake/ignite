import { formatCurrency } from "../lib/format";
import CollapsiblePanel from "./CollapsiblePanel";

// Trickle-down step 3 (orange): income taxes. Stub for now.
export default function TaxesPanel() {
  return (
    <CollapsiblePanel
      title="Taxes"
      subtitle="Income tax on gross earnings."
      tone="taxes"
      collapsedSummary={<span className="collapsed-total">{formatCurrency(0)}/mo</span>}
    >
      <p className="muted panel-stub">Coming soon.</p>
    </CollapsiblePanel>
  );
}
