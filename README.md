# TrackShift — Tyre Intelligence Engine

**"Isolating true tyre wear from fuel, traffic and track conditions."**

A slow lap doesn't automatically mean tyre degradation. TrackShift separates
fuel burn, traffic, track evolution and driver variation from the raw
lap-time signal — what's left over is a confidence-scored estimate of actual
tyre wear.

> **SIMULATION MODE.** All race, telemetry, competitor, weather and
> practice-session data in this app is procedurally generated for
> demonstration purposes. Not affiliated with, endorsed by, or connected to
> Formula 1®, the FIA, or any real team, driver, or race.

---

## Two modules, one app

This project started as a live-race pit-strategy simulator. The Tyre
Intelligence module below was added on top of it for the hackathon problem
statement — both share one FastAPI backend and one React frontend, but are
otherwise independent (separate data, separate routes, separate nav group).

### 1. Tyre Intelligence *(new — the hackathon deliverable)*
The core pipeline: **raw lap time → remove fuel effect → remove traffic
penalty → exclude invalid laps → remove track evolution → corrected lap
time → fit degradation curve → estimate true degradation → predict
remaining life → recommend a pit window.**

| Page | Route | What it shows |
|---|---|---|
| Overview | `/tyre-intelligence` | Hero raw-vs-corrected comparison + KPI cards (compound, age, degradation rate, confidence, remaining life, recommended pit window) |
| Degradation Analysis | `/degradation` | Filterable degradation curves (driver/compound) + soft/medium/hard comparison table |
| Lap Forensics | `/lap-forensics` | Pick a lap → waterfall breakdown of why it was slower + lap validity checklist |
| Strategy Simulator | `/strategy-simulator` | Stay-out vs pit-now vs pit-in-3-laps, compound-aware cost comparison |
| Race Engineer | `/race-engineer` | Deterministic Q&A chat, grounded in the session's actual computed metrics |

### 2. Race Ops *(original — kept intact, in the "Race Ops" nav dropdown)*
The original live-race strategy simulator: Live Race, Telemetry,
Competitors, legacy Tyre Analytics, legacy Race Sim (Monte Carlo), legacy
Pit Strategy. Unchanged from before this update — see the nav bar's **Race
Ops ▾** dropdown.

---

## Project layout

```
trackshift/
├── backend/
│   ├── engine.py            Race Ops: live-race simulation engine (unchanged)
│   ├── mock_data.py         Tyre Intel: synthetic practice-session generator
│   ├── tyre_analytics.py    Tyre Intel: the analytics pipeline (pure functions)
│   ├── race_engineer.py     Tyre Intel: deterministic Q&A assistant
│   ├── tyre_intel_api.py    Tyre Intel: FastAPI router, mounted at /tyre-intel
│   ├── main.py              App entrypoint — mounts both modules + CORS
│   ├── validate_pipeline.py Automated correctness checks (see below)
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── api.js                    axios client (race-ops + tyreIntelApi)
    │   ├── hooks.js                  usePolling hook for live data
    │   ├── components/               Navbar, ParticleBackground, charts,
    │   │                              WaterfallChart, ValidityBadge, StintPicker…
    │   └── pages/
    │       ├── Home, About                        (updated for TrackShift)
    │       ├── TyreIntelligence, DegradationAnalysis,
    │       │   LapForensics, StrategySimulator,
    │       │   RaceEngineer                        (new)
    │       └── LiveRace, Strategy, Telemetry,
    │           Competitors, Tyres, Simulator        (Race Ops, unchanged)
    └── package.json
```

---

## Run it

Two terminals — one for the API, one for the UI.

### 1. Backend (FastAPI)

```bash
cd backend
python3 -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Swagger docs at `http://localhost:8000/docs` — every endpoint below is
listed and callable from there directly.

### 2. Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

