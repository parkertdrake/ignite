// Budget cash-flow (Sankey) data. Mirrors backend/schemas/flow.py; keep in
// sync until OpenAPI codegen lands (M0 #2).
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "./client";

// Node tones mirror the trickle-down colour tokens in index.css.
export type FlowTone = "income" | "savings" | "taxes" | "spending" | "net" | "deficit";

export interface FlowNode {
  id: string;
  label: string;
  tone: FlowTone;
}

export interface FlowLink {
  source: string;
  target: string;
  value: number;
}

export interface BudgetFlow {
  nodes: FlowNode[];
  links: FlowLink[];
}

export function useBudgetFlow(budgetId: number) {
  return useQuery({
    queryKey: ["budgets", budgetId, "flow"],
    queryFn: () => apiClient.get<BudgetFlow>(`/budgets/${budgetId}/flow`),
  });
}
