// Earnings data hooks. Types mirror backend/schemas/earnings.py.
// Mutations invalidate both the earnings list and ["budgets"] so the
// summary header + cards refresh with the new income.
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "./client";

export interface Earning {
  id: number;
  budget_id: number;
  person: string;
  gross_annual: number;
}

export interface EarningInput {
  person: string;
  gross_annual: number;
}

const earningKeys = {
  forBudget: (budgetId: number) => ["earnings", budgetId] as const,
};

function useInvalidateAfterMutation(budgetId: number) {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: earningKeys.forBudget(budgetId) });
    queryClient.invalidateQueries({ queryKey: ["budgets"] });
  };
}

export function useEarnings(budgetId: number) {
  return useQuery({
    queryKey: earningKeys.forBudget(budgetId),
    queryFn: () => apiClient.get<Earning[]>(`/budgets/${budgetId}/earnings`),
  });
}

export function useCreateEarning(budgetId: number) {
  const invalidate = useInvalidateAfterMutation(budgetId);
  return useMutation({
    mutationFn: (input: EarningInput) =>
      apiClient.post<Earning>(`/budgets/${budgetId}/earnings`, input),
    onSuccess: invalidate,
  });
}

export function useUpdateEarning(budgetId: number) {
  const invalidate = useInvalidateAfterMutation(budgetId);
  return useMutation({
    mutationFn: ({ id, ...input }: Partial<EarningInput> & { id: number }) =>
      apiClient.patch<Earning>(`/budgets/${budgetId}/earnings/${id}`, input),
    onSuccess: invalidate,
  });
}

export function useDeleteEarning(budgetId: number) {
  const invalidate = useInvalidateAfterMutation(budgetId);
  return useMutation({
    mutationFn: (id: number) =>
      apiClient.del<void>(`/budgets/${budgetId}/earnings/${id}`),
    onSuccess: invalidate,
  });
}
