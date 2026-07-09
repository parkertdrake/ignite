// Category data hooks. Types mirror backend/schemas/categories.py.
// Categories are per-budget, created inline from the expense dropdown.
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "./client";

export interface Category {
  id: number;
  budget_id: number;
  name: string;
  sort_order: number;
}

export function useCategories(budgetId: number) {
  return useQuery({
    queryKey: ["categories", budgetId],
    queryFn: () => apiClient.get<Category[]>(`/budgets/${budgetId}/categories`),
  });
}

export function useCreateCategory(budgetId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name: string) =>
      apiClient.post<Category>(`/budgets/${budgetId}/categories`, { name }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["categories", budgetId] }),
  });
}

export function useDeleteCategory(budgetId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      apiClient.del<void>(`/budgets/${budgetId}/categories/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categories", budgetId] });
      // Deleting a category uncategorizes its expenses.
      queryClient.invalidateQueries({ queryKey: ["expenses", budgetId] });
    },
  });
}
