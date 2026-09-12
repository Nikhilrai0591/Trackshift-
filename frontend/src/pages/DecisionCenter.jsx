import { useEffect, useState } from 'react';
import { tyreIntelApi } from '../api';
import StintPicker from '../components/StintPicker';
import ErrorBanner from '../components/ErrorBanner';

function pct(v) { return `${Math.round(v || 0)}%`; }
function num(v, d = 2) { return Number(v || 0).toFixed(d); }

export default function DecisionCenter() {
  const [stintsData, setStintsData] = useState(null);
  const [stintId, setStintId] = useState(null);
  const [budget, setBudget] = useState(100);
  const [decision, setDecision] = useState(null);
  const [assumptions, setAssumptions] = useState(null);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const load = async () => {
    try {
      const [stints, model] = await Promise.all([tyreIntelApi.getStints(), tyreIntelApi.getModelAssumptions()]);
      setStintsData(stints); setAssumptions(model); setError('');
      const active = stintId || stints.defaultStintId;
      if (active) {
        const result = await tyreIntelApi.getDecisionValue(active, budget);
        setDecision(result);
      }
    } catch (e) { setError(e?.response?.data?.detail || 'Could not load Decision Center.'); }
  };

  useEffect(() => { load(); }, []);
  useEffect(() => {
    if (!stintId || !stintsData) return;
    tyreIntelApi.getDecisionValue(stintId, budget).then(setDecision).catch(e => setError(e?.response?.data?.detail || 'Decision calculation failed.'));
  }, [stintId, budget]);

  const activeStint = (stintsData?.stints || []).find(s => s.stintId === (stintId || stintsData?.defaultStintId));

  async function handleUpload() {
    if (!file) return;
    setUploading(true); setError(''); setMessage('');
    try {
      const result = await tyreIntelApi.uploadSession(file);
      setMessage(`Loaded ${result.lapCount} laps across ${result.stintCount} stints from ${result.filename}.`);
      setStintId(result.stints[0]);
      await load();
    } catch (e) { setError(e?.response?.data?.detail || 'Upload failed.'); }
    finally { setUploading(false); }
  }

  async function handleDemo() {
    await tyreIntelApi.useDemoSession(); setMessage('Returned to the synthetic demonstration session.'); setStintId(null); await load();
  }

  return (
    <section className="page">
      <div className="eyebrow" style={{ color: 'var(--cyan)' }}>DECISION INTELLIGENCE</div>
      <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(24px,4vw,38px)', marginBottom: 8 }}>Spend resources only when they can change the decision.</h1>
      <p style={{ color: 'var(--muted)', maxWidth: 760, lineHeight: 1.6 }}>
        TrackShift combines tyre degradation, confidence and strategy sensitivity to estimate whether another analysis or test is worth its normalized Resource Credit cost. It is a decision layer, not a replacement for a team's existing simulator.
      </p>

      {error && <ErrorBanner message={error} />}
      {message && <div className="panel" style={{ padding: 12, marginTop: 16, color: 'var(--green)' }}>✓ {message}</div>}

      <div className="section-head"><h2>Data source</h2><p>Use the built-in simulation or upload a session with the documented CSV schema.</p></div>
      <div className="panel upload-panel">
        <div className="upload-row">
          <div className="field" style={{ flex: 1 }}><label>Telemetry CSV</label><input type="file" accept=".csv,text/csv" onChange={e => setFile(e.target.files?.[0] || null)} /></div>
          <button className="btn btn-primary btn-sm" disabled={!file || uploading} onClick={handleUpload}>{uploading ? 'Processing…' : 'Analyze CSV'}</button>
          <button className="btn btn-ghost btn-sm" onClick={handleDemo}>Use Demo Data</button>
        </div>
        <div className="sim-note">Required columns: lapNumber, tyreAge, lapTime. Optional: compound, stintId, driver, fuelLoad, trafficScore, sector1–3, flagStatus, pitLap, temperatures.</div>
      </div>

      <div className="filter-bar">
        <StintPicker stints={stintsData?.stints || []} value={stintId || stintsData?.defaultStintId} onChange={setStintId} label="Decision context" />
        <div className="field" style={{ width: 220 }}><label>Resource budget</label><input type="range" min="0" max="250" step="5" value={budget} onChange={e => setBudget(Number(e.target.value))} /><div className="rangeval">{budget} credits</div></div>
      </div>

      {decision && !decision.insufficientData && (
        <>
          <div className="decision-hero panel">
            <div>
              <div className="tag">CURRENT DECISION CONTEXT</div>
              <h2>{activeStint?.driverName || decision.compound} · {decision.compound}</h2>
              <p>Degradation <b>{num(decision.modelEvidence?.degradationRate, 3)} s/lap</b> · {decision.modelEvidence?.validLapCount}/{decision.modelEvidence?.totalLapCount} clean laps</p>
            </div>
            <div className="decision-reco">
              <div className="lbl">RECOMMENDATION</div>
              <div className={decision.recommendation.action === 'save_resources' ? 'reco-save' : 'reco-run'}>{decision.recommendation.label}</div>
              <div className="sub">{decision.recommendation.reason}</div>
            </div>
          </div>

          <div className="kpi-grid">
            <div className="panel kpi-card"><div className="l">MODEL CONFIDENCE</div><div className="v" style={{ color: decision.confidence >= 70 ? 'var(--green)' : 'var(--amber)' }}>{pct(decision.confidence)}</div><div className="sub">based on valid observations</div></div>
            <div className="panel kpi-card"><div className="l">DECISION SENSITIVITY</div><div className="v" style={{ color: decision.decisionSensitivity.label === 'HIGH' ? 'var(--red-2)' : 'var(--cyan)' }}>{decision.decisionSensitivity.label}</div><div className="sub">score {decision.decisionSensitivity.score}/100</div></div>
            <div className="panel kpi-card"><div className="l">BASE RISK</div><div className="v">{num(decision.baseRiskSeconds, 3)}s</div><div className="sub">performance-equivalent uncertainty</div></div>
            <div className="panel kpi-card"><div className="l">BUDGET</div><div className="v">{budget}</div><div className="sub">normalized Resource Credits</div></div>
          </div>

          <div className="section-head"><h2>Should we collect more information?</h2><p>Higher value means the action has a better chance of changing an uncertain decision.</p></div>
          <div className="decision-table panel">
            <div className="decision-table-head"><span>ACTION</span><span>COST</span><span>EXPECTED VALUE</span><span>NET VALUE</span><span>ROI</span></div>
            {decision.actions.map(a => (
              <div className="decision-row" key={a.key}>
                <div><b>{a.label}</b><small>{a.projectedConfidence}% projected confidence · {a.affordable ? 'affordable' : 'over budget'}</small></div>
                <span>{num(a.cost)}</span><span>{num(a.expectedValue, 3)}</span><span className={a.netValue > 0 ? 'positive' : 'negative'}>{a.netValue > 0 ? '+' : ''}{num(a.netValue, 3)}</span><span>{num(a.roi, 2)}×</span>
              </div>
            ))}
          </div>

          <div className="section-head"><h2>Engineering assumptions</h2><p>Transparent defaults for the prototype; calibrate these with team data before production use.</p></div>
          <div className="assumption-grid">
            {(assumptions?.assumptions || []).map(a => <div className="panel assumption" key={a.name}><div className="l">{a.name}</div><div className="v">{a.value} <span>{a.unit}</span></div><div className="sub">{a.type}</div></div>)}
          </div>
        </>
      )}
      {decision?.insufficientData && <div className="panel" style={{ padding: 24 }}>Not enough valid data to calculate decision value: {decision.message}</div>}
    </section>
  );
}
