"""
TrackShift — Tyre Intelligence: ANALYTICS ENGINE.

Pure calculation functions. No FastAPI, no UI, no imports from mock_data
beyond receiving plain lap dicts as arguments — this module would work
unchanged against a real telemetry feed with the same lap schema.

THE PIPELINE (this is the actual product):

    RAW LAP TIME
        -> remove fuel effect            (calculate_fuel_effect)
        -> remove traffic penalty        (calculate_traffic_penalty)
        -> exclude invalid laps          (calculate_lap_validity)
        -> remove track evolution        (calculate_track_evolution)
        -> CORRECTED LAP TIME            (calculate_corrected_lap_time)
        -> fit degradation model         (calculate_tyre_degradation)
        -> ESTIMATED TRUE TYRE DEGRADATION

Every number that reaches the API is labeled as estimated/predicted with a
confidence score. Nothing here claims causal certainty — it's a statistical
decomposition of a lap-time signal into named, additive components.
"""
import math
import statistics


# ---------------------------------------------------------------- constants
MAX_TRAFFIC_PENALTY_SEC = 0.95
TRAFFIC_CLEAR_THRESHOLD = 20        # traffic score below this = "clear"
FUEL_COEF_SEC_PER_KG = 0.033         # must match the physical assumption used to *estimate* fuel if no sensor exists
CRITICAL_DEGRADATION_THRESHOLD_SEC = 1.2   # sec/lap loss vs fresh tyre considered "end of competitive life"
PIT_LOSS_SEC = 21.5


def traffic_level_label(score):
    if score <= 20:
        return "Clear"
    if score <= 40:
        return "Light"
    if score <= 60:
        return "Moderate"
    if score <= 80:
        return "Heavy"
    return "Severe"


# ---------------------------------------------------------------- fuel
def calculate_fuel_effect(lap, stint_laps):
    """
    Fuel effect for a single lap, expressed relative to the START of its
    stint (i.e. "how much faster is this lap than lap 1 of the stint,
    purely because it's carrying less fuel"). Negative = faster.

    If lap["fuelEstimated"] is True, this is model-based (documented
    coefficient FUEL_COEF_SEC_PER_KG applied to a fuel curve derived from
    lap number / stint position) rather than a direct sensor reading —
    this is surfaced to the UI so it is never presented as measured fact.
    """
    stint_start_fuel = stint_laps[0]["fuelLoad"]
    delta_kg = lap["fuelLoad"] - stint_start_fuel
    effect = delta_kg * FUEL_COEF_SEC_PER_KG
    return round(effect, 3)


# ---------------------------------------------------------------- traffic
def calculate_traffic_penalty(lap):
    """
    Maps an observed traffic score (0-100, itself a proxy derived from gap
    to car ahead / sector-time disruption) to an estimated time penalty in
    seconds. This is a calibrated heuristic, not a measured quantity.
    """
    score = lap.get("trafficScore", 0)
    if score <= TRAFFIC_CLEAR_THRESHOLD:
        return 0.0
    frac = (score - TRAFFIC_CLEAR_THRESHOLD) / (100 - TRAFFIC_CLEAR_THRESHOLD)
    return round(frac * MAX_TRAFFIC_PENALTY_SEC, 3)


def traffic_summary(lap):
    score = lap.get("trafficScore", 0)
    return {
        "trafficScore": score,
        "trafficLevel": traffic_level_label(score),
        "trafficPenalty": calculate_traffic_penalty(lap),
    }


