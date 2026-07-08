import { useRef, useState } from "react";
import {
  Saving,
  SavingPeriod,
  useCreateSaving,
  useDeleteSaving,
  useSavings,
  useUpdateSaving,
} from "../api/savings";
import { formatCurrency } from "../lib/format";
import CollapsiblePanel from "./CollapsiblePanel";
import { XIcon } from "./icons";

// Convert between the stored annual amount and the value shown for a period.
const toDisplay = (annual: number, period: SavingPeriod) =>
  period === "monthly" ? annual / 12 : annual;
const toAnnual = (value: number, period: SavingPeriod) =>
  period === "monthly" ? value * 12 : value;
const displayString = (annual: number, period: SavingPeriod) => {
  const value = toDisplay(annual, period);
  return String(Math.round(value * 100) / 100);
};

interface SavingsLedgerPanelProps {
  budgetId: number;
  pretax: boolean;
  title: string;
  subtitle: string;
  addLabel: string;
}

// Shared ledger for pre-tax and post-tax savings (blue). Person / Account /
// Amount (with a monthly|yearly toggle) / derived Monthly. Amount is stored
// annualized; the toggle only changes how it's entered and shown.
export default function SavingsLedgerPanel({
  budgetId,
  pretax,
  title,
  subtitle,
  addLabel,
}: SavingsLedgerPanelProps) {
  const savingsQuery = useSavings(budgetId, pretax);
  const [adding, setAdding] = useState(false);

  const savings = savingsQuery.data ?? [];
  const monthlyTotal =
    savings.reduce((sum, saving) => sum + saving.amount_annual, 0) / 12;
  const showLedger = savings.length > 0 || adding;

  return (
    <CollapsiblePanel
      title={title}
      subtitle={subtitle}
      tone="savings"
      collapsedSummary={<span className="collapsed-total">{formatCurrency(monthlyTotal)}/mo</span>}
    >
      {savingsQuery.isLoading && <p className="muted">Loading…</p>}
      {savingsQuery.isError && (
        <p className="error-text">Could not load savings: {savingsQuery.error.message}</p>
      )}

      {showLedger && (
        <div className="ledger ledger-savings">
          <div className="ledger-head">
            <span>Person</span>
            <span>Account</span>
            <span className="num">Amount</span>
            <span className="num">Monthly</span>
            <span />
          </div>
          {savings.map((saving) => (
            <SavingRow key={saving.id} budgetId={budgetId} pretax={pretax} saving={saving} />
          ))}
          {adding && (
            <DraftRow budgetId={budgetId} pretax={pretax} onDone={() => setAdding(false)} />
          )}
        </div>
      )}

      {!adding && (
        <button className="btn btn-add add-trigger" onClick={() => setAdding(true)}>
          {addLabel}
        </button>
      )}

      {savings.length > 0 && (
        <div className="panel-total">
          <span>Monthly savings</span>
          <span className="num panel-total-value">{formatCurrency(monthlyTotal)}</span>
        </div>
      )}
    </CollapsiblePanel>
  );
}

