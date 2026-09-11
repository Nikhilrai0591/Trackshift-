import { usePolling } from '../hooks';
import api from '../api';
import RaceTrack from '../components/RaceTrack';
import CompetitorTable from '../components/CompetitorTable';
import ErrorBanner from '../components/ErrorBanner';

export default function Competitors() {
  const { data: state } = usePolling(api.getState, 1500);
  const { data: compData, error } = usePolling(api.getCompetitors, 1500);

  return (
    <section className="page">
      <ErrorBanner message={error ? 'Could not reach the TrackShift backend' : null} />
      <div className="section-head">
        <h2>Competitor Field</h2>
        <p>Live gaps, tyre life and undercut threat across the grid.</p>
      </div>

      <div className="panel track-wrap" style={{ marginBottom: 20 }}>
        <h3>Track Visualization</h3>
        <RaceTrack competitors={compData?.competitors || []} lap={state?.lap || 0} height={260} />
      </div>

      <div className="panel" style={{ padding: '6px 10px', overflowX: 'auto' }}>
        <CompetitorTable competitors={compData?.competitors || []} />
      </div>
    </section>
  );
}
