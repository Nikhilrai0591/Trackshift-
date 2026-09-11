# TrackShift — Implementation Summary

Everything below is what actually changed in this update, tested against a
live-running instance before being written down here.

---

## 1. Files changed

**New files (Tyre Intelligence module):**
- `backend/mock_data.py` — synthetic practice-session generator
- `backend/tyre_analytics.py` — the analytics pipeline (pure functions)
- `backend/race_engineer.py` — deterministic Q&A assistant
- `backend/tyre_intel_api.py` — FastAPI router (`/tyre-intel/*`)
- `backend/validate_pipeline.py` — automated correctness test suite
- `frontend/src/pages/TyreIntelligence.jsx`
- `frontend/src/pages/DegradationAnalysis.jsx`
- `frontend/src/pages/LapForensics.jsx`
- `frontend/src/pages/StrategySimulator.jsx`
- `frontend/src/pages/RaceEngineer.jsx`
- `frontend/src/components/StintPicker.jsx`
- `frontend/src/components/WaterfallChart.jsx`
- `frontend/src/components/ValidityBadge.jsx`

**Modified files:**
- `backend/main.py` — mounts the new router, rebranded title, CORS unchanged
- `backend/engine.py` — one docstring line reworded (no logic changed)
- `backend/requirements.txt` — added `numpy`
- `frontend/src/api.js` — added `tyreIntelApi` client (original `api` object untouched)
- `frontend/src/App.jsx` — added 5 new routes; all original routes kept
- `frontend/src/components/Navbar.jsx` — rebranded, Tyre Intelligence pages
  promoted to the primary tab row, original pages grouped under a **Race
  Ops ▾** dropdown so nothing was deleted or hidden
- `frontend/src/pages/Home.jsx` — new hero copy + live raw-vs-corrected
  numbers pulled from `/tyre-intel/demo`; feature strip and stats row kept
- `frontend/src/pages/About.jsx` — rewritten to describe both modules
- `frontend/src/styles.css` — appended new classes only (hero comparison,
  waterfall chart, validity badge, chat panel, nav dropdown); nothing
  removed or overridden
- `frontend/index.html`, `frontend/package.json` — title/name rebrand
- Legacy pages (`LiveRace.jsx`, `Strategy.jsx`, `Telemetry.jsx`,
  `Competitors.jsx`, `Tyres.jsx`, `ErrorBanner.jsx`) — text-only rebrand
  ("ApexAI" → "TrackShift" in headings/error messages); zero logic changed

**Untouched:** `backend/engine.py`'s actual simulation logic, all Race Ops
page components' internal logic, `Simulator.jsx`, `WeatherCard.jsx`,
`CompetitorTable.jsx`, `hooks.js`, `TelemetryChart.jsx`, `MonteCarloChart.jsx`.

---

## 2. Features added

- Tyre Intelligence Overview: hero raw-vs-corrected comparison, 8 KPI cards
- True degradation isolation: fuel / traffic / track-evolution / tyre
  breakdown, all in named seconds-per-lap
- Lap Validity Engine: 0–100 score, pass/fail checklist, auto-exclusion
- Degradation curves: filterable by driver/compound, soft/medium/hard
  comparison table with relative Fast/Medium/Slow-style labels
- Lap Forensics: per-lap waterfall (tyre / traffic / fuel / track evolution
  / driver variation), guaranteed to sum to the observed delta
- Remaining tyre life projection (10-lap forward curve)
- Pit-window / strategy simulator: stay vs pit-now vs pit-in-3, compound-aware
- AI Race Engineer: deterministic chat, 7 question intents, grounded answers
- Demo bundle endpoint powering the Home page's live hero numbers

---

## 3. Calculations / models implemented

All in `backend/tyre_analytics.py`:

| Function | What it does |
|---|---|
| `calculate_fuel_effect` | Fuel-load delta from stint start × a documented sec/kg coefficient |
| `calculate_traffic_penalty` | Maps a 0–100 traffic score to an estimated time penalty (calibrated heuristic, not measured) |
| `calculate_track_evolution` | **Empirical linear regression** of near-fresh-tyre laps (tyreAge ≤ 3) against session lap number, pooled across all stints — see the "identification" note in item 6 |
| `calculate_lap_validity` | Weighted penalty score from pit/flag/traffic/sector checks → 0–100 + pass/fail list |
| `build_corrected_dataset` | Applies all three corrections to every lap in a stint |
| `calculate_tyre_degradation` | Linear + quadratic regression of corrected lap time vs tyre age, valid laps only, with a sample-size-and-fit-quality confidence score |
| `degradation_curve` | Projects the fitted model forward for charting |
| `predict_remaining_life` | Solves the fitted quadratic for the age at which a critical-degradation threshold (1.2s/lap loss) is crossed |
| `calculate_pit_window` | Compares cumulative projected cost of pitting at each lap in a horizon vs staying out, compound-aware |
| `generate_lap_explanation` | Waterfall decomposition, residual assigned to "driver variation" so the breakdown always sums exactly |
| `compare_compounds` | Aggregates all stints per compound; relative Fast/Medium/Slow-style labels |

---

## 4. Data source currently in use

**100% mock/synthetic**, generated in `backend/mock_data.py`. There is no
real F1 telemetry, fuel-sensor, or timing-system integration in this build —
public practice-session telemetry at this granularity (per-lap fuel load,
true traffic gap, etc.) isn't available to plug in for a hackathon timeline.

