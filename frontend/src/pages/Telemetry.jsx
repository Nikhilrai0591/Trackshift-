import { usePolling } from '../hooks';
import api from '../api';
import TelemetryChart from '../components/TelemetryChart';
import SimulationControls from '../components/SimulationControls';
import ErrorBanner from '../components/ErrorBanner';

export default function Telemetry() {
  const { data: state } = usePolling(api.getState, 1000);
  const { data: tele, error } = usePolling(api.getTelemetry, 500);

  const points = tele?.points || [];
  const labels = points.map(p => p.t.toFixed(1));
  const latest = tele?.latest;

  return (
    <section className="page">
      <ErrorBanner message={error ? 'Could not reach the TrackShift backend' : null} />
      <div className="section-head">
        <h2>Live Telemetry</h2>
        <p>Simulated car sensor data, streamed from the backend every tick.</p>
      </div>

      <SimulationControls
        running={!!state?.running}
        speed={state?.speed || 1}
        onStart={() => api.start()}
        onPause={() => api.pause()}
        onReset={() => api.reset()}
        onSpeedChange={(s) => api.setSpeed(s)}
      />

      <div className="chart-grid">
        <div className="panel chart-card">
          <div className="chd"><h4>Speed (km/h)</h4><span className="live-val">{latest?.speed ?? '—'}</span></div>
          <TelemetryChart labels={labels} datasets={[{ label: 'Speed', color: '#2be3ff', fill: true, data: points.map(p => p.speed) }]} />
        </div>
        <div className="panel chart-card">
          <div className="chd"><h4>Throttle / Brake (%)</h4><span className="live-val">{latest ? `${latest.throttle} / ${latest.brake}` : '—'}</span></div>
          <TelemetryChart labels={labels} showLegend datasets={[
            { label: 'Throttle', color: '#28e07f', data: points.map(p => p.throttle) },
            { label: 'Brake', color: '#e8101f', data: points.map(p => p.brake) },
          ]} />
        </div>
        <div className="panel chart-card">
          <div className="chd"><h4>Engine RPM</h4><span className="live-val">{latest ? latest.rpm.toLocaleString() : '—'}</span></div>
          <TelemetryChart labels={labels} datasets={[{ label: 'RPM', color: '#ffb648', fill: true, data: points.map(p => p.rpm) }]} />
        </div>
        <div className="panel chart-card">
          <div className="chd"><h4>Tyre Temperature (°C)</h4><span className="live-val">{latest?.tyreTemp ?? '—'}</span></div>
          <TelemetryChart labels={labels} datasets={[{ label: 'Tyre Temp', color: '#e8101f', fill: true, data: points.map(p => p.tyreTemp) }]} />
        </div>
        <div className="panel chart-card">
          <div className="chd"><h4>Lap Delta (s)</h4><span className="live-val">{latest ? (latest.lapDelta >= 0 ? '+' : '') + latest.lapDelta : '—'}</span></div>
          <TelemetryChart labels={labels} datasets={[{ label: 'Lap Delta', color: '#2be3ff', data: points.map(p => p.lapDelta) }]} />
        </div>
        <div className="panel chart-card">
          <div className="chd"><h4>Sector Time (s)</h4><span className="live-val">{latest?.sector ?? '—'}</span></div>
          <TelemetryChart labels={labels} datasets={[{ label: 'Sector', color: '#f3f4f6', data: points.map(p => p.sector) }]} />
        </div>
      </div>
    </section>
  );
}
