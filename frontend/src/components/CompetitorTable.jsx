export default function CompetitorTable({ competitors = [] }) {
  return (
    <table className="comp-table">
      <thead>
        <tr>
          <th>Car</th><th>Driver</th><th>Pos</th><th>Tyre</th><th>Age</th>
          <th>Last Lap</th><th>Gap</th><th>Trend</th><th>Undercut</th>
        </tr>
      </thead>
      <tbody>
        {competitors.map(c => (
          <tr key={c.car} className={`${c.me ? 'me' : ''} ${c.undercutRisk === 'CRITICAL' ? 'crit' : ''}`}>
            <td><b>{c.car}</b></td>
            <td>{c.name}{c.me ? ' (You)' : ''}</td>
            <td>P{c.position}</td>
            <td style={{ color: c.compoundColor }}>{c.compoundLabel}</td>
            <td>{c.tyreAge}</td>
            <td>{c.lastLap.toFixed(3)}s</td>
            <td>{c.gap === 0 ? '—' : `${c.gap > 0 ? '+' : ''}${c.gap.toFixed(1)}s`}</td>
            <td className={c.trend === 'up' ? 'trend-up' : 'trend-down'}>{c.trend === 'up' ? '▲ up' : '▼ down'}</td>
            <td><span className={`badge ${c.undercutRisk.toLowerCase()}`}>{c.undercutRisk}</span></td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
