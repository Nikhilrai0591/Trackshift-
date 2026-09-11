"""
TrackShift backend — SIMULATION MODE.

Run:
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8000

Two modules are mounted here:
  1. The original race-strategy simulation engine (engine.py) — live-race
     pit strategy, telemetry, competitors, Monte Carlo. Endpoints at the
     root path, unchanged from the original build.
  2. The Tyre Intelligence module (tyre_intel_api.py) — the hackathon
     problem-statement feature: isolating true tyre degradation from fuel,
     traffic and track-evolution effects on a mock practice session.
     Endpoints under /tyre-intel.

All race, telemetry, competitor, weather and tyre-intelligence data is
procedurally generated for demonstration purposes. This is not connected to
any real F1 race feed or telemetry provider.
"""
import os
import asyncio
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from engine import engine
from tyre_intel_api import router as tyre_intel_router


class SimulateRequest(BaseModel):
    tyre: str = Field(default="medium")
    position: int = Field(default=2, ge=1, le=20)
    weather: str = Field(default="dry")
    scProbability: float = Field(default=0.15, ge=0, le=1)
    iterations: int = Field(default=1000, ge=100, le=5000)


class SpeedRequest(BaseModel):
    multiplier: int = Field(default=1)


_bg_task = None


async def _background_loop():
    last = time.time()
    while True:
        await asyncio.sleep(0.1)
        now = time.time()
        dt = now - last
        last = now
        engine.advance(dt)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _bg_task
    _bg_task = asyncio.create_task(_background_loop())
    yield
    _bg_task.cancel()


app = FastAPI(title="TrackShift API", version="2.0.0", description="SIMULATION MODE — race-strategy + tyre-intelligence API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    # In production, set ALLOWED_ORIGINS to your deployed frontend URL(s),
    # comma-separated, e.g. "https://trackshift.vercel.app"
    allow_origins=os.environ.get("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tyre_intel_router)


@app.get("/")
def root():
    return {"service": "TrackShift API", "mode": "SIMULATION", "status": "ok",
            "modules": ["race-strategy (root paths)", "tyre-intelligence (/tyre-intel/*)"]}


# ---------------------------------------------------------------- GET
@app.get("/race/state")
def race_state():
    return engine.get_state_public()


@app.get("/telemetry")
def telemetry():
    return {"points": engine.telemetry_buffer, "latest": engine.telemetry_buffer[-1] if engine.telemetry_buffer else None}


@app.get("/strategy")
def strategy():
    reco = engine.compute_strategy()
    reco["featureImportance"] = engine.compute_feature_importance(reco)
    return reco


@app.get("/competitors")
def competitors():
    return {"competitors": engine.get_competitors_public()}


@app.get("/tyres")
def tyres():
    return {"tyres": engine.get_tyre_analytics(), "degradationCurve": engine.get_degradation_curve()}


@app.get("/weather")
def weather():
    return engine.get_weather_public()


# ---------------------------------------------------------------- POST (race control)
@app.post("/race/start")
def race_start():
    engine.state["running"] = True
    return {"running": True}


@app.post("/race/pause")
def race_pause():
    engine.state["running"] = False
    return {"running": False}


@app.post("/race/reset")
def race_reset():
    engine.reset()
    return engine.get_state_public()


@app.post("/race/next-lap")
def race_next_lap():
    engine.tick_lap()
    return engine.get_state_public()


@app.post("/race/speed")
def race_speed(body: SpeedRequest):
    if body.multiplier not in (1, 2, 5):
        raise HTTPException(status_code=400, detail="multiplier must be 1, 2, or 5")
    engine.state["speed"] = body.multiplier
    return {"speed": body.multiplier}


@app.post("/race/safety-car")
def race_safety_car():
    engine.trigger_safety_car()
    return {"flag": engine.state["flag"]}


# ---------------------------------------------------------------- POST (strategy simulation)
@app.post("/strategy/simulate")
def strategy_simulate(body: SimulateRequest):
    return engine.run_monte_carlo(
        tyre=body.tyre, start_position=body.position, weather=body.weather,
        sc_probability=body.scProbability, iterations=body.iterations,
    )
