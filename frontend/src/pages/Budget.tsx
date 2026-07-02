export default function Budget() {
  return (
    <section className="page-section">
      <h2>Budget</h2>
      <p className="muted">Track income, expenses, and monthly cash flow.</p>
      <div className="card-grid">
        <div className="card">
          <h3>Income</h3>
          <p className="metric">$0</p>
        </div>
        <div className="card">
          <h3>Expenses</h3>
          <p className="metric">$0</p>
        </div>
        <div className="card">
          <h3>Net</h3>
          <p className="metric">$0</p>
        </div>
      </div>
    </section>
  );
}