# ---------------------------------------------------------------- track evolution
def calculate_track_evolution(all_valid_laps):
    """
    Empirically estimates how much faster the track is getting over the
    course of the session.

    Identification approach: within any single stint, tyre age and session
    time are perfectly collinear (age increases in lockstep with time), so
    naively regressing corrected lap time against session lap number over a
    full stint would just re-absorb the tyre degradation trend itself. To
    avoid that, we calibrate evolution ONLY from laps with tyreAge <= 3 —
    laps where degradation has barely had time to act — across every stint.
    Each stint's calibration points are first centered on that stint's own
    mean (removing compound/driver pace level), then pooled and regressed
    against lapNumber. Any remaining trend in that pooled, centered
    residual is attributed to track evolution rather than tyre wear.
    """
    calibration = [l for l in all_valid_laps if l["tyreAge"] <= 3]
    if len(calibration) < 6:
        return {"rate_sec_per_lap": 0.0, "r_squared": 0.0, "sufficient_data": False}

    by_stint = {}
    for lap in calibration:
        by_stint.setdefault(lap["stintId"], []).append(lap)

    xs, ys = [], []
    for stint_laps in by_stint.values():
        if len(stint_laps) < 2:
            continue
        mean_time = statistics.mean(l["_correctedForFuelTraffic"] for l in stint_laps)
        for l in stint_laps:
            xs.append(l["lapNumber"])
            ys.append(l["_correctedForFuelTraffic"] - mean_time)

    if len(xs) < 6:
        return {"rate_sec_per_lap": 0.0, "r_squared": 0.0, "sufficient_data": False}

    slope, intercept, r2 = _linear_regression(xs, ys)
    return {"rate_sec_per_lap": round(slope, 5), "r_squared": round(r2, 3), "sufficient_data": True}


def _linear_regression(xs, ys):
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    ss_xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    ss_xx = sum((x - mean_x) ** 2 for x in xs)
    if ss_xx == 0:
        return 0.0, mean_y, 0.0
    slope = ss_xy / ss_xx
    intercept = mean_y - slope * mean_x
    ss_tot = sum((y - mean_y) ** 2 for y in ys)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return slope, intercept, r2


# ---------------------------------------------------------------- lap validity
def calculate_lap_validity(lap):
    """
    Produces a 0-100 validity score plus a pass/fail checklist. Laps below
    LAP_VALIDITY_EXCLUDE_THRESHOLD are excluded from degradation fitting.
    """
    checks = []
    penalty = 0

    if lap["pitLap"]:
        checks.append(("Pit entry/exit lap", False))
        penalty += 60
    else:
        checks.append(("No pit activity", True))

    if lap["flagStatus"] != "green":
        checks.append((f"{lap['flagStatus'].upper()} flag active", False))
        penalty += 45
    else:
        checks.append(("No flag", True))

    traffic = lap.get("trafficScore", 0)
    if traffic > 60:
        checks.append(("Heavy traffic", False))
        penalty += 35
    elif traffic > 20:
        checks.append(("Light/moderate traffic", False))
        penalty += 12
    else:
        checks.append(("Low traffic", True))

    # abnormal sector check: sector 2 unusually long relative to sector 1+3 split
    total = lap["sector1"] + lap["sector2"] + lap["sector3"]
    s2_ratio = lap["sector2"] / total if total else 0
    if s2_ratio > 0.42:
        checks.append(("Abnormal sector split", False))
        penalty += 15
    else:
        checks.append(("Normal sector performance", True))

    checks.append(("Clean track" if lap["flagStatus"] == "green" and not lap["pitLap"] else "Track compromised",
                    lap["flagStatus"] == "green" and not lap["pitLap"]))

    score = max(0, 100 - penalty)
    excluded = score < 60
    return {
        "lapValidity": score,
        "excluded": excluded,
        "checks": [{"label": c[0], "passed": c[1]} for c in checks],
    }


