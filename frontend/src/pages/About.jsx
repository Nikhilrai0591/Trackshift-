export default function About() {
  return (
    <section className="page">
      <div className="section-head">
        <h2>About TrackShift</h2>
        <p>What's under the hood.</p>
      </div>
      <div className="about-grid">
        <div>
          <p><b style={{ color: 'var(--white)' }}>TrackShift</b> is a hackathon project built around one problem: a slower lap doesn't automatically mean tyre degradation. Fuel burn, traffic, track evolution and driver variation all move lap times too — the Tyre Intelligence module isolates the tyre-attributable portion from all of that, with a confidence score attached to every estimate.</p>
          <p>The app has two modules sharing one FastAPI backend and one React frontend:</p>
          <p><b style={{ color: 'var(--white)' }}>Tyre Intelligence</b> (Overview, Degradation Analysis, Lap Forensics, Strategy Simulator, Race Engineer) — the hackathon problem-statement feature, built on a mock practice-session dataset with a documented analytics pipeline: fuel effect → traffic penalty → lap validity → track evolution → corrected lap time → fitted degradation curve → remaining life → pit-window recommendation.</p>
          <p><b style={{ color: 'var(--white)' }}>Race Ops</b> (Live Race, Telemetry, Competitors, legacy Tyre Analytics, legacy Race Sim) — the original live-race strategy simulator this project started as, kept intact and accessible from the nav.</p>
          <p>Everything runs in <b>SIMULATION MODE</b>. No real F1 telemetry, driver, or team data is used anywhere in this app.</p>
          <div className="tech-pills">
            <span className="tech-pill">FastAPI backend</span>
            <span className="tech-pill">React + Vite</span>
            <span className="tech-pill">Statistical degradation fitting</span>
            <span className="tech-pill">Deterministic Race Engineer (no LLM)</span>
            <span className="tech-pill">Monte Carlo Simulation</span>
            <span className="tech-pill">Canvas Particle Background</span>
            <span className="tech-pill">Chart.js</span>
          </div>
        </div>
        <div>
          <div className="panel" style={{ padding: 22 }}>
            <h3>Architecture</h3>
            <p style={{ color: 'var(--muted)', fontSize: 13, lineHeight: 2 }}>
              React SPA (Vite) → REST calls → FastAPI service. The Tyre Intelligence module
              (<code>mock_data.py</code> → <code>tyre_analytics.py</code> → <code>tyre_intel_api.py</code>)
              is fully separated from the original race-strategy engine (<code>engine.py</code>) —
              they're mounted on the same FastAPI app but share no state.
            </p>
          </div>
          <div className="disclaimer">
            TrackShift is an independent hackathon project created for demonstration purposes only. It is not affiliated with, endorsed by, or associated with Formula 1®, the FIA, or any competing team. All driver names, team names, telemetry and session data are fictional or procedurally simulated.
          </div>
        </div>
      </div>
    </section>
  );
}
