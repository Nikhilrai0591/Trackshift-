import { useState } from 'react';
import { usePolling } from '../hooks';
import { tyreIntelApi } from '../api';
import StintPicker from '../components/StintPicker';
import TelemetryChart from '../components/TelemetryChart';
import ErrorBanner from '../components/ErrorBanner';

export default function StrategySimulator() {
  const [stintId, setStintId] = useState(null);
  const [nextCompound, setNextCompound] = useState('hard');
  const [pitLoss, setPitLoss] = useState(21.5);
  const [horizon, setHorizon] = useState(10);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const { data: stintsData } = usePolling(tyreIntelApi.getStints, 0);
  const { data: meta } = usePolling(tyreIntelApi.getMeta, 0);
  const stints = stintsData?.stints || [];
  const activeStintId = stintId || stintsData?.defaultStintId;

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await tyreIntelApi.runStrategy({
        stintId: activeStintId, nextCompound, pitLossSeconds: pitLoss, horizon,
      });
      setResult(r);
    } catch {
      setError('Strategy simulation failed');
    } finally {
      setLoading(false);
    }
  };

  const costCurve = result?.pitWindow?.costCurve || [];

  return (
    <section className="page">
      <ErrorBanner message={error} />
      <div className="section-head">
        <h2>Pit-Window / Strategy Simulator</h2>
        <p>Compares staying out vs pitting now vs pitting in 3 laps, using the fitted degradation curves for each compound.</p>
      </div>

      {stints.length > 0 && (
        <div className="panel" style={{ padding: 24 }}>
          <div className="sim-config">
            <StintPicker stints={stints} value={activeStintId} onChange={setStintId} label="Current stint" />
            <div className="field">
              <label>Next Compound</label>
              <select value={nextCompound} onChange={e => setNextCompound(e.target.value)}>
                {Object.entries(meta?.compounds || {}).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
              </select>
            </div>
            <div className="field">
              <label>Pit Loss: <span className="rangeval">{pitLoss.toFixed(1)}s</span></label>
              <input type="range" min="10" max="35" step="0.5" value={pitLoss} onChange={e => setPitLoss(+e.target.value)} />
            </div>
            <div className="field">
              <label>Horizon: <span className="rangeval">{horizon} laps</span></label>
              <input type="range" min="3" max="20" value={horizon} onChange={e => setHorizon(+e.target.value)} />
            </div>
          </div>
          <div className="sim-controls" style={{ marginBottom: 0 }}>
            <button className="btn btn-primary" onClick={run} disabled={loading || !activeStintId}>
              {loading ? 'Calculating…' : 'Run Strategy Comparison'}
            </button>
          </div>
        </div>
      )}

      {result?.insufficientData && (
        <div className="panel" style={{ padding: 24, marginTop: 20 }}>
          <b>Not enough clean laps to recommend a strategy yet.</b>
          <p style={{ color: 'var(--muted)', fontSize: 13, marginTop: 8 }}>{result.message}</p>
        </div>
      )}

      {result && !result.insufficientData && (
        <>
          <div className="panel reco-card glow-edge" style={{ marginTop: 20 }}>
            <div className="tag">RECOMMENDED</div>
            <div className="action" style={{ fontSize: 'clamp(24px,4vw,38px)' }}>
              {result.options.find(o => o.recommended)?.label}
            </div>
            <p style={{ color: 'var(--muted)', fontSize: 13.5, marginTop: 14, maxWidth: 560, marginLeft: 'auto', marginRight: 'auto' }}>
              {result.pitWindow.reason}
            </p>
          </div>

          <div className="options-grid" style={{ marginTop: 20 }}>
            {result.options.map(o => (
              <div className="panel opt-card" key={o.key} style={o.recommended ? { borderColor: 'rgba(232,16,31,0.5)' } : {}}>
                <h4 style={{ color: o.recommended ? '#e8101f' : '#f3f4f6' }}>{o.label} {o.recommended ? '★' : ''}</h4>
                <div className="opt-row"><span>Projected cost</span><b>{o.projectedCost.toFixed(2)}s</b></div>
              </div>
            ))}
          </div>

          <div className="panel chart-card" style={{ marginTop: 20, padding: '20px 24px' }}>
            <h4 style={{ marginBottom: 10 }}>Projected Cost by Pit Lap</h4>
            <div style={{ height: 280 }}>
              <TelemetryChart
                labels={costCurve.map(c => `+${c.delayLaps}`)}
                datasets={[{ label: 'Projected cost (s)', color: '#2be3ff', fill: true, data: costCurve.map(c => c.projectedCost) }]}
              />
            </div>
          </div>
        </>
      )}
    </section>
  );
}
