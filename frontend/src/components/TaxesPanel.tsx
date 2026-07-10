import { useEffect, useState } from "react";
import { formatCurrency } from "../lib/format";
import { useTaxConfigOptions, useTaxes, useUpdateTaxConfig } from "../api/taxes";
import CollapsiblePanel from "./CollapsiblePanel";

// Trickle-down step 3 (orange): computed income + payroll taxes. Figures come
// from the backend tax engine (gross − pre-tax savings, MFJ brackets, FICA,
// optional state); this panel only picks the tax year / state and renders.
const MONTHS_PER_YEAR = 12;

const formatPercent = (rate: number) => `${(rate * 100).toFixed(1)}%`;

export default function TaxesPanel({ budgetId }: { budgetId: number }) {
  const taxesQuery = useTaxes(budgetId);
  const optionsQuery = useTaxConfigOptions();
  const updateConfig = useUpdateTaxConfig(budgetId);

  const breakdown = taxesQuery.data;
  const monthlyTotal = (breakdown?.total_annual ?? 0) / MONTHS_PER_YEAR;
  const effectiveRate = breakdown?.effective_rate ?? 0;
  const overrideMonthly = (breakdown?.override_annual ?? 0) / MONTHS_PER_YEAR;
  const gross = breakdown?.gross ?? 0;
  const overrideRate = gross > 0 ? (breakdown?.override_annual ?? 0) / gross : 0;

  // Editable monthly override, seeded from the backend and committed on blur.
  const [overrideDraft, setOverrideDraft] = useState("");
  useEffect(() => {
    setOverrideDraft(overrideMonthly > 0 ? String(Math.round(overrideMonthly)) : "");
  }, [overrideMonthly]);

  const commitOverride = () => {
    const parsed = Math.max(0, Number(overrideDraft) || 0);
    if (parsed !== overrideMonthly) {
      updateConfig.mutate({ tax_override_monthly: parsed });
    }
  };

  const collapsedSummary = (
    <span className="collapsed-total">
      {formatPercent(effectiveRate)}
      {overrideRate > 0 && ` (+ ${formatPercent(overrideRate)})`} ·{" "}
      {formatCurrency(monthlyTotal)}/mo
    </span>
  );

  const monthly = (annual: number | undefined) =>
    `${formatCurrency((annual ?? 0) / MONTHS_PER_YEAR)}/mo`;

  return (
    <CollapsiblePanel
      title="Taxes"
      subtitle="Computed from gross earnings minus pre-tax savings."
      tone="taxes"
      collapsedSummary={collapsedSummary}
    >
      {taxesQuery.isLoading && <p className="muted">Loading…</p>}
      {taxesQuery.isError && (
        <p className="error-text">Could not load taxes: {taxesQuery.error.message}</p>
      )}

      {breakdown && (
        <>
          <div className="tax-config">
            <label className="tax-field">
              <span>Tax year</span>
              <select
                className="select-input"
                value={breakdown.year ?? ""}
                disabled={updateConfig.isPending}
                onChange={(event) =>
                  updateConfig.mutate({ tax_year: Number(event.target.value) })
                }
              >
                {(optionsQuery.data?.years ?? []).map((year) => (
                  <option key={year} value={year}>
                    {year}
                  </option>
                ))}
              </select>
            </label>
            <label className="tax-field">
              <span>State</span>
              <select
                className="select-input"
                value={breakdown.state ?? ""}
                disabled={updateConfig.isPending}
                onChange={(event) => updateConfig.mutate({ state: event.target.value })}
              >
                <option value="">No state tax</option>
                {(optionsQuery.data?.states ?? []).map((state) => (
                  <option key={state} value={state}>
                    {state}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <p className="muted tax-basis">
            Taxable income (federal): {formatCurrency(breakdown.federal_taxable)}/yr · after{" "}
            {formatCurrency(breakdown.pretax_deductions)} pre-tax
          </p>

          <div className="tax-lines">
            <TaxLine label="Federal income tax" value={monthly(breakdown.federal_income)} />
            <TaxLine label="Social Security" value={monthly(breakdown.social_security)} />
            <TaxLine label="Medicare" value={monthly(breakdown.medicare)} />
            {breakdown.state && (
              <TaxLine
                label={`State income tax (${breakdown.state})`}
                value={monthly(breakdown.state_income)}
              />
            )}
            <div className="tax-line tax-override-line">
              <span>Tax override</span>
              <span className="tax-override-field">
                <span className="tax-override-prefix">$</span>
                <input
                  className="text-input num tax-override-input"
                  inputMode="numeric"
                  placeholder="0"
                  value={overrideDraft}
                  disabled={updateConfig.isPending}
                  onChange={(event) => setOverrideDraft(event.target.value)}
                  onBlur={commitOverride}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") event.currentTarget.blur();
                  }}
                />
                <span className="ledger-monthly">/mo</span>
              </span>
            </div>
          </div>

          <div className="panel-total">
            <span>Monthly taxes · {formatPercent(effectiveRate)} effective</span>
            <span className="num panel-total-value">{formatCurrency(monthlyTotal)}</span>
          </div>
        </>
      )}
    </CollapsiblePanel>
  );
}

function TaxLine({ label, value }: { label: string; value: string }) {
  return (
    <div className="tax-line">
      <span>{label}</span>
      <span className="num ledger-monthly">{value}</span>
    </div>
  );
}
