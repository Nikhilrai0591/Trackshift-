# TrackShift — product upgrade roadmap

## What changed in this build

This build adds the first production-oriented layer on top of the existing tyre intelligence engine:

1. **Decision Center** — combines degradation, confidence and strategy sensitivity.
2. **Value of Information** — estimates whether another analysis/test is worth its normalized Resource Credit cost.
3. **Resource planning** — transparent budget allocation using Resource Credits.
4. **CSV ingestion** — upload a real session-shaped CSV instead of relying only on synthetic telemetry.
5. **Transparent assumptions** — exposes fuel, pit-loss, traffic and degradation assumptions.
6. **Evidence-first UI** — every decision shows the data behind it.

## Levels

### Level 0 — Trust
- Keep simulation mode explicitly labelled.
- Expose assumptions and model metadata.
- Never present synthetic values as real F1 telemetry.

### Level 1 — Real data
- Use `POST /tyre-intel/session/upload`.
- Required CSV fields: `lapNumber`, `tyreAge`, `lapTime`.
- Optional fields include compound, stint, driver, fuel, traffic, sectors, flags and temperatures.
- The analytics engine receives the same normalized schema as demo data.

### Level 2 — Better modelling
Next production upgrades should add:
- temperature-aware degradation
- sector-level degradation
- uncertainty intervals
- cross-session calibration
- driver/setup effects

### Level 3 — Decision Intelligence
Current build starts this level:
- strategy sensitivity
- decision risk
- value of additional information
- recommendation: spend vs save

### Level 4 — Resource Optimization
The current resource planner uses a transparent greedy allocation. A production version should use a full integer/knapsack optimizer once action costs and value models are calibrated from customer data.

### Level 5 — Professional integrations
- WebSocket/live telemetry adapters
- historical sessions
- weather/competitor feeds
- team-specific configuration
- API/SSO/role permissions
- audit logs

### Level 6 — Enterprise/F1 positioning
TrackShift should not claim to replace an F1 team's internal models. Position it as a decision layer above existing telemetry, simulation and strategy systems.

## Resource Credits

Resource Credits are deliberately normalized. They are **not claimed to be actual F1 financial costs**. A real deployment should let a customer define the cost of a test, simulation or engineering action from their own economics.

## Real-world validation plan

1. Validate on synthetic sessions with known injected degradation.
2. Validate on public motorsport datasets where licensing permits.
3. Partner with one university/FSAE/karting/junior-racing team.
4. Measure prediction error, false recommendations, engineer time saved and decision changes.
5. Only then use quantified commercial ROI claims.
