import { useRef, useState } from "react";
import { useCategories, useCreateCategory } from "../api/categories";
import { useEarnings } from "../api/earnings";
import {
  Expense,
  ExpensePeriod,
  PayerType,
  useCreateExpense,
  useDeleteExpense,
  useExpenses,
  useUpdateExpense,
} from "../api/expenses";
import { formatCurrency } from "../lib/format";
import CollapsiblePanel from "./CollapsiblePanel";
import { XIcon } from "./icons";

const MONTHS_PER_YEAR = 12;

const toDisplay = (annual: number, period: ExpensePeriod) =>
  period === "monthly" ? annual / MONTHS_PER_YEAR : annual;
const toAnnual = (value: number, period: ExpensePeriod) =>
  period === "monthly" ? value * MONTHS_PER_YEAR : value;
const displayString = (annual: number, period: ExpensePeriod) =>
  String(Math.round(toDisplay(annual, period) * 100) / 100);

const PAYER_LABELS: Record<PayerType, string> = {
  joint_variable: "Joint Variable",
  joint_fixed: "Joint Fixed",
  individual: "Individual",
};

function blink(element: HTMLElement | null) {
  element?.animate(
    [
      { boxShadow: "0 0 0 2px #ef4444" },
      { boxShadow: "0 0 0 2px rgba(239,68,68,0)" },
    ],
    { duration: 200, iterations: 3 },
  );
}

// Trickle-down step 4 (red): household spending. Item / amount / category /
// payer, mirroring the sheet. Payer classifies funding (individual vs joint
// fixed/variable) for the future Levers split; category rolls up below.
export default function SpendingPanel({ budgetId }: { budgetId: number }) {
  const expensesQuery = useExpenses(budgetId);
  const categoriesQuery = useCategories(budgetId);
  const earningsQuery = useEarnings(budgetId);
  const [adding, setAdding] = useState(false);

  const expenses = expensesQuery.data ?? [];
  const categories = categoriesQuery.data ?? [];
  const persons = (earningsQuery.data ?? []).map((earning) => earning.person);
  const categoryName = new Map(categories.map((category) => [category.id, category.name]));

  const monthlyTotal =
    expenses.reduce((sum, expense) => sum + expense.amount_annual, 0) / MONTHS_PER_YEAR;
  const showLedger = expenses.length > 0 || adding;

  return (
    <CollapsiblePanel
      title="Spending"
      subtitle="Expenses by category and payer."
      tone="spending"
      collapsedSummary={<span className="collapsed-total">{formatCurrency(monthlyTotal)}/mo</span>}
    >
      {expensesQuery.isLoading && <p className="muted">Loading…</p>}
      {expensesQuery.isError && (
        <p className="error-text">Could not load expenses: {expensesQuery.error.message}</p>
      )}

      {showLedger && (
        <div className="ledger ledger-spending">
          <div className="ledger-head">
            <span>Item</span>
            <span>Category</span>
            <span>Payer</span>
            <span className="num">Amount</span>
            <span />
          </div>
          {expenses.map((expense) => (
            <ExpenseRow
              key={expense.id}
              budgetId={budgetId}
              expense={expense}
              categories={categories}
              persons={persons}
            />
          ))}
          {adding && (
            <DraftRow
              budgetId={budgetId}
              categories={categories}
              persons={persons}
              onDone={() => setAdding(false)}
            />
          )}
        </div>
      )}

      {!adding && (
        <button className="btn btn-add add-trigger" onClick={() => setAdding(true)}>
          + Add expense
        </button>
      )}

      {expenses.length > 0 && (
        <>
          <CategoryBreakdown expenses={expenses} categoryName={categoryName} />
          <div className="panel-total">
            <span>Monthly spending</span>
            <span className="num panel-total-value">{formatCurrency(monthlyTotal)}</span>
          </div>
        </>
      )}
    </CollapsiblePanel>
  );
}

function CategoryBreakdown({
  expenses,
  categoryName,
}: {
  expenses: Expense[];
  categoryName: Map<number, string>;
}) {
  const totals = new Map<string, number>();
  for (const expense of expenses) {
    const label =
      expense.category_id === null
        ? "Uncategorized"
        : categoryName.get(expense.category_id) ?? "Uncategorized";
    totals.set(label, (totals.get(label) ?? 0) + expense.amount_annual / MONTHS_PER_YEAR);
  }
  const rows = [...totals.entries()].sort((left, right) => right[1] - left[1]);

  return (
    <div className="category-breakdown">
      <p className="breakdown-title">By category</p>
      {rows.map(([label, monthly]) => (
        <div key={label} className="breakdown-row">
          <span>{label}</span>
          <span className="num ledger-monthly">{formatCurrency(monthly)}/mo</span>
        </div>
      ))}
    </div>
  );
}

