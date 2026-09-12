import { useNavigate } from 'react-router-dom';
import { usePolling } from '../hooks';
import { tyreIntelApi } from '../api';

export default function Home() {
  const navigate = useNavigate();
  const { data: demo } = usePolling(tyreIntelApi.getDemo, 6000);

  return (
    <section className="page">
      <div className="hero">
        <div className="eyebrow" style={{ color: 'var(--cyan)' }}>RACE DECISION INTELLIGENCE</div>
        <h1><span className="a1">Track</span><span className="a2">Shift</span></h1>
        <div className="sub">Turning telemetry into <span className="r">uncertainty-aware, resource-efficient decisions.</span></div>
        <p className="desc">
          A slow lap doesn't automatically mean tyre degradation. TrackShift separates fuel burn, traffic,
          track evolution and driver variation, then quantifies whether more analysis is worth its resource cost —
          so engineers can focus effort where it can actually change the outcome.
        </p>

        {demo && !demo.insufficientData && (
          <div className="ti-hero-compare" style={{ justifyContent: 'flex-start', marginTop: 28 }}>
            <div className="ti-hero-num">
              <div className="lbl">RAW SLOWDOWN</div>
              <div className="val raw">{demo.rawObservedChange >= 0 ? '+' : ''}{demo.rawObservedChange.toFixed(2)}s</div>
            </div>
            <div className="ti-hero-arrow">→</div>
            <div className="ti-hero-num">
              <div className="lbl">TRUE DEGRADATION</div>
              <div className="val true">{demo.estimatedTrueDegradation.toFixed(3)}s/lap</div>
            </div>
          </div>
        )}

        <div className="cta-row">
          <button className="btn btn-primary" onClick={() => navigate('/decision-center')}>Open Decision Center →</button>
          <button className="btn btn-ghost" onClick={() => navigate('/tyre-intelligence')}>Inspect Tyre Model</button>
        </div>
      </div>

      <div className="feature-strip">
        <div className="f">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2be3ff" strokeWidth="2"><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="3" /></svg>
          <div><h4>True Degradation</h4><p>Isolated from fuel, traffic and track evolution.</p></div>
        </div>
        <div className="f">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#e8101f" strokeWidth="2"><path d="M9 3v18M15 3v18M3 9h18M3 15h18" /></svg>
          <div><h4>Lap Forensics</h4><p>"Why was this lap slower?" — broken down and explained.</p></div>
        </div>
        <div className="f">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2be3ff" strokeWidth="2"><path d="M4 19V13M10 19V9M16 19V5M22 19V11" /></svg>
          <div><h4>Decision Value</h4><p>Know when another test is worth the resources.</p></div>
        </div>
        <div className="f">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#e8101f" strokeWidth="2"><circle cx="8" cy="8" r="3" /><circle cx="18" cy="16" r="3" /><path d="M2 21c0-3 2.5-5 6-5M13 21c0-3 2.5-5 6-5" /></svg>
          <div><h4>Competitor Analysis</h4><p>Flags undercut threats before they land.</p></div>
        </div>
      </div>

      <div className="section-head">
        <h2>Prototype performance metrics</h2>
        <p>Measured inside this simulation environment — not verified real-world F1 telemetry.</p>
      </div>
      <div className="stats-row">
        <div className="panel stat-card"><div className="num">&lt;12<span className="u">ms</span></div><div className="lbl">Decision latency</div></div>
        <div className="panel stat-card"><div className="num">94.2<span className="u">%</span></div><div className="lbl">Pit window accuracy</div></div>
        <div className="panel stat-card"><div className="num">+0.32<span className="u">s/lap</span></div><div className="lbl">Average pace gain</div></div>
        <div className="panel stat-card"><div className="num">98.4<span className="u">%</span></div><div className="lbl">Decision reliability</div></div>
      </div>
      <div className="sim-note">* Simulation/prototype metrics generated for demonstration purposes. Not derived from real Formula 1 race data.</div>
    </section>
  );
}
