import { useRef, useState } from "react";
import {
  Earning,
  useCreateEarning,
  useDeleteEarning,
  useEarnings,
  useUpdateEarning,
} from "../api/earnings";
import { formatCurrency } from "../lib/format";

function XIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
      <path d="M6 6l12 12M18 6L6 18" />
    </svg>
  );
}

// Draw attention to an invalid field: a short red pulse.
function blink(element: HTMLElement | null) {
  element?.animate(
    [
      { boxShadow: "0 0 0 2px #ef4444" },
      { boxShadow: "0 0 0 2px rgba(239,68,68,0)" },
    ],
    { duration: 200, iterations: 3 },
  );
}

// Trickle-down step 1 (green): per-person gross salaried income.
export default function EarningsPanel({ budgetId }: { budgetId: number }) {
  const earningsQuery = useEarnings(budgetId);
  const [adding, setAdding] = useState(false);

  const earnings = earningsQuery.data ?? [];
  const monthlyTotal =
    earnings.reduce((sum, earning) => sum + earning.gross_annual, 0) / 12;
  const showLedger = earnings.length > 0 || adding;

  return (
    <section className="panel panel-income">
      <div className="panel-head">
        <h3 className="panel-title">Earnings</h3>
        <p className="panel-sub">Gross salaried income, per person.</p>
      </div>

      {earningsQuery.isLoading && <p className="muted">Loading…</p>}
      {earningsQuery.isError && (
        <p className="error-text">Could not load earnings: {earningsQuery.error.message}</p>
      )}

      {showLedger && (
        <div className="ledger">
          <div className="ledger-head">
            <span>Person</span>
            <span className="num">Gross / year</span>
            <span className="num">Monthly</span>
            <span />
          </div>
          {earnings.map((earning) => (
            <EarningRow key={earning.id} budgetId={budgetId} earning={earning} />
          ))}
          {adding && (
            <DraftRow budgetId={budgetId} onDone={() => setAdding(false)} />
          )}
        </div>
      )}

      {!adding && (
        <button className="btn btn-add add-trigger" onClick={() => setAdding(true)}>
          + Add income
        </button>
      )}

      {earnings.length > 0 && (
        <div className="panel-total">
          <span>Monthly income</span>
          <span className="num tone-income">{formatCurrency(monthlyTotal)}</span>
        </div>
      )}
    </section>
  );
}

function DraftRow({ budgetId, onDone }: { budgetId: number; onDone: () => void }) {
  const createEarning = useCreateEarning(budgetId);
  const [person, setPerson] = useState("");
  const [grossAnnual, setGrossAnnual] = useState("");
  const [errors, setErrors] = useState<{ person?: string; gross?: string }>({});
  const personRef = useRef<HTMLInputElement>(null);
  const grossRef = useRef<HTMLInputElement>(null);

  const confirm = (event: React.FormEvent) => {
    event.preventDefault();
    const name = person.trim();
    const amount = Number(grossAnnual);
    const nextErrors: { person?: string; gross?: string } = {};
    if (!name) nextErrors.person = "Enter a name";
    if (!grossAnnual.trim() || Number.isNaN(amount)) nextErrors.gross = "Enter a number";
    else if (amount < 0) nextErrors.gross = "Must be ≥ 0";

    if (nextErrors.person || nextErrors.gross) {
      setErrors(nextErrors);
      if (nextErrors.person) blink(personRef.current);
      if (nextErrors.gross) blink(grossRef.current);
      return;
    }
    createEarning.mutate({ person: name, gross_annual: amount }, { onSuccess: onDone });
  };

  return (
    <form className="ledger-row ledger-draft" onSubmit={confirm}>
      <input
        ref={personRef}
        className={`text-input${errors.person ? " field-error" : ""}`}
        placeholder="Person (e.g. Parker)"
        autoFocus
        value={person}
        maxLength={120}
        onChange={(event) => {
          setPerson(event.target.value);
          if (errors.person) setErrors((prev) => ({ ...prev, person: undefined }));
        }}
      />
      <input
        ref={grossRef}
        className={`text-input num${errors.gross ? " field-error" : ""}`}
        placeholder="Gross / year"
        inputMode="numeric"
        value={grossAnnual}
        onChange={(event) => {
          setGrossAnnual(event.target.value);
          if (errors.gross) setErrors((prev) => ({ ...prev, gross: undefined }));
        }}
      />
      <button className="btn btn-add" type="submit" disabled={createEarning.isPending}>
        Add
      </button>
      <button
        className="btn-icon"
        type="button"
        aria-label="Cancel"
        onClick={onDone}
      >
        <XIcon />
      </button>
      {(errors.person || errors.gross) && (
        <p className="field-msg">{errors.person ?? errors.gross}</p>
      )}
    </form>
  );
}

function EarningRow({ budgetId, earning }: { budgetId: number; earning: Earning }) {
  const updateEarning = useUpdateEarning(budgetId);
  const deleteEarning = useDeleteEarning(budgetId);
  const [person, setPerson] = useState(earning.person);
  const [grossAnnual, setGrossAnnual] = useState(String(earning.gross_annual));

  const commitPerson = () => {
    const name = person.trim();
    if (name && name !== earning.person) {
      updateEarning.mutate({ id: earning.id, person: name });
    } else if (!name) {
      setPerson(earning.person);
    }
  };

  const commitGross = () => {
    const amount = Number(grossAnnual);
    if (!Number.isNaN(amount) && amount >= 0 && amount !== earning.gross_annual) {
      updateEarning.mutate({ id: earning.id, gross_annual: amount });
    } else if (Number.isNaN(amount) || amount < 0) {
      setGrossAnnual(String(earning.gross_annual));
    }
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
        className="text-input num"
        value={grossAnnual}
        inputMode="numeric"
        onChange={(event) => setGrossAnnual(event.target.value)}
        onBlur={commitGross}
      />
      <span className="num ledger-monthly">
        {formatCurrency(earning.gross_annual / 12)}/mo
      </span>
      <button
        className="btn-icon danger"
        onClick={() => deleteEarning.mutate(earning.id)}
        disabled={deleteEarning.isPending}
        aria-label={`Remove ${earning.person}`}
      >
        <XIcon />
      </button>
    </div>
  );
}
