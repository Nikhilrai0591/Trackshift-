export default function AIRecommendation({ reco }) {
  if (!reco) return null;
  const riskClass = `risk-${reco.undercutLabel.toLowerCase()}`;
  return (
    <div className="panel reco-card glow-edge">
      <div className="tag">APEXAI STRATEGY ENGINE</div>
      <div className="action">{reco.action}</div>
      <div className="compound">{reco.compound}</div>
      <div className="reco-meta">
        <div className="m"><div className="l">CONFIDENCE</div><div className="v">{reco.confidence}%</div></div>
        <div className="m"><div className="l">EXPECTED GAIN</div><div className="v green">+{reco.gain}s</div></div>
        <div className="m"><div className="l">UNDERCUT RISK</div><div className={`v ${riskClass}`}>{reco.undercutLabel}</div></div>
        <div className="m"><div className="l">REJOIN POSITION</div><div className="v cyan">{reco.rejoin}</div></div>
      </div>
      <div className="reco-reasons">
        {reco.reasons.map((r, i) => (
          <div key={i}><span className="check">✓</span>{r}</div>
        ))}
      </div>
    </div>
  );
}
