export default function StrategyOptions({ options = [], bestKey }) {
  return (
    <div className="options-grid">
      {options.map(o => {
        const isBest = o.key === bestKey;
        return (
          <div className="panel opt-card" key={o.key} style={isBest ? { borderColor: 'rgba(232,16,31,0.5)' } : {}}>
            <h4 style={{ color: isBest ? '#e8101f' : '#f3f4f6' }}>{o.label} {isBest ? '★' : ''}</h4>
            <div className="opt-row"><span>Projected time (8 laps)</span><b>{o.time.toFixed(2)}s</b></div>
            <div className="opt-row"><span>Delta vs best</span><b>{(o.time - options.find(x => x.key === bestKey).time).toFixed(2)}s</b></div>
            <div className="opt-row"><span>Pit stop required</span><b>{o.key === 'stay' ? 'No' : 'Yes'}</b></div>
          </div>
        );
      })}
    </div>
  );
}
