import { Routes, Route } from 'react-router-dom';
import { useEffect, useState } from 'react';
import Navbar from './components/Navbar';
import ParticleBackground from './components/ParticleBackground';
import Home from './pages/Home';
import TyreIntelligence from './pages/TyreIntelligence';
import DegradationAnalysis from './pages/DegradationAnalysis';
import LapForensics from './pages/LapForensics';
import StrategySimulator from './pages/StrategySimulator';
import RaceEngineer from './pages/RaceEngineer';
import LiveRace from './pages/LiveRace';
import Strategy from './pages/Strategy';
import Telemetry from './pages/Telemetry';
import Competitors from './pages/Competitors';
import Tyres from './pages/Tyres';
import Simulator from './pages/Simulator';
import About from './pages/About';
import DecisionCenter from './pages/DecisionCenter';
import api from './api';

export default function App() {
  const [apiOnline, setApiOnline] = useState(true);

  useEffect(() => {
    let mounted = true;
    const check = () => api.getState().then(
      () => mounted && setApiOnline(true),
      () => mounted && setApiOnline(false),
    );
    check();
    const t = setInterval(check, 5000);
    return () => { mounted = false; clearInterval(t); };
  }, []);

  return (
    <>
      <ParticleBackground />
      <div id="app">
        <Navbar apiOnline={apiOnline} />
        <main>
          {!apiOnline && (
            <div className="error-banner" style={{ marginTop: 24 }}>
              ⚠ Can't reach the TrackShift backend. Start it with <code>uvicorn main:app --reload --port 8000</code> in
              the <code>backend</code> folder, then refresh.
            </div>
          )}
          <Routes>
            <Route path="/" element={<Home />} />

            {/* Tyre Intelligence module — the hackathon problem-statement feature */}
            <Route path="/tyre-intelligence" element={<TyreIntelligence />} />
            <Route path="/degradation" element={<DegradationAnalysis />} />
            <Route path="/lap-forensics" element={<LapForensics />} />
            <Route path="/strategy-simulator" element={<StrategySimulator />} />
            <Route path="/race-engineer" element={<RaceEngineer />} />
            <Route path="/decision-center" element={<DecisionCenter />} />

            {/* Race Ops — original race-strategy simulation, unchanged */}
            <Route path="/live" element={<LiveRace />} />
            <Route path="/strategy" element={<Strategy />} />
            <Route path="/telemetry" element={<Telemetry />} />
            <Route path="/competitors" element={<Competitors />} />
            <Route path="/tyres" element={<Tyres />} />
            <Route path="/simulator" element={<Simulator />} />

            <Route path="/about" element={<About />} />
            <Route path="*" element={<Home />} />
          </Routes>
        </main>
        <footer>TRACKSHIFT · SIMULATION MODE · BUILT FOR HACKATHON DEMONSTRATION · NOT AFFILIATED WITH FORMULA 1 OR THE FIA</footer>
      </div>
    </>
  );
}
