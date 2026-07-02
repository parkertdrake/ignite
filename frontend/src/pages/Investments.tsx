export default function Investments() {
  return (
    <section className="page-section">
      <h2>Investments</h2>
      <p className="muted">Portfolio value, holdings, and allocation.</p>
      <div className="card-grid">
        <div className="card">
          <h3>Portfolio Value</h3>
          <p className="metric">$0</p>
        </div>
        <div className="card">
          <h3>Holdings</h3>
          <p className="metric">0</p>
        </div>
        <div className="card">
          <h3>Day Change</h3>
          <p className="metric">0.0%</p>
        </div>
      </div>
    </section>
  );
}