function CategorySelect({
  budgetId,
  value,
  onChange,
  categories,
}: {
  budgetId: number;
  value: number | null;
  onChange: (categoryId: number | null) => void;
  categories: { id: number; name: string }[];
}) {
  const createCategory = useCreateCategory(budgetId);
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");

  if (creating) {
    const confirm = () => {
      const trimmed = name.trim();
      if (!trimmed) {
        setCreating(false);
        return;
      }
      createCategory.mutate(trimmed, {
        onSuccess: (category) => {
          onChange(category.id);
          setCreating(false);
          setName("");
        },
      });
    };
    return (
      <input
        className="text-input"
        placeholder="New category"
        autoFocus
        value={name}
        maxLength={120}
        onChange={(event) => setName(event.target.value)}
        onBlur={confirm}
        onKeyDown={(event) => {
          if (event.key === "Enter") confirm();
          if (event.key === "Escape") setCreating(false);
        }}
      />
    );
  }

  return (
    <select
      className="select-input"
      value={value ?? ""}
      onChange={(event) => {
        if (event.target.value === "__new__") {
          setCreating(true);
          return;
        }
        onChange(event.target.value ? Number(event.target.value) : null);
      }}
    >
      <option value="">Uncategorized</option>
      {categories.map((category) => (
        <option key={category.id} value={category.id}>
          {category.name}
        </option>
      ))}
      <option value="__new__">+ New category…</option>
    </select>
  );
}

interface PayerValue {
  payer_type: PayerType;
  payer_person: string | null;
}

function PayerSelect({
  payerType,
  payerPerson,
  persons,
  onChange,
}: {
  payerType: PayerType;
  payerPerson: string | null;
  persons: string[];
  onChange: (value: PayerValue) => void;
}) {
  // Keep the current owner selectable even if they're not in earnings.
  const people =
    payerType === "individual" && payerPerson && !persons.includes(payerPerson)
      ? [...persons, payerPerson]
      : persons;
  const value = payerType === "individual" ? `person:${payerPerson}` : payerType;

  return (
    <select
      className="select-input"
      value={value}
      onChange={(event) => {
        const selected = event.target.value;
        if (selected.startsWith("person:")) {
          onChange({ payer_type: "individual", payer_person: selected.slice(7) });
        } else {
          onChange({ payer_type: selected as PayerType, payer_person: null });
        }
      }}
    >
      <option value="joint_variable">{PAYER_LABELS.joint_variable}</option>
      <option value="joint_fixed">{PAYER_LABELS.joint_fixed}</option>
      {people.map((person) => (
        <option key={person} value={`person:${person}`}>
          {person}
        </option>
      ))}
    </select>
  );
}

function DraftRow({
  budgetId,
  categories,
  persons,
  onDone,
}: {
  budgetId: number;
  categories: { id: number; name: string }[];
  persons: string[];
  onDone: () => void;
}) {
  const createExpense = useCreateExpense(budgetId);
  const [item, setItem] = useState("");
  const [amount, setAmount] = useState("");
  const [period, setPeriod] = useState<ExpensePeriod>("monthly");
  const [categoryId, setCategoryId] = useState<number | null>(null);
  const [payer, setPayer] = useState<PayerValue>({
    payer_type: "joint_variable",
    payer_person: null,
  });
  const [errors, setErrors] = useState<{ item?: string; amount?: string }>({});
  const itemRef = useRef<HTMLInputElement>(null);
  const amountRef = useRef<HTMLInputElement>(null);

  const confirm = (event: React.FormEvent) => {
    event.preventDefault();
    const name = item.trim();
    const value = Number(amount);
    const next: { item?: string; amount?: string } = {};
    if (!name) next.item = "Enter an item";
    if (!amount.trim() || Number.isNaN(value)) next.amount = "Enter a number";
    else if (value < 0) next.amount = "Must be ≥ 0";

    if (next.item || next.amount) {
      setErrors(next);
      if (next.item) blink(itemRef.current);
      if (next.amount) blink(amountRef.current);
      return;
    }
    createExpense.mutate(
      {
        item: name,
        amount_annual: toAnnual(value, period),
        period,
        category_id: categoryId,
        payer_type: payer.payer_type,
        payer_person: payer.payer_person,
      },
      { onSuccess: onDone },
    );
  };

  return (
    <form className="ledger-row ledger-draft" onSubmit={confirm}>
      <input
        ref={itemRef}
        className={`text-input${errors.item ? " field-error" : ""}`}
        placeholder="Item"
        autoFocus
        value={item}
        maxLength={200}
        onChange={(event) => {
          setItem(event.target.value);
          if (errors.item) setErrors((prev) => ({ ...prev, item: undefined }));
        }}
      />
      <CategorySelect
        budgetId={budgetId}
        value={categoryId}
        onChange={setCategoryId}
        categories={categories}
      />
      <PayerSelect
        payerType={payer.payer_type}
        payerPerson={payer.payer_person}
        persons={persons}
        onChange={setPayer}
      />
      <div className="amount-cell">
        <PeriodToggle period={period} onChange={setPeriod} />
        <input
          ref={amountRef}
          className={`text-input num${errors.amount ? " field-error" : ""}`}
          placeholder="Amount"
          inputMode="numeric"
          value={amount}
          onChange={(event) => {
            setAmount(event.target.value);
            if (errors.amount) setErrors((prev) => ({ ...prev, amount: undefined }));
          }}
        />
      </div>
      <div className="draft-actions">
        <button className="btn btn-add" type="submit" disabled={createExpense.isPending}>
          Add
        </button>
        <button className="btn-icon" type="button" aria-label="Cancel" onClick={onDone}>
          <XIcon />
        </button>
      </div>
      {(errors.item || errors.amount) && (
        <p className="field-msg">{errors.item ?? errors.amount}</p>
      )}
    </form>
  );
}

