// Tax data hooks. Types mirror backend/schemas/taxes.py. Taxes are computed
// (not entered): the breakdown is derived from earnings, pre-tax savings, and
// the budget's tax config (year + state). Config changes invalidate the
// breakdown and ["budgets"] so the summary refreshes.
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "./client";

export interface TaxBreakdown {
  year: number | null;
  state: string | null;
  filing_status: string;
  gross: number;
  pretax_deductions: number;
  federal_taxable: number;
  state_taxable: number;
  federal_income: number;
  social_security: number;
  medicare: number;
  state_income: number;
  total_annual: number;
  effective_rate: number;
}

export interface TaxConfigOptions {
  years: number[];
  states: string[];
}

export interface TaxConfigInput {
  tax_year?: number | null;
  state?: string | null;
  filing_status?: string | null;
}

export function useTaxes(budgetId: number) {
  return useQuery({
    queryKey: ["taxes", budgetId],
    queryFn: () => apiClient.get<TaxBreakdown>(`/budgets/${budgetId}/taxes`),
  });
}

export function useTaxConfigOptions() {
  return useQuery({
    queryKey: ["tax-config-options"],
    queryFn: () => apiClient.get<TaxConfigOptions>("/tax-config/options"),
  });
}

export function useUpdateTaxConfig(budgetId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: TaxConfigInput) =>
      apiClient.patch(`/budgets/${budgetId}/tax-config`, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["taxes", budgetId] });
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
    },
  });
}
