import { useMemo, useState } from "react";
import {
  sankey as d3sankey,
  sankeyJustify,
  sankeyLinkHorizontal,
} from "d3-sankey";
import type { SankeyGraph, SankeyNode, SankeyLink } from "d3-sankey";
import type { BudgetFlow, FlowTone } from "../api/flow";
import { formatCurrency } from "../lib/format";

// Trickle-down cash flow as a Sankey: each earner's income pools into the
// household, then flows out to pre-tax savings, taxes, spending, post-tax
// savings, and any unallocated remainder. Dollar values are labelled on every
// node; hovering a link shows its monthly amount. Colours follow index.css.
const WIDTH = 560;
const HEIGHT = 300;
const NODE_WIDTH = 14;
const NODE_PADDING = 20;
const MARGIN = { top: 34, right: 8, bottom: 16, left: 8 };

const TONE_COLOR: Record<FlowTone, string> = {
  income: "var(--income)",
  savings: "var(--savings)",
  taxes: "var(--taxes)",
  spending: "var(--spending)",
  net: "var(--text-muted)",
  deficit: "var(--danger)",
};

interface NodeDatum {
  id: string;
  label: string;
  tone: FlowTone;
}
interface LinkDatum {
  source: string;
  target: string;
  value: number;
}
type LaidOutNode = SankeyNode<NodeDatum, LinkDatum>;
type LaidOutLink = SankeyLink<NodeDatum, LinkDatum>;

// The colour of a link is its non-household endpoint's tone — the real
// category the money belongs to (income in, or the bucket out).
function linkTone(link: LaidOutLink): FlowTone {
  const source = link.source as LaidOutNode;
  const target = link.target as LaidOutNode;
  return source.id === "household" ? target.tone : source.tone;
}

export default function SankeyChart({ flow }: { flow: BudgetFlow }) {
  const [hoveredLink, setHoveredLink] = useState<number | null>(null);
  const [tooltip, setTooltip] = useState<{ x: number; y: number; text: string } | null>(null);

  const graph = useMemo(() => {
    if (flow.nodes.length === 0) return null;
    // d3-sankey mutates its input, so hand it fresh clones each layout.
    const layout = d3sankey<NodeDatum, LinkDatum>()
      .nodeId((node) => node.id)
      .nodeWidth(NODE_WIDTH)
      .nodePadding(NODE_PADDING)
      .nodeAlign(sankeyJustify)
      .extent([
        [MARGIN.left, MARGIN.top],
        [WIDTH - MARGIN.right, HEIGHT - MARGIN.bottom],
      ]);
    const input: SankeyGraph<NodeDatum, LinkDatum> = {
      nodes: flow.nodes.map((node) => ({ ...node })),
      links: flow.links.map((link) => ({ ...link })),
    };
    try {
      return layout(input);
    } catch {
      return null;
    }
  }, [flow]);

  if (!graph) {
    return (
      <div className="chart-empty sankey-empty">
        <span>Add income to see the flow</span>
      </div>
    );
  }

  const linkPath = sankeyLinkHorizontal<NodeDatum, LinkDatum>();

  return (
    <div className="sankey">
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="sankey-svg" role="img"
        aria-label="Household income flowing to taxes, spending, and savings">
        <g className="sankey-links">
          {graph.links.map((link, index) => {
            const tone = linkTone(link as LaidOutLink);
            const dim = hoveredLink !== null && hoveredLink !== index;
            const source = link.source as LaidOutNode;
            const target = link.target as LaidOutNode;
            return (
              <path
                key={index}
                d={linkPath(link) ?? ""}
                stroke={TONE_COLOR[tone]}
                strokeWidth={Math.max(1, link.width ?? 0)}
                className="sankey-link"
                opacity={dim ? 0.15 : 0.4}
                onMouseEnter={(event) => {
                  setHoveredLink(index);
                  setTooltip({
                    x: event.nativeEvent.offsetX,
                    y: event.nativeEvent.offsetY,
                    text: `${source.label} → ${target.label}: ${formatCurrency(link.value ?? 0)}/mo`,
                  });
                }}
                onMouseMove={(event) =>
                  setTooltip((current) =>
                    current
                      ? { ...current, x: event.nativeEvent.offsetX, y: event.nativeEvent.offsetY }
                      : current
                  )
                }
                onMouseLeave={() => {
                  setHoveredLink(null);
                  setTooltip(null);
                }}
              />
            );
          })}
        </g>

        <g className="sankey-nodes">
          {graph.nodes.map((node) => {
            const laid = node as LaidOutNode;
            const x0 = laid.x0 ?? 0;
            const x1 = laid.x1 ?? 0;
            const y0 = laid.y0 ?? 0;
            const y1 = laid.y1 ?? 0;
            const height = Math.max(1, y1 - y0);
            // Labels sit outside the node, toward the chart interior.
            const onLeft = x0 < WIDTH / 2;
            const labelX = onLeft ? x1 + 6 : x0 - 6;
            const anchor = onLeft ? "start" : "end";
            const isHousehold = laid.id === "household";
            return (
              <g key={laid.id}>
                <rect
                  x={x0}
                  y={y0}
                  width={x1 - x0}
                  height={height}
                  fill={TONE_COLOR[laid.tone]}
                  rx={2}
                  className="sankey-node"
                />
                {isHousehold ? (
                  <text
                    className="sankey-node-label household"
                    x={(x0 + x1) / 2}
                    y={y0 - 14}
                    textAnchor="middle"
                  >
                    {laid.label} · {formatCurrency(laid.value ?? 0)}
                  </text>
                ) : (
                  <text
                    className="sankey-node-label"
                    x={labelX}
                    y={(y0 + y1) / 2}
                    dy="0.32em"
                    textAnchor={anchor}
                  >
                    <tspan className="sankey-node-name">{laid.label}</tspan>
                    <tspan className="sankey-node-value" dx="6">
                      {formatCurrency(laid.value ?? 0)}
                    </tspan>
                  </text>
                )}
              </g>
            );
          })}
        </g>
      </svg>

      {tooltip && (
        <div className="chart-tooltip" style={{ left: tooltip.x, top: tooltip.y }}>
          {tooltip.text}
        </div>
      )}
    </div>
  );
}
