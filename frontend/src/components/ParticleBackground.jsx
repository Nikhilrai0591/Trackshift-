import { useEffect, useRef } from 'react';

const rnd = (a, b) => a + Math.random() * (b - a);

export default function ParticleBackground() {
  const canvasRef = useRef(null);
  const fallbackRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const fallback = fallbackRef.current;
    let ctx;
    try {
      ctx = canvas.getContext('2d');
      if (!ctx) throw new Error('no 2d context');
    } catch {
      canvas.style.display = 'none';
      if (fallback) fallback.style.display = 'block';
      return undefined;
    }

    // Some privacy-hardened browsers/extensions deliberately throw or
    // return spoofed data on getImageData (anti-fingerprinting), even with
    // no cross-origin content involved. If anything in setup throws, fall
    // back to the static gradient rather than taking the whole app down.
    try {
      return runParticleEffect(canvas, ctx, fallback);
    } catch (e) {
      console.warn('TrackShift: particle background disabled (canvas restricted):', e);
      canvas.style.display = 'none';
      if (fallback) fallback.style.display = 'block';
      return undefined;
    }
  }, []);

  return (
    <>
      <canvas id="particle-bg" ref={canvasRef}></canvas>
      <div className="bg-fallback" ref={fallbackRef} style={{ display: 'none' }}></div>
    </>
  );
}