**Note on `frontend/.env`:** it's currently pointed at a deployed backend
(`VITE_API_BASE=https://trackshift-oirc.onrender.com/`) from before this
update. That deployment is still running the *old* backend and doesn't have
the new `/tyre-intel/*` routes yet — **redeploy the backend on Render** (push
this updated `backend/` folder) for the Tyre Intelligence pages to work
against it. For local development, point `.env` at your local backend
instead: `VITE_API_BASE=http://localhost:8000`.

### 3. Verify the analytics pipeline (optional but recommended)

```bash
cd backend
uvicorn main:app --port 8000 &
python3 validate_pipeline.py
```

This hits every `/tyre-intel/*` endpoint and asserts:
- compound degradation ranks correctly (soft > medium > hard),
- the lap-forensics waterfall sums *exactly* to the raw observed delta on
  every single lap, in every stint,
- the strategy simulator and pit-window calculator never disagree with each
  other about what "pitting" means.

---

## API reference — Tyre Intelligence (`/tyre-intel/*`)

| Method | Path | Description |
|---|---|---|
| GET | `/tyre-intel/meta` | Drivers + compounds available in the session |
| GET | `/tyre-intel/stints` | List every stint with basic stats + the default stint id |
| POST | `/tyre-intel/session/regenerate` | Regenerate the mock session (new random seed) |
| GET | `/tyre-intel/overview?stintId=` | KPI card data for one stint |
| GET | `/tyre-intel/degradation?stintId=` | Hero raw-vs-corrected breakdown + curve |
| GET | `/tyre-intel/laps?stintId=` | Every lap in a stint with validity scoring |
| GET | `/tyre-intel/degradation-curve?compound=&driver=&stintId=` | Filterable curve data |
| GET | `/tyre-intel/compare` | Soft/Medium/Hard comparison table |
| GET | `/tyre-intel/remaining-life?stintId=` | Projected remaining competitive laps |
| GET | `/tyre-intel/lap-forensics?driver=&lapNumber=` | Waterfall breakdown for one lap |
| POST | `/tyre-intel/strategy` | Body: `{stintId, nextCompound, pitLossSeconds, horizon}` |
| POST | `/tyre-intel/ask` | Body: `{question, stintId}` — the Race Engineer |
| GET | `/tyre-intel/ask/examples` | Example questions for the chat UI |
| GET | `/tyre-intel/demo` | Single-call bundle for the Home page hero numbers |

The original Race Ops API (`/race/state`, `/telemetry`, `/strategy`,
`/competitors`, `/tyres`, `/weather`, plus the `/race/*` and
`/strategy/simulate` POST endpoints) is unchanged from before.

---

## Deploying an update

Same hosts as before (Render for the backend, Vercel/Netlify for the
frontend — `frontend/vercel.json` and `frontend/netlify.toml` are already
configured with the SPA rewrite rule). If you already have this project
deployed:

1. Push this updated code to the GitHub repo Render/Vercel are tracking.
2. Render will redeploy the backend automatically (or trigger manually from
   its dashboard) — this is what activates the new `/tyre-intel/*` routes.
3. Vercel/Netlify will redeploy the frontend automatically on push.
4. No new environment variables are required beyond what was already set
   (`ALLOWED_ORIGINS` on the backend, `VITE_API_BASE` on the frontend).

See `IMPLEMENTATION.md` for the full breakdown of what changed, what's real
vs. estimated, and a 60-second judge pitch. See `DEPLOYMENT.md` for the full
step-by-step deploy guide (updating your existing Render/Vercel deployment,
setting up fresh, or a 2-minute ngrok backup for demo day).

## Decision Intelligence upgrade

The current build includes a **Decision Center** at `/decision-center`. It adds a resource-aware layer to the tyre model: TrackShift estimates decision sensitivity and whether additional analysis is worth its normalized **Resource Credit** cost. It also supports CSV session uploads at `POST /tyre-intel/session/upload`.

Resource Credits are intentionally configurable demonstration units, not claims about real F1 costs. Before professional use, calibrate assumptions with team-specific historical data.

See `IMPLEMENTATION_ROADMAP.md` for the staged product plan and `sample_telemetry.csv` for an example upload format.
