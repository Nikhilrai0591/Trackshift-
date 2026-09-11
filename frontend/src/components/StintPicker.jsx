export default function StintPicker({ stints = [], value, onChange, label = 'Stint' }) {
  return (
    <div className="field">
      <label>{label}</label>
      <select value={value || ''} onChange={e => onChange(e.target.value)}>
        {stints.map(s => (
          <option key={s.stintId} value={s.stintId}>
            {s.driverName || s.driver} — {s.compoundLabel} ({s.stintLength} laps)
          </option>
        ))}
      </select>
    </div>
  );
}
