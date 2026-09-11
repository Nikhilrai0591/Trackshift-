import { useState, useRef, useEffect } from 'react';
import { usePolling } from '../hooks';
import { tyreIntelApi } from '../api';
import StintPicker from '../components/StintPicker';

export default function RaceEngineer() {
  const [stintId, setStintId] = useState(null);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([
    { role: 'assistant', text: "I'm the TrackShift Race Engineer. Ask me about degradation, consistency, pit timing, or a specific lap — I only answer from what's actually been calculated for the current session." },
  ]);
  const [sending, setSending] = useState(false);
  const scrollRef = useRef(null);

  const { data: stintsData } = usePolling(tyreIntelApi.getStints, 0);
  const { data: examplesData } = usePolling(tyreIntelApi.getAskExamples, 0);
  const stints = stintsData?.stints || [];
  const activeStintId = stintId || stintsData?.defaultStintId;

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages]);

  const send = async (text) => {
    const q = (text ?? input).trim();
    if (!q || sending) return;
    setMessages(m => [...m, { role: 'user', text: q }]);
    setInput('');
    setSending(true);
    try {
      const r = await tyreIntelApi.ask(q, activeStintId);
      setMessages(m => [...m, { role: 'assistant', text: r.answer }]);
    } catch {
      setMessages(m => [...m, { role: 'assistant', text: "I couldn't reach the analysis backend just now — try again in a moment." }]);
    } finally {
      setSending(false);
    }
  };

  return (
    <section className="page">
      <div className="section-head">
        <h2>TrackShift Race Engineer</h2>
        <p>A deterministic assistant grounded in this session's actual calculated data — no external LLM, no invented telemetry.</p>
      </div>

      {stints.length > 0 && (
        <div className="filter-bar">
          <StintPicker stints={stints} value={activeStintId} onChange={setStintId} label="Context stint" />
        </div>
      )}

      <div className="panel chat-panel">
        <div className="chat-messages" ref={scrollRef}>
          {messages.map((m, i) => (
            <div key={i} className={`chat-msg ${m.role}`}>{m.text}</div>
          ))}
          {sending && <div className="chat-msg assistant">…</div>}
        </div>

        <div className="chat-examples">
          {(examplesData?.examples || []).slice(0, 4).map(q => (
            <div key={q} className="chat-example-pill" onClick={() => send(q)}>{q}</div>
          ))}
        </div>

        <div className="chat-input-row">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') send(); }}
            placeholder="Ask about degradation, consistency, pit timing, a lap number…"
          />
          <button className="btn btn-primary btn-sm" onClick={() => send()} disabled={sending}>Send</button>
        </div>
      </div>
    </section>
  );
}
