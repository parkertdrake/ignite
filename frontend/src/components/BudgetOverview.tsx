import type { BudgetSummary } from "../api/budgets";
import { useBudgetFlow } from "../api/flow";
import DoughnutChart from "./DoughnutChart";
import SankeyChart from "./SankeyChart";

// Top-of-budget summary: a "where income goes" doughnut (1/3) beside a
// trickle-down cash-flow Sankey (2/3).
export default function BudgetOverview({
  budgetId,
  summary,
}: {
  budgetId: number;
  summary: BudgetSummary;
}) {
  const flowQuery = useBudgetFlow(budgetId);

  return (
    <div className="budget-overview">
      <div className="overview-panel overview-doughnut">
        <h3 className="overview-title">Where it goes</h3>
        <div className="doughnut-body">
          <DoughnutChart summary={summary} />
          <Legend summary={summary} />
        </div>
      </div>
      <div className="overview-panel overview-sankey">
        <h3 className="overview-title">Cash flow</h3>
        {flowQuery.isLoading && <div className="chart-empty">Loading…</div>}
        {flowQuery.isError && <div className="chart-empty">Could not load flow.</div>}
        {flowQuery.data && <SankeyChart flow={flowQuery.data} />}
      </div>
    </div>
  );
}

function Legend({ summary }: { summary: BudgetSummary }) {
  const items = [
    { label: "Savings", color: "var(--savings)", value: summary.savings },
    { label: "Taxes", color: "var(--taxes)", value: summary.taxes },
    { label: "Spending", color: "var(--spending)", value: summary.spending },
  ];
  if (summary.net > 0.5) {
    items.push({ label: "Unallocated", color: "var(--text-muted)", value: summary.net });
  }
  return (
    <ul className="doughnut-legend">
      {items
        .filter((item) => item.value > 0)
        .map((item) => (
          <li key={item.label}>
            <span className="legend-swatch" style={{ background: item.color }} />
            {item.label}
          </li>
        ))}
    </ul>
  );
}
