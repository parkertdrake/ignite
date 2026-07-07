import type { BudgetSummary } from "../api/budgets";
import { formatCurrency } from "../lib/format";

// Compact monthly stat row, colored per the trickle-down scheme:
// income green, savings blue, spending red, net neutral (green when
// balanced at $0, red when over-allocated).
interface SummaryHeaderProps {
  summary: BudgetSummary;
  variant?: "full" | "card";
}

export default function SummaryHeader({ summary, variant = "full" }: SummaryHeaderProps) {
  const netState = summary.net === 0 ? "balanced" : summary.net < 0 ? "over" : "";

  return (
    <div className={`summary-row ${variant}`}>
      <Stat label="Income" tone="income" value={summary.income} />
      <Stat label="Savings" tone="savings" value={summary.savings} />
      <Stat label="Spending" tone="spending" value={summary.spending} />
      <Stat label="Net" tone={`net ${netState}`} value={summary.net} />
    </div>
  );
}

function Stat({ label, tone, value }: { label: string; tone: string; value: number }) {
  return (
    <div className={`summary-stat ${tone}`}>
      <span className="summary-stat-label">{label}</span>
      <span className="summary-stat-value">{formatCurrency(value)}</span>
    </div>
  );
}
