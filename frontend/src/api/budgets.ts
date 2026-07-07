// Budget data hooks. Types mirror backend/schemas/budgets.py; keep in
// sync until OpenAPI codegen lands (M0 #2).
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "./client";

export type BudgetStatus = "active" | "inactive";

export interface Budget {
  id: number;
  name: string;
  status: BudgetStatus;
  created_at: string;
}

const budgetKeys = {
  all: ["budgets"] as const,
  detail: (id: number) => ["budgets", id] as const,
};

export function useBudgets() {
  return useQuery({
    queryKey: budgetKeys.all,
    queryFn: () => apiClient.get<Budget[]>("/budgets"),
  });
}

export function useBudget(id: number) {
  return useQuery({
    queryKey: budgetKeys.detail(id),
    queryFn: () => apiClient.get<Budget>(`/budgets/${id}`),
  });
}

export function useCreateBudget() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => apiClient.post<Budget>("/budgets", { name }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: budgetKeys.all }),
  });
}

export function useActivateBudget() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiClient.post<Budget>(`/budgets/${id}/activate`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: budgetKeys.all }),
  });
}
