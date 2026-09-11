import { useState, useEffect } from 'react';
import { usePolling } from '../hooks';
import { tyreIntelApi } from '../api';
import StintPicker from '../components/StintPicker';
import WaterfallChart from '../components/WaterfallChart';
import ValidityBadge from '../components/ValidityBadge';
import ErrorBanner from '../components/ErrorBanner';

export default function LapForensics() {
  const [stintId, setStintId] = useState(null);
  const [lapNumber, setLapNumber] = useState(null);
  const { data: stintsData } = usePolling(tyreIntelApi.getStints, 0);

  const stints = stintsData?.stints || [];
  const activeStintId = stintId || stintsData?.defaultStintId;
  const activeStint = stints.find(s => s.stintId === activeStintId);

  const { data: lapsData } = usePolling(() => tyreIntelApi.getLaps(activeStintId), 0, [activeStintId]);

  useEffect(() => {
    if (lapsData?.laps?.length && !lapNumber) {
      // default to the last lap — usually the most interesting one to explain
      setLapNumber(lapsData.laps[lapsData.laps.length - 1].lapNumber);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lapsData]);

  const { data: forensics, error } = usePolling(
    () => activeStint && lapNumber ? tyreIntelApi.getLapForensics(activeStint.driver, lapNumber) : Promise.resolve(null),
    0, [activeStint?.driver, lapNumber],
  );

  return (
    <section className="page">
      <ErrorBanner message={error ? 'Could not reach the TrackShift backend' : null} />
      <div className="section-head">
        <h2>Lap Forensics</h2>
        <p>Select a lap — TrackShift explains why it was slower or faster than the stint baseline.</p>
      </div>

      {stints.length > 0 && (
        <div className="filter-bar">
          <StintPicker stints={stints} value={activeStintId} onChange={(v) => { setStintId(v); setLapNumber(null); }} />
        </div>
      )}

      {lapsData?.laps && (
        <div className="lap-picker">
          {lapsData.laps.map(l => (
            <div
              key={l.lapNumber}
              className={`lap-chip ${l.excluded ? 'excluded' : ''} ${lapNumber === l.lapNumber ? 'active' : ''}`}
              onClick={() => setLapNumber(l.lapNumber)}
            >
              Lap {l.lapNumber}
            </div>
          ))}
        </div>
      )}

      {forensics && (
        <>
          <div className="panel" style={{ padding: 28, marginTop: 10 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', flexWrap: 'wrap', gap: 10 }}>
              <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 22, color: 'var(--white)' }}>
                LAP {forensics.lapNumber}
              </h3>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 800, color: forensics.rawDelta >= 0 ? 'var(--red-2)' : 'var(--green)' }}>
                {forensics.rawDelta >= 0 ? '+' : ''}{forensics.rawDelta.toFixed(2)}s vs baseline
              </div>
            </div>

            <WaterfallChart contributions={forensics.contributions} />

            <div className="waterfall-primary">
              <b>PRIMARY CAUSE: {forensics.primaryCause}</b>
            </div>
          </div>

          <div className="section-head"><h2>Lap Validity</h2><p>Why this lap was or wasn't trusted for degradation analysis.</p></div>
          <div className="panel" style={{ padding: 24 }}>
            <ValidityBadge
              validity={forensics.lapValidity}
              excluded={forensics.excluded}
              checks={lapsData?.laps?.find(l => l.lapNumber === forensics.lapNumber)?.checks || []}
            />
          </div>
        </>
      )}
    </section>
  );
}
