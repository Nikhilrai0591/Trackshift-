import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useState, useRef, useEffect } from 'react';

const PRIMARY_TABS = [
  { to: '/', label: 'Overview', end: true },
  { to: '/tyre-intelligence', label: 'Tyre Intelligence' },
  { to: '/degradation', label: 'Degradation Analysis' },
  { to: '/lap-forensics', label: 'Lap Forensics' },
  { to: '/strategy-simulator', label: 'Strategy Simulator' },
  { to: '/race-engineer', label: 'Race Engineer' },
];

const RACE_OPS_TABS = [
  { to: '/live', label: 'Live Race' },
  { to: '/telemetry', label: 'Telemetry' },
  { to: '/competitors', label: 'Competitors' },
  { to: '/tyres', label: 'Tyre Analytics (legacy)' },
  { to: '/simulator', label: 'Race Sim (legacy)' },
  { to: '/strategy', label: 'Pit Strategy (legacy)' },
];

export default function Navbar({ apiOnline }) {
  const [open, setOpen] = useState(false);
  const [opsOpen, setOpsOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const opsRef = useRef(null);

  const opsActive = RACE_OPS_TABS.some(t => location.pathname === t.to);

  useEffect(() => {
    function onClickOutside(e) {
      if (opsRef.current && !opsRef.current.contains(e.target)) setOpsOpen(false);
    }
    document.addEventListener('mousedown', onClickOutside);
    return () => document.removeEventListener('mousedown', onClickOutside);
  }, []);

  return (
    <header className="nav">
      <a className="brand" onClick={(e) => { e.preventDefault(); navigate('/'); }} href="/">
        <svg width="30" height="30" viewBox="0 0 32 32" fill="none">
          <path d="M2 20L12 8H20L14 20H26L30 12" stroke="#e8101f" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <div className="brand-text">
          <div className="word">Track<span>Shift</span></div>
          <div className="tag">TYRE INTELLIGENCE ENGINE</div>
        </div>
      </a>

      <nav className={`tabs${open ? ' mobile-open' : ''}`}>
        {PRIMARY_TABS.map(t => (
          <NavLink key={t.to} to={t.to} end={t.end} onClick={() => setOpen(false)} className={({ isActive }) => (isActive ? 'active' : '')}>
            {t.label}
          </NavLink>
        ))}

        <div className="nav-dropdown" ref={opsRef}>
          <button
            type="button"
            className={`nav-dropdown-trigger${opsActive ? ' active' : ''}`}
            onClick={() => setOpsOpen(o => !o)}
          >
            Race Ops {opsOpen ? '▴' : '▾'}
          </button>
          {opsOpen && (
            <div className="nav-dropdown-menu">
              {RACE_OPS_TABS.map(t => (
                <NavLink
                  key={t.to} to={t.to}
                  onClick={() => { setOpsOpen(false); setOpen(false); }}
                  className={({ isActive }) => (isActive ? 'active' : '')}
                >
                  {t.label}
                </NavLink>
              ))}
            </div>
          )}
        </div>

        <NavLink to="/about" onClick={() => setOpen(false)} className={({ isActive }) => (isActive ? 'active' : '')}>About</NavLink>
      </nav>

      <div className="nav-right">
        <div className="status-pill">
          <span className={`dot ${apiOnline ? 'live' : 'off'}`}></span>
          <span>{apiOnline ? 'SIMULATION MODE — LIVE API' : 'API OFFLINE'}</span>
        </div>
        <button className="menu-btn" onClick={() => setOpen(o => !o)}>☰</button>
      </div>
    </header>
  );
}
