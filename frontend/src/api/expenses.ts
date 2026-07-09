// Expense data hooks. Types mirror backend/schemas/expenses.py. Mutations
// invalidate the expense list and ["budgets"] so the summary (spending / net)
// refreshes. Amount is stored annualized; `period` is the entry unit.
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "./client";

export type ExpensePeriod = "monthly" | "yearly";
export type PayerType = "individual" | "joint_fixed" | "joint_variable";

export interface Expense {
  id: number;
  budget_id: number;
  item: string;
  amount_annual: number;
  period: ExpensePeriod;
  category_id: number | null;
  payer_type: PayerType;
  payer_person: string | null;
}

export interface ExpenseInput {
  item: string;
  amount_annual: number;
  period: ExpensePeriod;
  category_id: number | null;
  payer_type: PayerType;
  payer_person: string | null;
}

// PATCH accepts partial fields; clear_category distinguishes "leave as-is"
// from "set to uncategorized".
export type ExpensePatch = Partial<ExpenseInput> & { clear_category?: boolean };

function useInvalidateAfterMutation(budgetId: number) {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: ["expenses", budgetId] });
    queryClient.invalidateQueries({ queryKey: ["budgets"] });
  };
}

export function useExpenses(budgetId: number) {
  return useQuery({
    queryKey: ["expenses", budgetId],
    queryFn: () => apiClient.get<Expense[]>(`/budgets/${budgetId}/expenses`),
  });
}

export function useCreateExpense(budgetId: number) {
  const invalidate = useInvalidateAfterMutation(budgetId);
  return useMutation({
    mutationFn: (input: ExpenseInput) =>
      apiClient.post<Expense>(`/budgets/${budgetId}/expenses`, input),
    onSuccess: invalidate,
  });
}

export function useUpdateExpense(budgetId: number) {
  const invalidate = useInvalidateAfterMutation(budgetId);
  return useMutation({
    mutationFn: ({ id, ...patch }: ExpensePatch & { id: number }) =>
      apiClient.patch<Expense>(`/budgets/${budgetId}/expenses/${id}`, patch),
    onSuccess: invalidate,
  });
}

export function useDeleteExpense(budgetId: number) {
  const invalidate = useInvalidateAfterMutation(budgetId);
  return useMutation({
    mutationFn: (id: number) =>
      apiClient.del<void>(`/budgets/${budgetId}/expenses/${id}`),
    onSuccess: invalidate,
  });
}
