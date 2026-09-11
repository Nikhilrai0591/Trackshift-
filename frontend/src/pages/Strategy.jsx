import { usePolling } from '../hooks';
import api from '../api';
import AIRecommendation from '../components/AIRecommendation';
import StrategyOptions from '../components/StrategyOptions';
import FeatureImportance from '../components/FeatureImportance';
import ErrorBanner from '../components/ErrorBanner';

export default function Strategy() {
  const { data: reco, error } = usePolling(api.getStrategy, 1500);

  return (
    <section className="page">
      <ErrorBanner message={error ? 'Could not reach the TrackShift backend' : null} />

      <div className="section-head">
        <h2>AI Recommendation</h2>
        <p>Recalculated every lap from live tyre, traffic and competitor models.</p>
      </div>
      {reco ? <AIRecommendation reco={reco} /> : <div className="loading-line">Loading recommendation…</div>}

      <div className="section-head">
        <h2>Strategy Options Evaluated</h2>
        <p>Every viable window, scored against pace, traffic and tyre life.</p>
      </div>
      {reco && <StrategyOptions options={reco.options} bestKey={reco.best.key} />}

      <div className="section-head">
        <h2>Explainable AI</h2>
        <p>Why did TrackShift recommend this?</p>
      </div>
      <div className="panel" style={{ padding: 24 }}>
        {reco && (
          <>
            <FeatureImportance importance={reco.featureImportance} />
            <div className="ai-why">
              <b>WHY DID APEXAI RECOMMEND THIS?</b><br />
              Tyre wear on the current compound has reached {reco.wear.toFixed(0)}%, and Car {reco.rivalCar} is closing
              at {reco.rivalClosing.toFixed(2)}s/lap. Combined with the current track state, the model favors{' '}
              <b>{reco.action}</b> with {reco.confidence}% confidence.
            </div>
          </>
        )}
      </div>
    </section>
  );
}