# ---------------------------------------------------------------- corrected lap time
def build_corrected_dataset(laps):
    """
    Runs the full correction pipeline over a list of laps (typically one
    stint, but works over any list). Returns the same laps enriched with:
        trafficPenalty, trafficLevel, fuelEffect, lapValidity, excluded,
        validityChecks, correctedLapTime, contributions (dict of named
        signed seconds that sum exactly to lapTime - stintBaseline).
    """
    if not laps:
        return []

    stint_laps_by_id = {}
    for lap in laps:
        stint_laps_by_id.setdefault(lap["stintId"], []).append(lap)
    for stint_laps in stint_laps_by_id.values():
        stint_laps.sort(key=lambda l: l["tyreAge"])

    enriched = []
    for lap in laps:
        stint_laps = stint_laps_by_id[lap["stintId"]]
        fuel_effect = calculate_fuel_effect(lap, stint_laps)
        traffic = traffic_summary(lap)
        validity = calculate_lap_validity(lap)
        e = dict(lap)
        e["fuelEffect"] = fuel_effect
        e.update(traffic)
        e.update(validity)
        e["_correctedForFuelTraffic"] = lap["lapTime"] - fuel_effect - traffic["trafficPenalty"]
        enriched.append(e)

    # track evolution needs the whole valid pool
    valid_laps = [l for l in enriched if not l["excluded"]]
    evolution = calculate_track_evolution(valid_laps)
    evo_rate = evolution["rate_sec_per_lap"]

    for e in enriched:
        stint_laps = stint_laps_by_id[e["stintId"]]
        baseline_lap_number = stint_laps[0]["lapNumber"]
        track_evo_effect = evo_rate * (e["lapNumber"] - baseline_lap_number)
        e["trackEvolutionEffect"] = round(track_evo_effect, 3)
        e["correctedLapTime"] = round(e["lapTime"] - e["fuelEffect"] - e["trafficPenalty"] - track_evo_effect, 3)
        del e["_correctedForFuelTraffic"]

    return enriched, evolution


# ---------------------------------------------------------------- tyre degradation fit
def calculate_tyre_degradation(enriched_stint_laps):
    """
    Fits corrected lap time vs tyre age for one stint, using only valid
    laps, to estimate a degradation rate (sec/lap) and acceleration
    (sec/lap^2). Confidence reflects both sample size and fit quality.

    Returns None-safe structure: if too few valid laps exist, flags
    `insufficient_data` instead of fabricating a confident number.
    """
    valid = [l for l in enriched_stint_laps if not l["excluded"]]
    if len(valid) < 4:
        return {
            "insufficientData": True,
            "message": "Not enough clean laps to estimate degradation reliably.",
            "validLapCount": len(valid),
        }

    valid = sorted(valid, key=lambda l: l["tyreAge"])
    baseline = valid[0]["correctedLapTime"]
    xs = [l["tyreAge"] for l in valid]
    ys = [l["correctedLapTime"] - baseline for l in valid]

    slope, intercept, r2 = _linear_regression(xs, ys)
    # quadratic acceleration term via simple residual-vs-age^2 regression
    residuals = [y - (slope * x + intercept) for x, y in zip(xs, ys)]
    xs2 = [x ** 2 for x in xs]
    accel_slope, _, accel_r2 = _linear_regression(xs2, residuals)
    accel = max(accel_slope, 0.0)  # degradation acceleration shouldn't be negative in our model

    confidence = _confidence_score(len(valid), r2)

    return {
        "insufficientData": False,
        "degradationRate": round(max(slope, 0.0), 4),
        "degradationAcceleration": round(accel, 5),
        "rSquared": round(r2, 3),
        "confidence": confidence,
        "validLapCount": len(valid),
        "totalLapCount": len(enriched_stint_laps),
        "baselineLapTime": round(baseline, 3),
    }


def _confidence_score(n_valid, r_squared):
    base = min(n_valid / 12, 1.0) * 55       # sample-size component, caps at 12 laps
    fit = max(r_squared, 0) * 40             # fit-quality component
    return round(min(base + fit + 5, 97))


# ---------------------------------------------------------------- degradation curve
def degradation_curve(deg_model, max_age=25):
    if deg_model.get("insufficientData"):
        return []
    rate = deg_model["degradationRate"]
    accel = deg_model["degradationAcceleration"]
    return [
        {"tyreAge": age, "correctedLoss": round(rate * age + accel * age ** 2, 3)}
        for age in range(1, max_age + 1)
    ]