function PeriodToggle({
  period,
  onChange,
}: {
  period: SavingPeriod;
  onChange: (period: SavingPeriod) => void;
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

function blink(element: HTMLElement | null) {
  element?.animate(
    [
      { boxShadow: "0 0 0 2px #ef4444" },
      { boxShadow: "0 0 0 2px rgba(239,68,68,0)" },
    ],
    { duration: 200, iterations: 3 },
  );
}

function DraftRow({
  budgetId,
  pretax,
  onDone,
}: {
  budgetId: number;
  pretax: boolean;
  onDone: () => void;
}) {
  const createSaving = useCreateSaving(budgetId, pretax);
  const [person, setPerson] = useState("");
  const [account, setAccount] = useState("");
  const [amount, setAmount] = useState("");
  const [period, setPeriod] = useState<SavingPeriod>("yearly");
  const [errors, setErrors] = useState<{ person?: string; account?: string; amount?: string }>({});
  const personRef = useRef<HTMLInputElement>(null);
  const accountRef = useRef<HTMLInputElement>(null);
  const amountRef = useRef<HTMLInputElement>(null);

  const confirm = (event: React.FormEvent) => {
    event.preventDefault();
    const name = person.trim();
    const accountName = account.trim();
    const value = Number(amount);
    const next: { person?: string; account?: string; amount?: string } = {};
    if (!name) next.person = "Enter a name";
    if (!accountName) next.account = "Enter an account";
    if (!amount.trim() || Number.isNaN(value)) next.amount = "Enter a number";
    else if (value < 0) next.amount = "Must be ≥ 0";

    if (next.person || next.account || next.amount) {
      setErrors(next);
      if (next.person) blink(personRef.current);
      if (next.account) blink(accountRef.current);
      if (next.amount) blink(amountRef.current);
      return;
    }
    createSaving.mutate(
      { person: name, account: accountName, amount_annual: toAnnual(value, period), period },
      { onSuccess: onDone },
    );
  };

  const clearError = (field: "person" | "account" | "amount") => {
    if (errors[field]) setErrors((prev) => ({ ...prev, [field]: undefined }));
  };

  return (
    <form className="ledger-row ledger-draft" onSubmit={confirm}>
      <input
        ref={personRef}
        className={`text-input${errors.person ? " field-error" : ""}`}
        placeholder="Person"
        autoFocus
        value={person}
        maxLength={120}
        onChange={(event) => {
          setPerson(event.target.value);
          clearError("person");
        }}
      />
      <input
        ref={accountRef}
        className={`text-input${errors.account ? " field-error" : ""}`}
        placeholder="Account (e.g. 401k)"
        value={account}
        maxLength={120}
        onChange={(event) => {
          setAccount(event.target.value);
          clearError("account");
        }}
      />
      <div className="amount-cell">
        <input
          ref={amountRef}
          className={`text-input num${errors.amount ? " field-error" : ""}`}
          placeholder="Amount"
          inputMode="numeric"
          value={amount}
          onChange={(event) => {
            setAmount(event.target.value);
            clearError("amount");
          }}
        />
        <PeriodToggle period={period} onChange={setPeriod} />
      </div>
      <button className="btn btn-add" type="submit" disabled={createSaving.isPending}>
        Add
      </button>
      <button className="btn-icon" type="button" aria-label="Cancel" onClick={onDone}>
        <XIcon />
      </button>
      {(errors.person || errors.account || errors.amount) && (
        <p className="field-msg">{errors.person ?? errors.account ?? errors.amount}</p>
      )}
    </form>
  );
}

function SavingRow({
  budgetId,
  pretax,
  saving,
}: {
  budgetId: number;
  pretax: boolean;
  saving: Saving;
}) {
  const updateSaving = useUpdateSaving(budgetId, pretax);
  const deleteSaving = useDeleteSaving(budgetId, pretax);
  const [person, setPerson] = useState(saving.person);
  const [account, setAccount] = useState(saving.account);
  const [amount, setAmount] = useState(displayString(saving.amount_annual, saving.period));

  const commitPerson = () => {
    const name = person.trim();
    if (name && name !== saving.person) updateSaving.mutate({ id: saving.id, person: name });
    else if (!name) setPerson(saving.person);
  };

  const commitAccount = () => {
    const value = account.trim();
    if (value && value !== saving.account) updateSaving.mutate({ id: saving.id, account: value });
    else if (!value) setAccount(saving.account);
  };

  const commitAmount = () => {
    const value = Number(amount);
    if (Number.isNaN(value) || value < 0) {
      setAmount(displayString(saving.amount_annual, saving.period));
      return;
    }
    const annual = toAnnual(value, saving.period);
    if (annual !== saving.amount_annual) {
      updateSaving.mutate({ id: saving.id, amount_annual: annual });
    }
  };

  const changePeriod = (period: SavingPeriod) => {
    if (period === saving.period) return;
    setAmount(displayString(saving.amount_annual, period));
    updateSaving.mutate({ id: saving.id, period });
  };

  return (
    <div className="ledger-row">
      <input
        className="text-input"
        value={person}
        maxLength={120}
        onChange={(event) => setPerson(event.target.value)}
        onBlur={commitPerson}
      />
      <input
        className="text-input"
        value={account}
        maxLength={120}
        onChange={(event) => setAccount(event.target.value)}
        onBlur={commitAccount}
      />
      <div className="amount-cell">
        <input
          className="text-input num"
          value={amount}
          inputMode="numeric"
          onChange={(event) => setAmount(event.target.value)}
          onBlur={commitAmount}
        />
        <PeriodToggle period={saving.period} onChange={changePeriod} />
      </div>
      <span className="num ledger-monthly">{formatCurrency(saving.amount_annual / 12)}/mo</span>
      <button
        className="btn-icon danger"
        onClick={() => deleteSaving.mutate(saving.id)}
        disabled={deleteSaving.isPending}
        aria-label={`Remove ${saving.account}`}
      >
        <XIcon />
      </button>
    </div>
  );
}
