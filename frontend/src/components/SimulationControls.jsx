export default function SimulationControls({ running, speed, onStart, onPause, onReset, onSpeedChange, extra }) {
  return (
    <div className="sim-controls">
      <div className="seg">
        <button className={running ? 'on' : ''} onClick={onStart}>LIVE</button>
        <button className={!running ? 'on' : ''} onClick={onPause}>PAUSE</button>
        <button onClick={onReset}>RESET</button>
      </div>
      <div className="seg">
        {[1, 2, 5].map(s => (
          <button key={s} className={speed === s ? 'on' : ''} onClick={() => onSpeedChange(s)}>×{s}</button>
        ))}
      </div>
      <div className="spacer"></div>
      {extra}
    </div>
  );
}