# ---------------------------------------------------------------- remaining life
def predict_remaining_life(deg_model, current_age, threshold=CRITICAL_DEGRADATION_THRESHOLD_SEC):
    if deg_model.get("insufficientData"):
        return {"insufficientData": True, "message": "Not enough clean laps to project remaining tyre life."}
    rate = deg_model["degradationRate"]
    accel = deg_model["degradationAcceleration"]

    if accel <= 1e-6:
        if rate <= 1e-6:
            crit_age = current_age + 20  # flat degradation — arbitrarily far out, capped below
        else:
            crit_age = threshold / rate
    else:
        crit_age = (-rate + math.sqrt(max(rate ** 2 + 4 * accel * threshold, 0))) / (2 * accel)

    remaining = max(0, round(crit_age - current_age))
    remaining = min(remaining, 20)
    projection = []
    for step in range(0, 11):
        age = current_age + step
        loss = rate * age + accel * age ** 2
        projection.append({"lapOffset": step, "tyreAge": age, "predictedLoss": round(loss, 3)})

    return {
        "insufficientData": False,
        "remainingCompetitiveLaps": remaining,
        "criticalAge": round(crit_age, 1),
        "projection": projection,
    }


# ---------------------------------------------------------------- pit window / strategy
def calculate_pit_window(deg_model, current_age, next_model=None, pit_loss=PIT_LOSS_SEC, horizon=10):
    """
    Compares projected cumulative corrected time staying out vs pitting at
    each lap in [0..horizon] to recommend a pit-lap range.

    `next_model` is the degradation model (rate/acceleration) of the tyre
    you'd pit ONTO. If not provided, this falls back to assuming a fresh
    tyre of the SAME compound (deg_model itself) — which is a real and
    sometimes-useful scenario (a like-for-like tyre change) but callers
    that know the intended next compound should always pass its model,
    otherwise this can look artificially favorable toward pitting (a fresh
    tyre on the SAME steep curve resets the clock without gaining the
    lower-degradation benefit an actual compound change would provide).
    """
    if deg_model.get("insufficientData"):
        return {"insufficientData": True, "message": "Not enough clean laps to recommend a pit window."}

    rate, accel = deg_model["degradationRate"], deg_model["degradationAcceleration"]
    next_rate, next_accel = (next_model["degradationRate"], next_model["degradationAcceleration"]) if next_model else (rate, accel)
    assumed_same_compound = next_model is None

    def loss_at(age):
        return rate * age + accel * age ** 2

    def next_loss_at(age):
        return next_rate * age + next_accel * age ** 2

    best_lap, best_cost = None, math.inf
    costs = []
    for delay in range(0, horizon + 1):
        cost_before = sum(loss_at(current_age + i) for i in range(delay))
        if delay >= horizon:
            # never actually pits within the horizon — no pit-loss incurred
            cost_after = 0.0
        else:
            cost_after = pit_loss + sum(next_loss_at(i) for i in range(horizon - delay))
        total = cost_before + cost_after
        costs.append({"delayLaps": delay, "projectedCost": round(total, 2)})
        if total < best_cost:
            best_cost, best_lap = total, delay

    if best_lap >= horizon:
        window = "hold — no pit needed yet"
        reason = "Current tyre is degrading slowly enough that staying out through the full horizon costs less than pitting."
    elif best_lap == 0:
        window = "now"
        reason = "Current tyre degradation is already costing more per lap than the pit-loss amortizes over the remaining stint."
    elif best_lap <= 3:
        window = f"in {best_lap} lap{'s' if best_lap != 1 else ''}"
        reason = "Degradation is increasing faster than the expected pit-loss penalty over the next few laps."
    else:
        window = f"in {best_lap}+ laps"
        reason = "Current tyre is still within its competitive window; degradation cost is lower than an immediate pit-loss."

    return {
        "insufficientData": False,
        "recommendedDelayLaps": best_lap,
        "recommendedWindowLabel": window,
        "reason": reason,
        "costCurve": costs,
        "assumedSameCompoundForNextTyre": assumed_same_compound,
    }


