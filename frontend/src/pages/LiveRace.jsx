import { usePolling } from '../hooks';
import api from '../api';
import MetricCard from '../components/MetricCard';
import SafetyCarAlert from '../components/SafetyCarAlert';
import SimulationControls from '../components/SimulationControls';
import RaceTrack from '../components/RaceTrack';
import WeatherCard from '../components/WeatherCard';
import ErrorBanner from '../components/ErrorBanner';

export default function LiveRace() {
  const { data: state, error: stateErr } = usePolling(api.getState, 1000);
  const { data: compData } = usePolling(api.getCompetitors, 1500);

  const flag = state?.flag || 'green';
  const flagLabel = { green: 'GREEN FLAG', vsc: 'VIRTUAL SAFETY CAR', sc: 'SAFETY CAR', red: 'RED FLAG' }[flag];

  return (
    <section className="page">
      <ErrorBanner message={stateErr ? 'Could not reach the TrackShift backend' : null} />
      <SafetyCarAlert flag={flag} />

      <div className="race-header">
        <h1>TrackShift Live Race</h1>
        <div className={`flag-badge flag-${flag}`}>{flagLabel}</div>
      </div>

      <div className="stat-grid">
        <MetricCard label="LAP" value={state ? `${state.lap} / ${state.totalLaps}` : '—'} />
        <MetricCard label="CAR" value="16" valueClass="cyan" />
        <MetricCard label="POSITION" value={state ? `P${state.position}` : '—'} valueClass="red" />
        <MetricCard label="CURRENT TYRE" value={state?.compoundLabel || '—'} />
        <MetricCard label="TYRE AGE" value={state ? `${state.tyreAge} LAPS` : '—'} />
        <MetricCard label="CURRENT LAP TIME" value={state ? `${state.lapTime.toFixed(3)}s` : '—'} valueClass="cyan" />
      </div>

      <SimulationControls
        running={!!state?.running}
        speed={state?.speed || 1}
        onStart={() => api.start()}
        onPause={() => api.pause()}
        onReset={() => api.reset()}
        onSpeedChange={(s) => api.setSpeed(s)}
        extra={<button className="btn btn-ghost btn-sm" onClick={() => api.triggerSafetyCar()}>⚠ Trigger Safety Car</button>}
      />

      <div className="two-col">
        <div className="panel track-wrap">
          <h3>Track Position</h3>
          <RaceTrack competitors={compData?.competitors || []} lap={state?.lap || 0} height={320} />
        </div>
        <div className="panel track-wrap">
          <h3>Current Delta &amp; Weather</h3>
          <div className="mini-stat" style={{ padding: '0 0 16px' }}>
            <div className="l">DELTA TO CAR AHEAD</div>
            <div className="v red">{state ? `${state.delta >= 0 ? '+' : ''}${state.delta.toFixed(3)}s` : '—'}</div>
          </div>
          <WeatherCard weather={state?.weather} />
        </div>
      </div>
    </section>
  );
}
