import { useMemo, useState } from "react";
import { arc as d3arc, pie as d3pie } from "d3-shape";
import type { BudgetSummary } from "../api/budgets";
import { formatCurrency } from "../lib/format";

// "Where income goes" doughnut. Income is the whole ring; slices are the
// allocations (savings / taxes / spending) plus any unallocated remainder.
// Percentages are share-of-income and always shown; dollar amounts appear in
// the centre on hover. Colours follow the trickle-down tokens in index.css.
interface Segment {
  key: string;
  label: string;
  color: string;
  value: number;
}

const SIZE = 240;
const RADIUS = SIZE / 2;
const RING = 34; // ring thickness

export default function DoughnutChart({ summary }: { summary: BudgetSummary }) {
  const [hovered, setHovered] = useState<string | null>(null);

  const segments = useMemo<Segment[]>(() => {
    const base: Segment[] = [
      { key: "savings", label: "Savings", color: "var(--savings)", value: summary.savings },
      { key: "taxes", label: "Taxes", color: "var(--taxes)", value: summary.taxes },
      { key: "spending", label: "Spending", color: "var(--spending)", value: summary.spending },
    ];
    if (summary.net > 0.5) {
      base.push({
        key: "unallocated",
        label: "Unallocated",
        color: "var(--text-muted)",
        value: summary.net,
      });
    }
    return base.filter((segment) => segment.value > 0);
  }, [summary]);

  const wholeTotal = segments.reduce((sum, segment) => sum + segment.value, 0);
  const overBy = summary.net < -0.5 ? -summary.net : 0;

  const arcs = useMemo(() => {
    const layout = d3pie<Segment>()
      .sort(null)
      .padAngle(0.02)
      .value((segment) => segment.value);
    const arcGen = d3arc<ReturnType<typeof layout>[number]>()
      .innerRadius(RADIUS - RING)
      .outerRadius(RADIUS)
      .cornerRadius(3);
    return layout(segments).map((slice) => ({
      segment: slice.data,
      path: arcGen(slice) ?? "",
      centroid: arcGen.centroid(slice),
      fraction: wholeTotal > 0 ? slice.data.value / wholeTotal : 0,
    }));
  }, [segments, wholeTotal]);

  if (wholeTotal === 0) {
    return (
      <div className="chart-empty doughnut-empty">
        <span>No income yet</span>
      </div>
    );
  }

  const active = hovered ? segments.find((segment) => segment.key === hovered) : null;
  const percent = (value: number) => `${Math.round((value / wholeTotal) * 100)}%`;

  return (
    <div className="doughnut">
      <svg viewBox={`0 0 ${SIZE} ${SIZE}`} className="doughnut-svg" role="img"
        aria-label="Allocation of income by savings, taxes, spending, and unallocated">
        <g transform={`translate(${RADIUS}, ${RADIUS})`}>
          {arcs.map(({ segment, path, centroid, fraction }) => {
            const dim = hovered !== null && hovered !== segment.key;
            return (
              <g key={segment.key}>
                <path
                  d={path}
                  fill={segment.color}
                  className="doughnut-arc"
                  opacity={dim ? 0.35 : 1}
                  onMouseEnter={() => setHovered(segment.key)}
                  onMouseLeave={() => setHovered(null)}
                />
                {fraction >= 0.06 && (
                  <text
                    className="doughnut-arc-label"
                    x={centroid[0]}
                    y={centroid[1]}
                    dy="0.35em"
                    textAnchor="middle"
                  >
                    {percent(segment.value)}
                  </text>
                )}
              </g>
            );
          })}
        </g>
      </svg>

      <div className="doughnut-center">
        {active ? (
          <>
            <span className="doughnut-center-label" style={{ color: active.color }}>
              {active.label}
            </span>
            <span className="doughnut-center-value">{formatCurrency(active.value)}</span>
            <span className="doughnut-center-sub">{percent(active.value)} of income</span>
          </>
        ) : (
          <>
            <span className="doughnut-center-label">Income</span>
            <span className="doughnut-center-value">{formatCurrency(summary.income)}</span>
            <span className="doughnut-center-sub">
              {overBy > 0 ? `over by ${formatCurrency(overBy)}` : "/ month"}
            </span>
          </>
        )}
      </div>
    </div>
  );
}