function ExpenseRow({
  budgetId,
  expense,
  categories,
  persons,
}: {
  budgetId: number;
  expense: Expense;
  categories: { id: number; name: string }[];
  persons: string[];
}) {
  const updateExpense = useUpdateExpense(budgetId);
  const deleteExpense = useDeleteExpense(budgetId);
  const [item, setItem] = useState(expense.item);
  const [amount, setAmount] = useState(displayString(expense.amount_annual, expense.period));

  const commitItem = () => {
    const name = item.trim();
    if (name && name !== expense.item) updateExpense.mutate({ id: expense.id, item: name });
    else if (!name) setItem(expense.item);
  };

  const commitAmount = () => {
    const value = Number(amount);
    if (Number.isNaN(value) || value < 0) {
      setAmount(displayString(expense.amount_annual, expense.period));
      return;
    }
    const annual = toAnnual(value, expense.period);
    if (annual !== expense.amount_annual) {
      updateExpense.mutate({ id: expense.id, amount_annual: annual });
    }
  };

  const changePeriod = (period: ExpensePeriod) => {
    if (period === expense.period) return;
    setAmount(displayString(expense.amount_annual, period));
    updateExpense.mutate({ id: expense.id, period });
  };

  return (
    <div className="ledger-row">
      <input
        className="text-input"
        value={item}
        maxLength={200}
        onChange={(event) => setItem(event.target.value)}
        onBlur={commitItem}
      />
      <CategorySelect
        budgetId={budgetId}
        value={expense.category_id}
        onChange={(categoryId) =>
          updateExpense.mutate(
            categoryId === null
              ? { id: expense.id, clear_category: true }
              : { id: expense.id, category_id: categoryId },
          )
        }
        categories={categories}
      />
      <PayerSelect
        payerType={expense.payer_type}
        payerPerson={expense.payer_person}
        persons={persons}
        onChange={(value) => updateExpense.mutate({ id: expense.id, ...value })}
      />
      <div className="amount-cell">
        <PeriodToggle period={expense.period} onChange={changePeriod} />
        <input
          className="text-input num"
          value={amount}
          inputMode="numeric"
          onChange={(event) => setAmount(event.target.value)}
          onBlur={commitAmount}
        />
      </div>
      <button
        className="btn-icon danger"
        onClick={() => deleteExpense.mutate(expense.id)}
        disabled={deleteExpense.isPending}
        aria-label={`Remove ${expense.item}`}
      >
        <XIcon />
      </button>
    </div>
  );
}

function PeriodToggle({
  period,
  onChange,
}: {
  period: ExpensePeriod;
  onChange: (period: ExpensePeriod) => void;
}) {
  return (
    <div className="period-toggle" role="group" aria-label="Amount period">
      <button
        type="button"
        className={period === "monthly" ? "active" : ""}
        aria-pressed={period === "monthly"}
        onClick={() => onChange("monthly")}
      >
        mo
      </button>
      <button
        type="button"
        className={period === "yearly" ? "active" : ""}
        aria-pressed={period === "yearly"}
        onClick={() => onChange("yearly")}
      >
        yr
      </button>
    </div>
  );
}
