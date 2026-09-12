"""
TrackShift — Tyre Intelligence API routes.

Mounted under /tyre-intel in main.py. This layer is deliberately thin: it
fetches mock laps, calls into tyre_analytics.py for every calculation, and
shapes the response. No calculation logic lives here.
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from fastapi import UploadFile, File

from decision_value import calculate_decision_value, optimize_resource_budget, DEFAULT_ACTIONS
from telemetry_io import normalize_csv
from typing import Optional

import mock_data
import tyre_analytics as ta
import race_engineer

router = APIRouter(prefix="/tyre-intel", tags=["tyre-intelligence"])

_uploaded_analysis = None
_uploaded_laps = None


# ---------------------------------------------------------------- shared helpers
def _current_analysis():
    return _uploaded_analysis if _uploaded_analysis is not None else ta.analyze_session(mock_data.get_session())


def _default_stint_id(stints):
    for sid in stints:
        if sid.startswith("REY-medium"):
            return sid
    return next(iter(stints)) if stints else None


def _get_stint_or_404(stints, stint_id):
    if stint_id not in stints:
        raise HTTPException(status_code=404, detail=f"Unknown stintId '{stint_id}'. See /tyre-intel/stints for valid ids.")
    return stints[stint_id]


def _pick_next_compound_model(stints, current_compound, prefer=None):
    """
    Picks a degradation model to represent "the tyre you'd pit onto", for
    contexts where the caller hasn't specified one (Overview/Demo KPI
    cards). Prefers `prefer` if given and has data; otherwise picks the
    compound (other than the current one) with the lowest degradation rate
    among those with sufficient data — a reasonable default assumption
    that pitting means going to a more durable compound, not a like-for-
    like swap. Returns None if no other compound has enough data, in which
    case callers should fall back to a same-compound assumption.
    """
    compare_rows = ta.compare_compounds(stints)
    if prefer and prefer in compare_rows and not compare_rows[prefer].get("insufficientData"):
        row = compare_rows[prefer]
        return {"degradationRate": row["degradationRate"], "degradationAcceleration": row["degradationAcceleration"]}, prefer

    candidates = [
        (k, v) for k, v in compare_rows.items()
        if k != current_compound and not v.get("insufficientData")
    ]
    if not candidates:
        return None, None
    best_key, best_row = min(candidates, key=lambda kv: kv[1]["degradationRate"])
    return {"degradationRate": best_row["degradationRate"], "degradationAcceleration": best_row["degradationAcceleration"]}, best_key


# ---------------------------------------------------------------- meta
@router.get("/meta")
def meta():
    return {"drivers": mock_data.get_drivers(), "compounds": mock_data.get_compounds()}


@router.get("/stints")
def list_stints():
    stints = _current_analysis()
    return {
        "defaultStintId": _default_stint_id(stints),
        "stints": [
            {
                "stintId": s["stintId"], "driver": s["driver"], "driverName": s["driverName"],
                "car": s["car"], "compound": s["compound"], "compoundLabel": s["compoundLabel"],
                "stintLength": s["stintLength"], "currentAge": s["currentAge"],
                "degradationConfidence": s["degradationModel"].get("confidence"),
                "insufficientData": s["degradationModel"].get("insufficientData", False),
            }
            for s in stints.values()
        ],
    }


@router.post("/session/regenerate")
def regenerate_session(seed: Optional[int] = None):
    global _uploaded_analysis, _uploaded_laps
    _uploaded_analysis = None
    _uploaded_laps = None
    mock_data.regenerate_session(seed)
    return {"status": "regenerated"}


# ---------------------------------------------------------------- overview / KPIs
@router.get("/overview")
def overview(stintId: Optional[str] = Query(None)):
    stints = _current_analysis()
    sid = stintId or _default_stint_id(stints)
    stint = _get_stint_or_404(stints, sid)
    deg = stint["degradationModel"]

    if deg.get("insufficientData"):
        return {
            "stintId": sid, "driver": stint["driverName"], "compound": stint["compoundLabel"],
            "tyreAge": stint["currentAge"], "insufficientData": True, "message": deg["message"],
        }

    life = ta.predict_remaining_life(deg, stint["currentAge"])
    next_model, next_compound = _pick_next_compound_model(stints, stint["compound"])
    pit = ta.calculate_pit_window(deg, stint["currentAge"], next_model=next_model)

    return {
        "stintId": sid,
        "driver": stint["driverName"],
        "car": stint["car"],
        "compound": stint["compound"],
        "compoundLabel": stint["compoundLabel"],
        "tyreAge": stint["currentAge"],
        "estimatedDegradationRate": deg["degradationRate"],
        "degradationAcceleration": deg["degradationAcceleration"],
        "confidence": deg["confidence"],
        "estimatedRemainingLife": life.get("remainingCompetitiveLaps"),
        "recommendedPitWindow": pit.get("recommendedWindowLabel"),
        "recommendedNextCompound": next_compound,
        "validLapCount": deg["validLapCount"],
        "totalLapCount": deg["totalLapCount"],
        "insufficientData": False,
    }


# ---------------------------------------------------------------- hero: raw vs corrected
@router.get("/degradation")
def degradation(stintId: Optional[str] = Query(None)):
    stints = _current_analysis()
    sid = stintId or _default_stint_id(stints)
    stint = _get_stint_or_404(stints, sid)
    deg = stint["degradationModel"]
    laps = stint["laps"]

    if deg.get("insufficientData") or len(laps) < 2:
        return {"stintId": sid, "insufficientData": True, "message": deg.get("message", "Not enough data.")}

    valid_laps = [l for l in laps if not l["excluded"]]
    if len(valid_laps) < 2:
        return {"stintId": sid, "insufficientData": True, "message": "Not enough clean laps to compare raw vs corrected change."}
    first, last = valid_laps[0], valid_laps[-1]
    raw_slowdown = round(last["lapTime"] - first["lapTime"], 3)

    # average per-lap contributions across the stint (excluding invalid laps for the averages)
    avg = lambda key: round(sum(l[key] for l in valid_laps) / len(valid_laps), 3) if valid_laps else 0.0
    fuel_avg = avg("fuelEffect")
    traffic_avg = avg("trafficPenalty")
    evo_avg = avg("trackEvolutionEffect")

    return {
        "stintId": sid,
        "insufficientData": False,
        "rawObservedChange": raw_slowdown,
        "fuelEffect": fuel_avg,
        "trafficEffect": traffic_avg,
        "trackEvolutionEffect": evo_avg,
        "estimatedTrueDegradation": deg["degradationRate"],
        "confidence": deg["confidence"],
        "validLapCount": deg["validLapCount"],
        "totalLapCount": deg["totalLapCount"],
        "excludedLapCount": deg["totalLapCount"] - deg["validLapCount"],
        "curve": ta.degradation_curve(deg),
    }


# ---------------------------------------------------------------- laps (validity table)
@router.get("/laps")
def laps(stintId: Optional[str] = Query(None)):
    stints = _current_analysis()
    sid = stintId or _default_stint_id(stints)
    stint = _get_stint_or_404(stints, sid)
    return {
        "stintId": sid,
        "laps": [
            {
                "lapNumber": l["lapNumber"], "stintLap": l["stintLap"], "lapTime": l["lapTime"],
                "correctedLapTime": l["correctedLapTime"], "trafficScore": l["trafficScore"],
                "trafficLevel": l["trafficLevel"], "flagStatus": l["flagStatus"], "pitLap": l["pitLap"],
                "lapValidity": l["lapValidity"], "excluded": l["excluded"], "checks": l["checks"],
            }
            for l in stint["laps"]
        ],
    }


# ---------------------------------------------------------------- degradation curve (filterable)
@router.get("/degradation-curve")
def degradation_curve_endpoint(compound: Optional[str] = None, driver: Optional[str] = None, stintId: Optional[str] = None):
    stints = _current_analysis()

    if stintId:
        stint = _get_stint_or_404(stints, stintId)
        selected = [stint]
    else:
        selected = list(stints.values())
        if compound:
            selected = [s for s in selected if s["compound"] == compound]
        if driver:
            selected = [s for s in selected if s["driver"] == driver]

    curves = []
    for s in selected:
        deg = s["degradationModel"]
        if deg.get("insufficientData"):
            continue
        curves.append({
            "stintId": s["stintId"], "driver": s["driverName"], "compound": s["compound"],
            "compoundLabel": s["compoundLabel"], "degradationRate": deg["degradationRate"],
            "degradationAcceleration": deg["degradationAcceleration"], "confidence": deg["confidence"],
            "curve": ta.degradation_curve(deg, max_age=max(s["stintLength"] + 5, 15)),
        })

    if not curves:
        return {"insufficientData": True, "message": "Not enough clean laps for the selected filter.", "curves": []}
    return {"insufficientData": False, "curves": curves}


# ---------------------------------------------------------------- compound comparison
@router.get("/compare")
def compare():
    stints = _current_analysis()
    return {"compounds": ta.compare_compounds(stints)}


# ---------------------------------------------------------------- remaining life
@router.get("/remaining-life")
def remaining_life(stintId: Optional[str] = Query(None)):
    stints = _current_analysis()
    sid = stintId or _default_stint_id(stints)
    stint = _get_stint_or_404(stints, sid)
    deg = stint["degradationModel"]
    if deg.get("insufficientData"):
        return {"stintId": sid, "insufficientData": True, "message": deg["message"]}
    life = ta.predict_remaining_life(deg, stint["currentAge"])
    return {"stintId": sid, "currentAge": stint["currentAge"], **life}


# ---------------------------------------------------------------- lap forensics
@router.get("/lap-forensics")
def lap_forensics(driver: str, lapNumber: int):
    stints = _current_analysis()
    stint = next((s for s in stints.values() if s["driver"] == driver.upper()
                  and any(l["lapNumber"] == lapNumber for l in s["laps"])), None)
    if not stint:
        raise HTTPException(status_code=404, detail=f"No lap {lapNumber} found for driver {driver}.")
    lap = next(l for l in stint["laps"] if l["lapNumber"] == lapNumber)
    explanation = ta.generate_lap_explanation(lap, stint["degradationModel"], stint["baselineLap"])
    explanation["stintId"] = stint["stintId"]
    explanation["driver"] = stint["driverName"]
    explanation["compound"] = stint["compoundLabel"]
    return explanation


# ---------------------------------------------------------------- strategy simulator
class StrategyRequest(BaseModel):
    stintId: str
    nextCompound: str = Field(default="hard")
    pitLossSeconds: float = Field(default=ta.PIT_LOSS_SEC, ge=10, le=35)
    horizon: int = Field(default=10, ge=3, le=20)


@router.post("/strategy")
def strategy(body: StrategyRequest):
    stints = _current_analysis()
    stint = _get_stint_or_404(stints, body.stintId)
    deg = stint["degradationModel"]
    if deg.get("insufficientData"):
        return {"insufficientData": True, "message": deg["message"]}

    compare_rows = ta.compare_compounds(stints)
    next_row = compare_rows.get(body.nextCompound, {})
    next_model = None
    if next_row and not next_row.get("insufficientData"):
        next_model = {"degradationRate": next_row["degradationRate"],
                       "degradationAcceleration": next_row["degradationAcceleration"]}

    # same next_model feeds BOTH the pit-window calc and the options comparison below,
    # so the two can never disagree about what "pitting" actually means here.
    pit = ta.calculate_pit_window(deg, stint["currentAge"], next_model=next_model,
                                   pit_loss=body.pitLossSeconds, horizon=body.horizon)

    def project(delay):
        cost_before = sum(
            deg["degradationRate"] * (stint["currentAge"] + i) + deg["degradationAcceleration"] * (stint["currentAge"] + i) ** 2
            for i in range(delay)
        )
        if next_model:
            cost_after = body.pitLossSeconds + sum(
                next_model["degradationRate"] * i + next_model["degradationAcceleration"] * i ** 2
                for i in range(body.horizon - delay)
            )
        else:
            cost_after = body.pitLossSeconds
        return round(cost_before + cost_after, 2)

    options = [
        {"key": "stay", "label": f"Stay on {stint['compoundLabel']} for {body.horizon} more laps",
         "projectedCost": round(sum(deg["degradationRate"] * (stint["currentAge"] + i) + deg["degradationAcceleration"] * (stint["currentAge"] + i) ** 2 for i in range(body.horizon)), 2)},
        {"key": "now", "label": f"Pit now → {body.nextCompound.upper()}", "projectedCost": project(0)},
        {"key": "plus3", "label": f"Pit in 3 laps → {body.nextCompound.upper()}", "projectedCost": project(3)},
    ]
    best = min(options, key=lambda o: o["projectedCost"])
    for o in options:
        o["recommended"] = o["key"] == best["key"]

    return {
        "insufficientData": False,
        "stintId": body.stintId,
        "currentCompound": stint["compoundLabel"],
        "currentAge": stint["currentAge"],
        "options": options,
        "recommendedOption": best["key"],
        "pitWindow": pit,
    }



# ---------------------------------------------------------------- decision intelligence
class DecisionValueRequest(BaseModel):
    stintId: str
    budget: float = Field(default=100.0, ge=0, le=10000)


@router.post("/decision-value")
def decision_value(body: DecisionValueRequest):
    stints = _current_analysis()
    stint = _get_stint_or_404(stints, body.stintId)
    deg = stint["degradationModel"]
    if deg.get("insufficientData"):
        return {"insufficientData": True, "message": deg["message"]}
    compare_rows = ta.compare_compounds(stints)
    current = stint["compound"]
    next_model, next_compound = _pick_next_compound_model(stints, current)
    candidates = [
        {"key": "stay", "delay": 0, "pitLoss": 0},
        {"key": "pit_now", "delay": 0, "pitLoss": ta.PIT_LOSS_SEC},
        {"key": "pit_plus_3", "delay": 3, "pitLoss": ta.PIT_LOSS_SEC},
    ]
    if next_model:
        for c in candidates:
            c["pitLoss"] = 0 if c["key"] == "stay" else ta.PIT_LOSS_SEC
    result = calculate_decision_value(deg, stint["currentAge"], candidates, budget=body.budget)
    result["stintId"] = body.stintId
    result["compound"] = stint["compoundLabel"]
    result["nextCompound"] = next_compound
    result["modelEvidence"] = {"validLapCount": deg.get("validLapCount"), "totalLapCount": deg.get("totalLapCount"), "degradationRate": deg.get("degradationRate"), "confidence": deg.get("confidence")}
    result["resourcePrinciple"] = "Resource Credits are normalized demonstration units, not claimed F1 financial costs."
    return result


class ResourcePlanRequest(BaseModel):
    budget: float = Field(default=100.0, ge=0, le=10000)
    actions: list[dict] = []


@router.post("/resource-plan")
def resource_plan(body: ResourcePlanRequest):
    actions = body.actions or DEFAULT_ACTIONS
    return optimize_resource_budget(actions, body.budget)


@router.get("/model-assumptions")
def model_assumptions():
    return {
        "mode": "simulation",
        "source": "synthetic demo data unless an uploaded session is active",
        "assumptions": [
            {"name": "Fuel coefficient", "value": ta.FUEL_COEF_SEC_PER_KG, "unit": "s/kg", "type": "estimated"},
            {"name": "Pit loss", "value": ta.PIT_LOSS_SEC, "unit": "s", "type": "configurable estimate"},
            {"name": "Traffic clear threshold", "value": ta.TRAFFIC_CLEAR_THRESHOLD, "unit": "score / 100", "type": "heuristic"},
            {"name": "Critical degradation", "value": ta.CRITICAL_DEGRADATION_THRESHOLD_SEC, "unit": "s/lap", "type": "configurable threshold"},
        ],
        "note": "These values must be calibrated with team-specific historical data before professional use."
    }


@router.post("/session/upload")
async def upload_session(file: UploadFile = File(...)):
    global _uploaded_analysis, _uploaded_laps
    content = await file.read()
    try:
        laps = normalize_csv(content.decode("utf-8-sig"))
        analysis = ta.analyze_session(laps)
    except (UnicodeDecodeError, ValueError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _uploaded_laps = laps
    _uploaded_analysis = analysis
    return {"status": "uploaded", "filename": file.filename, "lapCount": len(laps), "stintCount": len(analysis), "stints": list(analysis.keys()), "mode": "uploaded"}


@router.post("/session/use-demo")
def use_demo_session():
    global _uploaded_analysis, _uploaded_laps
    _uploaded_analysis = None
    _uploaded_laps = None
    return {"status": "demo", "mode": "simulation"}

# ---------------------------------------------------------------- AI race engineer
class AskRequest(BaseModel):
    question: str
    stintId: Optional[str] = None


@router.post("/ask")
def ask(body: AskRequest):
    stints = _current_analysis()
    sid = body.stintId or _default_stint_id(stints)
    stint = _get_stint_or_404(stints, sid) if sid else None
    compare_rows = ta.compare_compounds(stints)

    lap_explanations = {}
    pit_window = None
    if stint and not stint["degradationModel"].get("insufficientData"):
        for lap in stint["laps"]:
            exp = ta.generate_lap_explanation(lap, stint["degradationModel"], stint["baselineLap"])
            lap_explanations[lap["lapNumber"]] = exp
        pit_window = ta.calculate_pit_window(stint["degradationModel"], stint["currentAge"])

    context = {
        "currentStint": stint,
        "allStints": stints,
        "compare": compare_rows,
        "degModel": stint["degradationModel"] if stint else {},
        "lapExplanations": lap_explanations,
        "pitWindow": pit_window,
    }
    answer = race_engineer.answer_question(body.question, context)
    return {"question": body.question, "answer": answer, "stintId": sid}


@router.get("/ask/examples")
def ask_examples():
    return {"examples": race_engineer.EXAMPLE_QUESTIONS}


# ---------------------------------------------------------------- demo bundle (single call for Home hero + Demo Mode)
@router.get("/demo")
def demo():
    stints = _current_analysis()
    sid = _default_stint_id(stints)
    stint = _get_stint_or_404(stints, sid)
    deg = stint["degradationModel"]
    if deg.get("insufficientData"):
        return {"insufficientData": True, "message": deg["message"]}

    laps = stint["laps"]
    valid_laps = [l for l in laps if not l["excluded"]]
    if len(valid_laps) < 2:
        return {"insufficientData": True, "message": "Not enough clean laps to compare raw vs corrected change."}
    raw_slowdown = round(valid_laps[-1]["lapTime"] - valid_laps[0]["lapTime"], 3)
    avg = lambda key: round(sum(l[key] for l in valid_laps) / len(valid_laps), 3) if valid_laps else 0.0
    life = ta.predict_remaining_life(deg, stint["currentAge"])
    next_model, next_compound = _pick_next_compound_model(stints, stint["compound"])
    pit = ta.calculate_pit_window(deg, stint["currentAge"], next_model=next_model)

    return {
        "insufficientData": False,
        "stintId": sid,
        "driver": stint["driverName"],
        "compound": stint["compoundLabel"],
        "tyreAge": stint["currentAge"],
        "rawObservedChange": raw_slowdown,
        "fuelEffect": avg("fuelEffect"),
        "trafficEffect": avg("trafficPenalty"),
        "trackEvolutionEffect": avg("trackEvolutionEffect"),
        "estimatedTrueDegradation": deg["degradationRate"],
        "confidence": deg["confidence"],
        "excludedLapCount": deg["totalLapCount"] - deg["validLapCount"],
        "totalLapCount": deg["totalLapCount"],
        "remainingCompetitiveLaps": life.get("remainingCompetitiveLaps"),
        "recommendedPitWindow": pit.get("recommendedWindowLabel"),
        "recommendedNextCompound": next_compound,
    }
