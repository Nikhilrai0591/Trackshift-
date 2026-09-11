import { useState } from 'react';
import { usePolling } from '../hooks';
import { tyreIntelApi } from '../api';
import StintPicker from '../components/StintPicker';
import ErrorBanner from '../components/ErrorBanner';

export default function TyreIntelligence() {
  const [stintId, setStintId] = useState(null);
  const { data: stintsData } = usePolling(tyreIntelApi.getStints, 0);
  const { data: overview, error: ovErr } = usePolling(() => tyreIntelApi.getOverview(stintId), 4000, [stintId]);
  const { data: deg, error: degErr } = usePolling(() => tyreIntelApi.getDegradation(stintId), 4000, [stintId]);

  const stints = stintsData?.stints || [];
  const activeStintId = stintId || stintsData?.defaultStintId;

  return (
    <section className="page">
      <ErrorBanner message={ovErr || degErr ? 'Could not reach the TrackShift backend' : null} />

      <div className="eyebrow" style={{ color: 'var(--cyan)' }}>TYRE INTELLIGENCE</div>
      <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(24px,4vw,36px)', fontWeight: 800, marginBottom: 6 }}>
        Isolating true tyre wear from fuel, traffic and track conditions
      </h1>
      <p style={{ color: 'var(--muted)', fontSize: 14, maxWidth: 640, marginBottom: 20 }}>
        A slow lap doesn't automatically mean tyre degradation. Select a stint below to see the raw slowdown
        decomposed into fuel burn, traffic, track evolution and the tyre-attributable remainder.
      </p>

      {stints.length > 0 && (
        <div className="filter-bar">
          <StintPicker stints={stints} value={activeStintId} onChange={setStintId} label="Viewing stint" />
        </div>
      )}

      {deg?.insufficientData && (
        <div className="panel" style={{ padding: 24, marginTop: 20 }}>
          <b>Not enough clean laps to estimate degradation reliably.</b>
          <p style={{ color: 'var(--muted)', fontSize: 13, marginTop: 8 }}>{deg.message}</p>
        </div>
      )}

      {deg && !deg.insufficientData && (
        <div className="panel ti-hero" style={{ marginTop: 20 }}>
          <div className="tag">OBSERVED SLOWDOWN ≠ TYRE DEGRADATION</div>
          <div className="ti-hero-compare">
            <div className="ti-hero-num">
              <div className="lbl">RAW SLOWDOWN</div>
              <div className="val raw">{deg.rawObservedChange >= 0 ? '+' : ''}{deg.rawObservedChange.toFixed(2)}s</div>
            </div>
            <div className="ti-hero-arrow">→</div>
            <div className="ti-hero-num">
              <div className="lbl">TRUE DEGRADATION (est.)</div>
              <div className="val true">{deg.estimatedTrueDegradation >= 0 ? '+' : ''}{deg.estimatedTrueDegradation.toFixed(3)}s/lap</div>
            </div>
          </div>
          <p className="ti-hero-sub">
            Estimated at {deg.confidence}% confidence from {deg.validLapCount} of {deg.totalLapCount} laps in this
            stint ({deg.excludedLapCount} excluded — traffic, flags, pit activity, or abnormal sectors).
          </p>

          <div className="ti-breakdown">
            <div className="b">
              <div className="l">FUEL EFFECT</div>
              <div className={`v ${deg.fuelEffect >= 0 ? 'pos' : 'neg'}`}>{deg.fuelEffect >= 0 ? '+' : ''}{deg.fuelEffect.toFixed(2)}s/lap</div>
            </div>
            <div className="b">
              <div className="l">TRAFFIC EFFECT</div>
              <div className={`v ${deg.trafficEffect >= 0 ? 'pos' : 'neg'}`}>{deg.trafficEffect >= 0 ? '+' : ''}{deg.trafficEffect.toFixed(2)}s/lap</div>
            </div>
            <div className="b">
              <div className="l">TRACK EVOLUTION</div>
              <div className={`v ${deg.trackEvolutionEffect >= 0 ? 'pos' : 'neg'}`}>{deg.trackEvolutionEffect >= 0 ? '+' : ''}{deg.trackEvolutionEffect.toFixed(2)}s/lap</div>
            </div>
            <div className="b">
              <div className="l">EST. TRUE DEGRADATION</div>
              <div className="v pos">{deg.estimatedTrueDegradation >= 0 ? '+' : ''}{deg.estimatedTrueDegradation.toFixed(3)}s/lap</div>
            </div>
          </div>
        </div>
      )}

      {overview && !overview.insufficientData && (
        <>
          <div className="section-head"><h2>Current Tyre</h2><p>Live KPIs for the selected stint.</p></div>
          <div className="kpi-grid">
            <div className="panel kpi-card"><div className="l">COMPOUND</div><div className="v">{overview.compoundLabel}</div><div className="sub">Car {overview.car} · {overview.driver}</div></div>
            <div className="panel kpi-card"><div className="l">TYRE AGE</div><div className="v">{overview.tyreAge} laps</div></div>
            <div className="panel kpi-card"><div className="l">DEGRADATION RATE</div><div className="v" style={{ color: 'var(--cyan)' }}>{overview.estimatedDegradationRate.toFixed(3)} s/lap</div><div className="sub">accel {overview.degradationAcceleration.toFixed(5)} s/lap²</div></div>
            <div className="panel kpi-card"><div className="l">CONFIDENCE</div><div className="v" style={{ color: overview.confidence >= 70 ? 'var(--green)' : 'var(--amber)' }}>{overview.confidence}%</div></div>
            <div className="panel kpi-card"><div className="l">REMAINING LIFE</div><div className="v">{overview.estimatedRemainingLife ?? '—'} laps</div><div className="sub">estimated</div></div>
            <div className="panel kpi-card"><div className="l">RECOMMENDED PIT</div><div className="v" style={{ color: 'var(--red-2)', fontSize: 16 }}>{overview.recommendedPitWindow || '—'}</div></div>
            <div className="panel kpi-card"><div className="l">NEXT COMPOUND</div><div className="v">{overview.recommendedNextCompound ? overview.recommendedNextCompound.toUpperCase() : '—'}</div><div className="sub">lowest degradation available</div></div>
            <div className="panel kpi-card"><div className="l">CLEAN LAPS USED</div><div className="v">{overview.validLapCount}/{overview.totalLapCount}</div></div>
          </div>
        </>
      )}
    </section>
  );
}
