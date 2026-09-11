import { usePolling } from '../hooks';
import api from '../api';
import TyreCard from '../components/TyreCard';
import TelemetryChart from '../components/TelemetryChart';
import ErrorBanner from '../components/ErrorBanner';

export default function Tyres() {
  const { data, error } = usePolling(api.getTyres, 2000);
  const tyres = data?.tyres || [];
  const curve = data?.degradationCurve;

  const labels = curve ? Array.from({ length: curve.soft.data.length }, (_, i) => i + 1) : [];
  const datasets = curve
    ? Object.values(curve).map(c => ({ label: c.label, color: c.color, data: c.data }))
    : [];

  return (
    <section className="page">
      <ErrorBanner message={error ? 'Could not reach the TrackShift backend' : null} />
      <div className="section-head">
        <h2>Tyre Intelligence</h2>
        <p>Degradation modeling across all three dry compounds.</p>
      </div>

      <div className="tyre-grid">
        {tyres.map(t => <TyreCard key={t.key} tyre={t} />)}
      </div>

      <div className="panel chart-card" style={{ marginTop: 20, padding: '20px 24px' }}>
        <h4 style={{ marginBottom: 10 }}>Degradation Curve — Predicted Lap Time vs Stint Length</h4>
        {curve && <TelemetryChart labels={labels} showLegend datasets={datasets} />}
      </div>
    </section>
  );
}
