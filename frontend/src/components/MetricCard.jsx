export default function MetricCard({ label, value, valueClass = '' }) {
  return (
    <div className="panel mini-stat">
      <div className="l">{label}</div>
      <div className={`v ${valueClass}`}>{value}</div>
    </div>
  );
}
