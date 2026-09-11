export default function ValidityBadge({ validity, checks = [], excluded }) {
  const color = validity >= 80 ? 'var(--green)' : validity >= 60 ? 'var(--amber)' : 'var(--red-2)';
  return (
    <div className="validity-box">
      <div className="validity-ring" style={{ borderColor: color, color }}>
        {validity}%
      </div>
      <div className="validity-checks">
        {checks.map((c, i) => (
          <div key={i} className={`chk ${c.passed ? 'pass' : 'fail'}`}>
            {c.passed ? '✓' : '✗'} {c.label}
          </div>
        ))}
        {excluded && <div className="validity-excluded-note">EXCLUDED FROM DEGRADATION MODEL</div>}
      </div>
    </div>
  );
}
