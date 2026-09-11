export default function WeatherCard({ weather }) {
  if (!weather) return null;
  return (
    <div className="weather-grid" style={{ gridTemplateColumns: 'repeat(2,1fr)' }}>
      <div className="w-card" style={{ background: 'rgba(255,255,255,0.02)', borderRadius: 8 }}>
        <div className="l">TRACK TEMP</div><div className="v">{weather.trackTemp}°C</div>
      </div>
      <div className="w-card" style={{ background: 'rgba(255,255,255,0.02)', borderRadius: 8 }}>
        <div className="l">AIR TEMP</div><div className="v">{weather.airTemp}°C</div>
      </div>
      <div className="w-card" style={{ background: 'rgba(255,255,255,0.02)', borderRadius: 8 }}>
        <div className="l">RAIN PROB.</div><div className="v">{weather.rain}%</div>
      </div>
      <div className="w-card" style={{ background: 'rgba(255,255,255,0.02)', borderRadius: 8 }}>
        <div className="l">GRIP LEVEL</div><div className="v green">{weather.grip}%</div>
      </div>
    </div>
  );
}
