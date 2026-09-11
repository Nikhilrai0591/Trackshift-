import { useState, useRef } from 'react';
import api from '../api';
import MonteCarloChart from '../components/MonteCarloChart';
import ErrorBanner from '../components/ErrorBanner';

export default function Simulator() {
  const [tyre, setTyre] = useState('medium');
  const [position, setPosition] = useState(2);
  const [weather, setWeather] = useState('dry');
  const [scProb, setScProb] = useState(15);
  const [progress, setProgress] = useState(0);
  const [running, setRunning] = useState(false);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);
  const progressTimer = useRef(null);

  const run = async () => {
    setError(null);
    setRunning(true);
    setProgress(6);
    clearInterval(progressTimer.current);
    progressTimer.current = setInterval(() => {
      setProgress(p => (p < 88 ? p + rndStep() : p));
    }, 60);

    try {
      const result = await api.simulate({
        tyre, position, weather, scProbability: scProb / 100, iterations: 1000,
      });
      setProgress(100);
      setTimeout(() => {
        setSummary(result.summary);
        setRunning(false);
        clearInterval(progressTimer.current);
      }, 250);
    } catch {
      setError('Simulation request failed');
      setRunning(false);
      clearInterval(progressTimer.current);
    }
  };

  const reset = () => { setSummary(null); setProgress(0); setError(null); };

  return (
    <section className="page">
      <ErrorBanner message={error} />
      <div className="section-head">
        <h2>Monte Carlo Strategy Simulator</h2>
        <p>Runs 1,000 randomized race simulations per strategy option, powered by the FastAPI backend.</p>
      </div>

      <div className="panel" style={{ padding: 24 }}>
        <div className="sim-config">
          <div className="field">
            <label>Starting Tyre</label>
            <select value={tyre} onChange={e => setTyre(e.target.value)}>
              <option value="soft">Soft</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
          </div>
          <div className="field">
            <label>Starting Position</label>
            <select value={position} onChange={e => setPosition(+e.target.value)}>
              {[1, 2, 3, 4, 5].map(p => <option key={p} value={p}>P{p}</option>)}
            </select>
          </div>
          <div className="field">
            <label>Weather</label>
            <select value={weather} onChange={e => setWeather(e.target.value)}>
              <option value="dry">Dry</option>
              <option value="changeable">Changeable</option>
              <option value="wet">Wet</option>
            </select>
          </div>
          <div className="field">
            <label>Safety Car Probability: <span className="rangeval">{scProb}%</span></label>
            <input type="range" min="0" max="60" value={scProb} onChange={e => setScProb(+e.target.value)} />
          </div>
        </div>

        <div className="sim-controls" style={{ marginBottom: 0 }}>
          <button className="btn btn-primary" onClick={run} disabled={running}>
            {running ? 'Running…' : 'Run 1,000 Simulations'}
          </button>
          <button className="btn btn-ghost" onClick={reset}>Reset</button>
          <div className="spacer"></div>
          <span style={{ fontSize: 12, color: 'var(--muted)' }}>
            {running ? 'Running…' : summary ? 'Done — 1,000 simulations per strategy' : 'Idle'}
          </span>
        </div>
        {running && (
          <div style={{ height: 6, background: 'rgba(255,255,255,0.06)', borderRadius: 3, overflow: 'hidden', marginTop: 16 }}>
            <div style={{ height: '100%', width: `${progress}%`, background: 'linear-gradient(90deg,#2be3ff,#e8101f)', transition: 'width .1s linear' }}></div>
          </div>
        )}
      </div>

      {summary && (
        <>
          <div className="mc-grid">
            {summary.map(r => (
              <div className="panel mc-card" key={r.strategy}>
                <h4>{r.strategy}</h4>
                <div className="big">P{r.expectedPosition.toFixed(1)}</div>
                <div className="sub2">Expected finishing position</div>
                <div className="big" style={{ marginTop: 10, fontSize: 18, color: '#2be3ff' }}>{r.successProbability.toFixed(0)}%</div>
                <div className="sub2">Success probability</div>
                <div
                  className="risk-tag"
                  style={{
                    background: r.risk === 'LOW' ? 'rgba(40,224,127,0.15)' : r.risk === 'MEDIUM' ? 'rgba(255,182,72,0.15)' : 'rgba(232,16,31,0.15)',
                    color: r.risk === 'LOW' ? '#28e07f' : r.risk === 'MEDIUM' ? '#ffb648' : '#e8101f',
                  }}
                >{r.risk} RISK</div>
              </div>
            ))}
          </div>

          <div className="panel chart-card" style={{ marginTop: 20, padding: '20px 24px' }}>
            <h4 style={{ marginBottom: 10 }}>Expected Finishing Position by Strategy</h4>
            <MonteCarloChart summary={summary} />
          </div>
        </>
      )}
    </section>
  );
}

function rndStep() {
  return 2 + Math.random() * 6;
}
