export default function TyreCard({ tyre }) {
  const wearClass = tyre.wearLabel.toLowerCase();
  return (
    <div className="panel tyre-card">
      <div className="tyre-ring" style={{ borderColor: tyre.color, color: tyre.color }}>{tyre.code}</div>
      <h4>{tyre.label}</h4>
      <div className="tyre-line"><span>Current wear</span><b className={`wear-${wearClass}`}>{tyre.wearLabel} ({tyre.wear}%)</b></div>
      <div className="tyre-line"><span>Est. remaining life</span><b>{tyre.remainingLaps} laps</b></div>
      <div className="tyre-line"><span>Predicted lap time</span><b>{tyre.predictedLapTime.toFixed(2)}s</b></div>
    </div>
  );
}
