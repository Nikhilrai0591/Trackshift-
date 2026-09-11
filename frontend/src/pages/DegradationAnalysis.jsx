import { useState } from 'react';
import { usePolling } from '../hooks';
import { tyreIntelApi } from '../api';
import TelemetryChart from '../components/TelemetryChart';
import ErrorBanner from '../components/ErrorBanner';

const COMPOUND_COLORS = { soft: '#e8101f', medium: '#ffb648', hard: '#f3f4f6' };

export default function DegradationAnalysis() {
  const [driver, setDriver] = useState('');
  const [compound, setCompound] = useState('');

  const { data: meta } = usePolling(tyreIntelApi.getMeta, 0);
  const { data: curveData, error: curveErr } = usePolling(
    () => tyreIntelApi.getDegradationCurve({ driver: driver || undefined, compound: compound || undefined }),
    4000, [driver, compound],
  );
  const { data: compareData, error: cmpErr } = usePolling(tyreIntelApi.getCompare, 4000);

  const curves = curveData?.curves || [];
  const maxLen = Math.max(0, ...curves.map(c => c.curve.length));
  const labels = Array.from({ length: maxLen }, (_, i) => i + 1);
  const datasets = curves.map(c => ({
    label: `${c.driver} · ${c.compoundLabel}`,
    color: COMPOUND_COLORS[c.compound] || '#2be3ff',
    data: c.curve.map(p => p.correctedLoss),
  }));

  const compareRows = Object.values(compareData?.compounds || {});

  return (
    <section className="page">
      <ErrorBanner message={curveErr || cmpErr ? 'Could not reach the TrackShift backend' : null} />
      <div className="section-head">
        <h2>Degradation Analysis</h2>
        <p>Corrected lap-time loss vs tyre age, filterable by driver and compound.</p>
      </div>

      <div className="filter-bar">
        <div className="field">
          <label>Driver</label>
          <select value={driver} onChange={e => setDriver(e.target.value)}>
            <option value="">All drivers</option>
            {(meta?.drivers || []).map(d => <option key={d.code} value={d.code}>{d.name}</option>)}
          </select>
        </div>
        <div className="field">
          <label>Compound</label>
          <select value={compound} onChange={e => setCompound(e.target.value)}>
            <option value="">All compounds</option>
            {Object.entries(meta?.compounds || {}).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
          </select>
        </div>
      </div>

      {curveData?.insufficientData ? (
        <div className="panel" style={{ padding: 24 }}>
          <b>Not enough clean laps for the selected filter.</b>
          <p style={{ color: 'var(--muted)', fontSize: 13, marginTop: 8 }}>{curveData.message}</p>
        </div>
      ) : (
        <div className="panel chart-card" style={{ padding: '20px 24px' }}>
          <h4 style={{ marginBottom: 10 }}>Corrected Lap-Time Loss vs Tyre Age</h4>
          <div style={{ height: 320 }}>
            <TelemetryChart labels={labels} showLegend datasets={datasets} />
          </div>
        </div>
      )}

      {curves.length > 0 && (
        <div className="options-grid" style={{ marginTop: 20 }}>
          {curves.map(c => (
            <div className="panel opt-card" key={c.stintId}>
              <h4>{c.driver} · {c.compoundLabel}</h4>
              <div className="opt-row"><span>Degradation rate</span><b>{c.degradationRate.toFixed(3)} s/lap</b></div>
              <div className="opt-row"><span>Acceleration</span><b>{c.degradationAcceleration.toFixed(5)} s/lap²</b></div>
              <div className="opt-row"><span>Confidence</span><b>{c.confidence}%</b></div>
            </div>
          ))}
        </div>
      )}

      <div className="section-head"><h2>Compound Comparison</h2><p>Soft vs Medium vs Hard, aggregated across this session.</p></div>
      <div className="tyre-grid">
        {compareRows.map(row => row.insufficientData ? null : (
          <div className="panel tyre-card" key={row.compound}>
            <div className="tyre-ring" style={{ borderColor: COMPOUND_COLORS[row.compound], color: COMPOUND_COLORS[row.compound] }}>
              {row.compound.slice(0, 1).toUpperCase()}
            </div>
            <h4>{row.compound.toUpperCase()}</h4>
            <div className="tyre-line"><span>Initial pace</span><b>{row.initialPaceLabel}</b></div>
            <div className="tyre-line"><span>Degradation</span><b>{row.degradationLabel} ({row.degradationRate.toFixed(3)} s/lap)</b></div>
            <div className="tyre-line"><span>Expected life</span><b>{row.lifeLabel} (~{row.expectedLifeLaps} laps)</b></div>
            <div className="tyre-line"><span>Consistency (±s)</span><b>{row.consistency != null ? row.consistency.toFixed(3) : '—'}</b></div>
            <div className="tyre-line"><span>Confidence</span><b>{row.confidence}%</b></div>
          </div>
        ))}
      </div>
    </section>
  );
}
