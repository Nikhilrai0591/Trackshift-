const LABELS = {
  tyreDegradation: 'Tyre Degradation',
  traffic: 'Traffic',
  fuelEffect: 'Fuel Effect',
  trackEvolution: 'Track Evolution',
  driverVariation: 'Driver Variation',
};

export default function WaterfallChart({ contributions = {} }) {
  const entries = Object.entries(contributions);
  const maxAbs = Math.max(0.05, ...entries.map(([, v]) => Math.abs(v)));

  return (
    <div className="waterfall">
      {entries.map(([key, value]) => {
        const pct = Math.min(100, (Math.abs(value) / maxAbs) * 48); // half-track max
        const isPos = value >= 0;
        return (
          <div className="waterfall-row" key={key}>
            <div className="label">{LABELS[key] || key}</div>
            <div className="waterfall-track">
              <div className="waterfall-center-line"></div>
              <div className={`waterfall-fill ${isPos ? 'pos' : 'neg'}`} style={{ width: `${pct}%` }}></div>
            </div>
            <div className={`val ${isPos ? 'pos' : 'neg'}`}>{isPos ? '+' : ''}{value.toFixed(2)}s</div>
          </div>
        );
      })}
    </div>
  );
}
