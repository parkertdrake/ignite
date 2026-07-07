const wholeDollars = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

/** Format a dollar amount with no cents, e.g. 20766 -> "$20,766". */
export function formatCurrency(amount: number): string {
  return wholeDollars.format(amount);
}