// Returns a cleanup function, exactly like a useEffect callback would.
// Kept outside the component so the try/catch in the effect can wrap the
// entire setup (including the synchronous getImageData call) in one place.
function runParticleEffect(canvas, ctx) {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let W, H, particles = [], streaks = [];
  let rafId = null;
  let resizeTimer = null;
  const isMobile = () => window.innerWidth < 760;

  function buildCarShape() {
    const off = document.createElement('canvas');
    const ow = 1000, oh = 340;
    off.width = ow; off.height = oh;
    const octx = off.getContext('2d');
    if (!octx) throw new Error('offscreen canvas unavailable');
    octx.fillStyle = '#fff';
    octx.beginPath();
    octx.moveTo(60, 230);
    octx.bezierCurveTo(140, 150, 260, 140, 360, 150);
    octx.bezierCurveTo(430, 110, 520, 95, 610, 100);
    octx.bezierCurveTo(700, 90, 780, 110, 840, 150);
    octx.lineTo(930, 175);
    octx.lineTo(920, 200);
    octx.lineTo(830, 190);
    octx.bezierCurveTo(760, 215, 640, 225, 540, 222);
    octx.lineTo(540, 240);
    octx.lineTo(300, 240);
    octx.lineTo(300, 225);
    octx.bezierCurveTo(220, 222, 150, 232, 90, 250);
    octx.closePath();
    octx.fill();
    octx.beginPath();
    octx.arc(470, 120, 34, Math.PI * 1.05, Math.PI * 1.95);
    octx.lineWidth = 14; octx.strokeStyle = '#fff'; octx.stroke();
    octx.fillRect(20, 235, 150, 10);
    octx.fillRect(40, 222, 110, 8);
    octx.fillRect(880, 110, 18, 90);
    octx.fillRect(860, 105, 70, 12);
    [[190, 255], [760, 255]].forEach(([x, y]) => {
      octx.beginPath(); octx.arc(x, y, 52, 0, Math.PI * 2); octx.fill();
    });
    octx.fillStyle = '#000';
    [[190, 255], [760, 255]].forEach(([x, y]) => {
      octx.beginPath(); octx.arc(x, y, 26, 0, Math.PI * 2); octx.fill();
    });
    // The call most likely to throw under anti-fingerprinting protections.
    return octx.getImageData(0, 0, ow, oh);
  }
  const carImgData = buildCarShape();

  function sampleTargets(scale, offX, offY, stride) {
    const { data, width, height } = carImgData;
    const pts = [];
    for (let y = 0; y < height; y += stride) {
      for (let x = 0; x < width; x += stride) {
        const idx = (y * width + x) * 4;
        if (data[idx + 3] > 120) pts.push({ x: offX + x * scale, y: offY + y * scale });
      }
    }
    return pts;
  }

  function resize() {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
    const mobile = isMobile();
    const carW = mobile ? W * 0.95 : W * 0.62;
    const scale = carW / 1000;
    const offX = mobile ? W * 0.03 : W * 0.34;
    const offY = H * 0.30;
    const stride = mobile ? 9 : 6;
    const targets = sampleTargets(scale, offX, offY, stride);

    if (particles.length === 0) {
      particles = targets.map(t => ({
        x: rnd(0, W), y: rnd(0, H), tx: t.x, ty: t.y,
        phase: rnd(0, Math.PI * 2), speed: rnd(0.02, 0.05),
        drift: Math.random() < 0.12, driftT: rnd(0, 600), r: rnd(0.7, 1.8),
      }));
    } else {
      particles.forEach((p, i) => {
        const t = targets[i % targets.length];
        p.tx = t.x; p.ty = t.y;
      });
      if (targets.length > particles.length) {
        for (let i = particles.length; i < targets.length; i++) {
          const t = targets[i];
          particles.push({ x: rnd(0, W), y: rnd(0, H), tx: t.x, ty: t.y, phase: rnd(0, Math.PI * 2), speed: rnd(0.02, 0.05), drift: Math.random() < 0.12, driftT: rnd(0, 600), r: rnd(0.7, 1.8) });
        }
      } else {
        particles.length = targets.length;
      }
    }

    streaks = Array.from({ length: mobile ? 6 : 14 }, () => ({
      y: rnd(0, H), x: rnd(-200, W), len: rnd(80, 220), speed: rnd(1.2, 3.4), alpha: rnd(0.05, 0.18),
    }));
  }

  let t = 0;
  function frame() {
    t += 1;
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = 'rgba(2,2,3,1)'; ctx.fillRect(0, 0, W, H);

    const g = ctx.createRadialGradient(W * 0.68, H * 0.4, 0, W * 0.68, H * 0.4, W * 0.5);
    g.addColorStop(0, 'rgba(232,16,31,0.07)'); g.addColorStop(1, 'transparent');
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);

    streaks.forEach(s => {
      s.x += s.speed;
      if (s.x > W + s.len) s.x = -s.len;
      const grad = ctx.createLinearGradient(s.x, s.y, s.x + s.len, s.y);
      grad.addColorStop(0, 'rgba(43,227,255,0)');
      grad.addColorStop(0.5, `rgba(43,227,255,${s.alpha})`);
      grad.addColorStop(1, 'rgba(43,227,255,0)');
      ctx.strokeStyle = grad; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(s.x, s.y); ctx.lineTo(s.x + s.len, s.y); ctx.stroke();
    });

    particles.forEach(p => {
      if (p.drift) {
        p.driftT--;
        if (p.driftT < 0) p.drift = false;
        p.x += Math.sin(t * 0.01 + p.phase) * 0.6;
        p.y += Math.cos(t * 0.013 + p.phase) * 0.6;
      } else {
        p.x += (p.tx - p.x) * p.speed;
        p.y += (p.ty - p.y) * p.speed;
        if (Math.random() < 0.0006) { p.drift = true; p.driftT = rnd(60, 240); }
      }
      const wobbleX = Math.sin(t * 0.02 + p.phase) * 1.1;
      const wobbleY = Math.cos(t * 0.024 + p.phase) * 1.1;
      const nearTarget = Math.abs(p.x - p.tx) < 3 && Math.abs(p.y - p.ty) < 3;
      ctx.beginPath();
      ctx.fillStyle = nearTarget ? (Math.random() < 0.003 ? '#ff3b47' : 'rgba(255,255,255,0.85)') : 'rgba(43,227,255,0.5)';
      ctx.shadowBlur = nearTarget ? 4 : 2;
      ctx.shadowColor = nearTarget ? '#e8101f' : '#2be3ff';
      ctx.arc(p.x + wobbleX, p.y + wobbleY, p.r, 0, Math.PI * 2);
      ctx.fill();
    });
    ctx.shadowBlur = 0;

    if (!reduceMotion) rafId = requestAnimationFrame(frame);
  }

  resize();
  const onResize = () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(resize, 200); };
  window.addEventListener('resize', onResize);

  if (reduceMotion) {
    ctx.fillStyle = '#020203'; ctx.fillRect(0, 0, W, H);
    particles.forEach(p => { ctx.beginPath(); ctx.fillStyle = 'rgba(232,16,31,0.5)'; ctx.arc(p.tx, p.ty, 1.2, 0, Math.PI * 2); ctx.fill(); });
  } else {
    rafId = requestAnimationFrame(frame);
  }

  return () => {
    window.removeEventListener('resize', onResize);
    clearTimeout(resizeTimer);
    if (rafId) cancelAnimationFrame(rafId);
  };
}