The mock generator is seeded and deterministic (same session every restart
unless you call `POST /tyre-intel/session/regenerate`), and — importantly —
it also stores a *hidden* ground-truth degradation value per lap purely so
we could validate that the analytics engine recovers a signal close to what
was actually injected. The analytics engine never reads those hidden fields;
`validate_pipeline.py` checks the recovered values land in the right
relative order (soft > medium > hard degradation) using only what a real
dataset would expose.

**Swapping in a real feed** later only requires replacing `mock_data.py`'s
`get_session()` with something that returns the same lap-dict schema — the
analytics engine, API layer and frontend don't need to change.

---

## 5. Real vs. estimated — labeled explicitly

| Value | Status |
|---|---|
| Lap time, sector times, tyre compound, tyre age, flag status | Mock "raw" data, but internally consistent |
| Fuel load | `fuelEstimated: true` on every lap — always model-based here, since no real sensor exists |
| Traffic score / penalty | Estimated proxy, calibrated heuristic |
| Track evolution rate | Empirically fit from the data itself (real statistical estimate, but on synthetic data) |
| Degradation rate / acceleration | Fitted via regression, always shown with a confidence score |
| Remaining life, pit window, strategy recommendations | Explicitly labeled "estimated" / "predicted" everywhere in the UI, never presented as guaranteed |
| Race Engineer answers | Deterministic, template-filled from the above — not generative, cannot invent a number not already computed |

Nothing in this build claims real-world causal certainty. Every hero number
and KPI card carries a confidence percentage or an explicit estimate label.

---

## 6. How the system isolates tyre degradation

```
RAW LAP TIME
   → subtract fuel effect (fuelLoad delta × coefficient)
   → subtract traffic penalty (from trafficScore)
   → exclude invalid laps (pit laps, flags, heavy traffic, abnormal sectors)
   → subtract track evolution (regression on near-fresh-tyre laps only)
   → CORRECTED LAP TIME
   → fit corrected time vs tyre age (linear + quadratic term)
   → ESTIMATED TRUE DEGRADATION RATE + CONFIDENCE
```

The one non-obvious design decision worth explaining to a judge: track
evolution and tyre degradation are **statistically collinear within a single
stint** (both increase with time in lockstep), so a naive regression of
corrected time against session time would just re-absorb the degradation
trend it's supposed to be separating out. We calibrate evolution only from
laps with `tyreAge <= 3` — laps too fresh for degradation to have acted much
— across every stint, which breaks that collinearity. This was a real bug
caught by `validate_pipeline.py` during development (degradation was coming
out as ~0 before the fix) — see the git history / commit messages for the
before/after if you want to show judges the debugging process.

---

## 7. How to run the project

See `README.md` → "Run it". Short version:
```bash
cd backend && pip install -r requirements.txt && uvicorn main:app --reload --port 8000
cd frontend && npm install && npm run dev
```

---

## 8. Environment variables

| Variable | Where | Purpose |
|---|---|---|
| `ALLOWED_ORIGINS` | backend | Comma-separated CORS origins for production (defaults to `*`) |
| `VITE_API_BASE` | frontend `.env` | Backend URL the frontend calls |

No API keys are required — there is no external LLM or third-party service
in this build.

---

## 9. Limitations

- **Synthetic data only.** Rankings and confidence scores are internally
  consistent but not validated against real F1 telemetry.
- **Small sample per compound** (2 stints each in the default session) —
  confidence scores reflect this (typically 75–92%, not higher).
- **Fuel model is a simplification**: linear sec/kg coefficient, not a real
  physics model of fuel-load-vs-lap-time (which is track- and car-dependent).
- **Traffic score is a proxy**, not derived from real gap/telemetry data.
- **Track evolution calibration** uses only near-fresh-tyre laps, which
  limits precision when a compound's stints are short.
- **Pit window model assumes a fixed pit-loss constant** per calculation
  (user-adjustable in the Strategy Simulator, but not track-specific).
- **Race Engineer is intent-matched, not free-form** — unrecognized
  questions get a fallback listing example questions, by design (no
  hallucination), but that means it can't answer genuinely novel phrasings.
- The original Race Ops module (Live Race, Monte Carlo, etc.) and the new
  Tyre Intelligence module use **separate, unrelated mock datasets** — a lap
  time in one has no relationship to a lap time in the other. This is fine
  for the hackathon demo but worth knowing if you extend either module.

---

## 10. 60-second explanation for judges

> "TrackShift answers one question: when a lap gets slower, is it actually
> the tyres — or is it fuel, traffic, or the track itself? We built a
> pipeline that takes raw lap times from a practice session and strips out
> fuel burn, traffic-affected laps, and track evolution one layer at a time,
> using statistical fits rather than guesses. What's left is an isolated,
> confidence-scored estimate of true tyre degradation — for this stint, it's
> [X] seconds per lap, at [Y]% confidence, versus a much bigger raw slowdown
> of [Z] seconds. From that curve we predict how many competitive laps are
> left and recommend a pit window. You can drill into any single lap and see
> exactly why it was slow — tyre, traffic, fuel, or just driver variance —
> and ask our Race Engineer assistant questions about it, which only ever
> answers from numbers we've actually calculated, never invented ones. It's
> all built on mock data because real per-lap fuel and traffic telemetry
> isn't publicly available, but the pipeline is architected so a real feed
> could drop in without changing the analysis code at all."

(Swap in the live numbers from the Home page or Tyre Intelligence Overview
when you say it — they'll be different each time you regenerate the session.)
