// Savings data hooks. Types mirror backend/schemas/savings.py. One table
// backs both panels; `pretax` filters/creates the right rows. Mutations
// invalidate the matching savings list and ["budgets"] so the summary
// refreshes.
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "./client";

export type SavingPeriod = "monthly" | "yearly";

export interface Saving {
  id: number;
  budget_id: number;
  person: string;
  account: string;
  amount_annual: number;
  period: SavingPeriod;
  pretax: boolean;
}

export interface SavingInput {
  person: string;
  account: string;
  amount_annual: number;
  period: SavingPeriod;
}

const savingKeys = {
  forBudget: (budgetId: number, pretax: boolean) => ["savings", budgetId, pretax] as const,
};

function useInvalidateAfterMutation(budgetId: number, pretax: boolean) {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: savingKeys.forBudget(budgetId, pretax) });
    queryClient.invalidateQueries({ queryKey: ["budgets"] });
  };
}

export function useSavings(budgetId: number, pretax: boolean) {
  return useQuery({
    queryKey: savingKeys.forBudget(budgetId, pretax),
    queryFn: () =>
      apiClient.get<Saving[]>(`/budgets/${budgetId}/savings?pretax=${pretax}`),
  });
}

export function useCreateSaving(budgetId: number, pretax: boolean) {
  const invalidate = useInvalidateAfterMutation(budgetId, pretax);
  return useMutation({
    mutationFn: (input: SavingInput) =>
      apiClient.post<Saving>(`/budgets/${budgetId}/savings`, { ...input, pretax }),
    onSuccess: invalidate,
  });
}

export function useUpdateSaving(budgetId: number, pretax: boolean) {
  const invalidate = useInvalidateAfterMutation(budgetId, pretax);
  return useMutation({
    mutationFn: ({ id, ...input }: Partial<SavingInput> & { id: number }) =>
      apiClient.patch<Saving>(`/budgets/${budgetId}/savings/${id}`, input),
    onSuccess: invalidate,
  });
}

export function useDeleteSaving(budgetId: number, pretax: boolean) {
  const invalidate = useInvalidateAfterMutation(budgetId, pretax);
  return useMutation({
    mutationFn: (id: number) => apiClient.del<void>(`/budgets/${budgetId}/savings/${id}`),
    onSuccess: invalidate,
  });
}