# ---------------------------------------------------------------- lap forensics
def generate_lap_explanation(enriched_lap, deg_model, baseline_lap):
    """
    Builds the "why was this lap slower" waterfall, relative to the first
    VALID lap of the stint (not necessarily tyreAge 1 — that's usually the
    pit out-lap and is excluded). All four named components are rebased
    against the SAME baseline lap's own fuel/traffic/track-evolution
    values, so the breakdown is internally consistent regardless of which
    lap ends up as the reference. Contributions are signed seconds and ARE
    GUARANTEED to sum to (lapTime - baselineLapTime) — the residual is
    placed in "driver variation" so the breakdown is always honest about
    what it could and couldn't attribute.
    """
    raw_delta = round(enriched_lap["lapTime"] - baseline_lap["lapTime"], 3)

    tyre_component = 0.0
    if deg_model and not deg_model.get("insufficientData"):
        rate, accel = deg_model["degradationRate"], deg_model["degradationAcceleration"]
        age, baseline_age = enriched_lap["tyreAge"], baseline_lap["tyreAge"]
        loss_now = rate * age + accel * age ** 2
        loss_baseline = rate * baseline_age + accel * baseline_age ** 2
        tyre_component = loss_now - loss_baseline

    fuel_component = enriched_lap["fuelEffect"] - baseline_lap["fuelEffect"]
    traffic_component = enriched_lap["trafficPenalty"] - baseline_lap["trafficPenalty"]
    track_component = enriched_lap["trackEvolutionEffect"] - baseline_lap["trackEvolutionEffect"]

    explained = tyre_component + fuel_component + traffic_component + track_component
    driver_component = round(raw_delta - explained, 3)

    contributions = {
        "tyreDegradation": round(tyre_component, 3),
        "traffic": round(traffic_component, 3),
        "fuelEffect": round(fuel_component, 3),
        "trackEvolution": round(track_component, 3),
        "driverVariation": driver_component,
    }
    primary_cause = max(contributions, key=lambda k: abs(contributions[k]))
    label_map = {
        "tyreDegradation": "TYRE DEGRADATION", "traffic": "TRAFFIC", "fuelEffect": "FUEL EFFECT",
        "trackEvolution": "TRACK EVOLUTION", "driverVariation": "DRIVER VARIATION",
    }

    return {
        "lapNumber": enriched_lap["lapNumber"],
        "rawDelta": raw_delta,
        "contributions": contributions,
        "primaryCause": label_map[primary_cause],
        "primaryCauseKey": primary_cause,
        "excluded": enriched_lap["excluded"],
        "lapValidity": enriched_lap["lapValidity"],
    }


# ---------------------------------------------------------------- session-level orchestration
def analyze_session(raw_laps):
    """
    Runs the full pipeline over an entire session (all drivers, all
    stints) and returns a dict keyed by stintId. This is the single
    entry point the API layer calls — it does not know about mock_data,
    it just takes a list of lap dicts matching the documented schema.
    """
    by_stint = {}
    for lap in raw_laps:
        by_stint.setdefault(lap["stintId"], []).append(lap)

    stints = {}
    for stint_id, stint_laps in by_stint.items():
        stint_laps = sorted(stint_laps, key=lambda l: l["tyreAge"])
        enriched, evolution = build_corrected_dataset(stint_laps)
        deg_model = calculate_tyre_degradation(enriched)
        # Baseline must come from the first VALID lap, not literally tyreAge=1 —
        # in this dataset tyreAge=1 is always the pit out-lap and is excluded,
        # so using it as a reference would contaminate every forensics delta.
        valid_sorted = [l for l in enriched if not l["excluded"]]
        baseline_lap = valid_sorted[0] if valid_sorted else enriched[0]
        stints[stint_id] = {
            "stintId": stint_id,
            "driver": stint_laps[0]["driver"],
            "driverName": stint_laps[0]["driverName"],
            "car": stint_laps[0]["car"],
            "compound": stint_laps[0]["compound"],
            "compoundLabel": stint_laps[0]["compoundLabel"],
            "laps": enriched,
            "degradationModel": deg_model,
            "trackEvolution": evolution,
            "currentAge": enriched[-1]["tyreAge"],
            "stintLength": len(enriched),
            "baselineLapTime": baseline_lap["correctedLapTime"],
            "baselineTyreAge": baseline_lap["tyreAge"],
            "baselineLap": baseline_lap,
        }
    return stints


