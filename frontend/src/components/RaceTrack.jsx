import { useEffect, useRef } from 'react';

export default function RaceTrack({ competitors = [], lap = 0, height = 300 }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = (canvas.width = canvas.clientWidth);
    const h = (canvas.height = height);
    ctx.clearRect(0, 0, w, h);
    const cx = w / 2, cy = h / 2, rx = w * 0.42, ry = h * 0.36;

    ctx.strokeStyle = 'rgba(255,255,255,0.12)'; ctx.lineWidth = 22;
    ctx.beginPath(); ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2); ctx.stroke();

    ctx.strokeStyle = 'rgba(255,255,255,0.03)'; ctx.lineWidth = 1; ctx.setLineDash([4, 6]);
    ctx.beginPath(); ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2); ctx.stroke();
    ctx.setLineDash([]);

    const total = competitors.length || 1;
    competitors.forEach((c) => {
      const t = ((c.position - 1) / total) * Math.PI * 2 - Math.PI / 2 + lap * 0.03;
      const x = cx + rx * Math.cos(t);
      const y = cy + ry * Math.sin(t);
      ctx.beginPath();
      ctx.fillStyle = c.me ? '#2be3ff' : c.undercutRisk === 'CRITICAL' || c.undercutRisk === 'HIGH' ? '#e8101f' : 'rgba(255,255,255,0.55)';
      ctx.shadowBlur = c.me || c.undercutRisk === 'CRITICAL' ? 10 : 0;
      ctx.shadowColor = ctx.fillStyle;
      ctx.arc(x, y, c.me ? 7 : 5.5, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;
      ctx.fillStyle = '#c9cbd1';
      ctx.font = '11px Titillium Web';
      ctx.textAlign = 'center';
      ctx.fillText(c.car, x, y - 11);
    });
  }, [competitors, lap, height]);

  return (
    <div style={{ width: '100%' }}>
      <canvas ref={canvasRef} style={{ width: '100%', height }} />
    </div>
  );
}