# ---------------------------------------------------------------- compound comparison
def compare_compounds(stints_by_id):
    """
    Aggregates every stint of each compound (across all drivers) into a
    single comparison row. Ranks are relative to the other compounds
    actually present in the session — not fixed physical constants.
    """
    by_compound = {}
    for stint in stints_by_id.values():
        by_compound.setdefault(stint["compound"], []).append(stint)

    rows = {}
    for compound, stints in by_compound.items():
        valid_models = [s["degradationModel"] for s in stints if not s["degradationModel"].get("insufficientData")]
        if not valid_models:
            rows[compound] = {"insufficientData": True, "compound": compound}
            continue

        avg_rate = statistics.mean(m["degradationRate"] for m in valid_models)
        avg_accel = statistics.mean(m["degradationAcceleration"] for m in valid_models)
        avg_confidence = round(statistics.mean(m["confidence"] for m in valid_models))
        # For cross-stint pace comparison (unlike within-stint degradation fitting), we
        # also remove the ABSOLUTE fuel load, not just the delta from stint start — different
        # stints begin at different points in the session with different starting fuel, and
        # that has to be normalized out for a fair "initial pace" comparison across compounds.
        initial_paces = [
            round(s["baselineLap"]["correctedLapTime"] - s["baselineLap"]["fuelLoad"] * FUEL_COEF_SEC_PER_KG, 3)
            for s in stints if s.get("baselineLap")
        ]
        avg_initial_pace = statistics.mean(initial_paces) if initial_paces else None

        all_residual_laps = [l for s in stints for l in s["laps"] if not l["excluded"]]
        if len(all_residual_laps) >= 4:
            ages = [l["tyreAge"] for l in all_residual_laps]
            times = [l["correctedLapTime"] for l in all_residual_laps]
            slope, intercept, _ = _linear_regression(ages, times)
            residual_stdev = statistics.pstdev([t - (slope * a + intercept) for a, t in zip(ages, times)])
        else:
            residual_stdev = None

        pseudo_model = {"insufficientData": False, "degradationRate": avg_rate, "degradationAcceleration": avg_accel}
        life = predict_remaining_life(pseudo_model, current_age=1)

        rows[compound] = {
            "insufficientData": False,
            "compound": compound,
            "degradationRate": round(avg_rate, 4),
            "degradationAcceleration": round(avg_accel, 5),
            "confidence": avg_confidence,
            "avgInitialPace": round(avg_initial_pace, 3) if avg_initial_pace is not None else None,
            "consistency": round(residual_stdev, 3) if residual_stdev is not None else None,
            "expectedLifeLaps": life.get("remainingCompetitiveLaps") if not life.get("insufficientData") else None,
            "stintCount": len(stints),
            "lapCount": sum(s["stintLength"] for s in stints),
        }

    # relative labels (Fast/Medium/Slow, High/Medium/Low, Short/Medium/Long)
    valid_rows = [r for r in rows.values() if not r["insufficientData"]]
    if valid_rows:
        paces = sorted(valid_rows, key=lambda r: r["avgInitialPace"] or 0)
        rates = sorted(valid_rows, key=lambda r: r["degradationRate"])
        lives = sorted(valid_rows, key=lambda r: r["expectedLifeLaps"] or 0)
        pace_label = {r["compound"]: lbl for r, lbl in zip(paces, ["Fast", "Medium", "Slow"][:len(paces)])}
        rate_label = {r["compound"]: lbl for r, lbl in zip(rates, ["Low", "Medium", "High"][:len(rates)])}
        life_label = {r["compound"]: lbl for r, lbl in zip(lives, ["Short", "Medium", "Long"][:len(lives)])}
        for r in valid_rows:
            r["initialPaceLabel"] = pace_label[r["compound"]]
            r["degradationLabel"] = rate_label[r["compound"]]
            r["lifeLabel"] = life_label[r["compound"]]

    return rows
