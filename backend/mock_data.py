"""
TrackShift — Tyre Intelligence: MOCK DATA LAYER.

This file is the ONLY place in the Tyre Intelligence module that invents
numbers. Everything in `tyre_analytics.py` treats this data as if it came
from a real telemetry feed — it never peeks at the "hidden" ground-truth
fields below, and every value it computes (fuel effect, traffic penalty,
track evolution, tyre degradation, lap validity...) is *derived statistically
from the observed columns*, the same way it would be from a real dataset.

Why synthetic data, and why this matters for the demo:
    We don't have access to real F1 practice-session telemetry (fuel
    sensors, live gap data, etc. are not publicly available at this level of
    granularity). So we generate a physically-plausible session where we
    KNOW the true tyre degradation we injected — which lets us show judges
    that the analytics engine (tyre_analytics.py) actually recovers a
    signal close to the injected ground truth, rather than just producing
    plausible-looking numbers. The hidden ground-truth fields are exposed
    ONLY via `debug_ground_truth=True` on the session getter, clearly
    labeled, and are never used by the analytics engine itself.

Replacing this with a real data source later means implementing a function
with the same output shape as `get_session()` — nothing in tyre_analytics.py
or the API layer needs to change.
"""
import math
import random
import zlib

DRIVERS = [
    {"code": "REY", "name": "J. Reyes", "car": 16, "consistency": 0.06},   # smooth, consistent
    {"code": "LDQ", "name": "H. Lindqvist", "car": 4, "consistency": 0.11},  # more variance
    {"code": "CST", "name": "R. Castillo", "car": 55, "consistency": 0.08},
]

COMPOUNDS = {
    "soft":   {"label": "SOFT",   "code": "C4", "color": "#e8101f", "base_pace": -0.85, "true_rate": 0.145, "true_accel": 0.0065},
    "medium": {"label": "MEDIUM", "code": "C3", "color": "#ffb648", "base_pace": 0.0,   "true_rate": 0.078, "true_accel": 0.0026},
    "hard":   {"label": "HARD",   "code": "C2", "color": "#f3f4f6", "base_pace": 0.55,  "true_rate": 0.036, "true_accel": 0.0009},
}

FUEL_START_KG = 108.0
FUEL_BURN_PER_LAP_KG = 1.65
FUEL_COEF_SEC_PER_KG = 0.033   # heavier car = slower, sec of laptime per kg

BASE_LAP_TIME = 92.4
SESSION_TOTAL_LAPS = 46
TRACK_EVOLUTION_RATE = 0.0065  # sec/lap faster per session-lap as rubber goes down


def _seeded_random(seed):
    r = random.Random(seed)
    return r


def _build_stint(rnd, driver, compound_key, stint_start_session_lap, stint_len, session_lap_cursor):
    """Builds one stint (a run on one set of tyres) for one driver."""
    compound = COMPOUNDS[compound_key]
    laps = []
    fuel = FUEL_START_KG - (stint_start_session_lap * FUEL_BURN_PER_LAP_KG * 0.4)
    driver_sigma = driver["consistency"]

    for tyre_age in range(1, stint_len + 1):
        session_lap = session_lap_cursor + tyre_age
        fuel_this_lap = max(fuel - tyre_age * FUEL_BURN_PER_LAP_KG, 8.0)

        # --- ground truth signal (hidden from the analytics engine) ---
        true_degradation = compound["true_rate"] * tyre_age + compound["true_accel"] * tyre_age ** 2
        fuel_effect_hidden = fuel_this_lap * FUEL_COEF_SEC_PER_KG
        track_evolution_hidden = -TRACK_EVOLUTION_RATE * session_lap
        driver_noise = rnd.gauss(0, driver_sigma)

        # --- traffic: some laps get compromised ---
        is_traffic_lap = rnd.random() < 0.22
        traffic_score = 0
        traffic_penalty_hidden = 0.0
        if is_traffic_lap:
            traffic_score = int(min(100, max(21, rnd.gauss(58, 20))))
            traffic_penalty_hidden = (traffic_score / 100) * 0.9 + rnd.uniform(0, 0.15)
        else:
            traffic_score = int(max(0, rnd.gauss(8, 6)))

        # --- flags / pit laps: rare, invalidate the lap ---
        flag_status = "green"
        pit_lap = False
        flag_penalty = 0.0
        roll = rnd.random()
        if tyre_age == 1 or tyre_age == stint_len:
            pit_lap = True
            flag_penalty = rnd.uniform(17, 23)
        elif roll < 0.035:
            flag_status = "yellow"
            flag_penalty = rnd.uniform(1.5, 4.0)
        elif roll < 0.05:
            flag_status = "vsc"
            flag_penalty = rnd.uniform(3.0, 6.5)

        measurement_noise = rnd.gauss(0, 0.05)

        lap_time = (
            BASE_LAP_TIME + compound["base_pace"] + true_degradation
            + fuel_effect_hidden + track_evolution_hidden + traffic_penalty_hidden
            + flag_penalty + driver_noise + measurement_noise
        )

        # sector split (rough thirds with a bit of independent noise)
        s1 = lap_time * 0.31 + rnd.gauss(0, 0.05)
        s2 = lap_time * 0.38 + rnd.gauss(0, 0.05)
        s3 = lap_time - s1 - s2

        laps.append({
            "lapNumber": session_lap,
            "stintLap": tyre_age,
            "driver": driver["code"],
            "driverName": driver["name"],
            "car": driver["car"],
            "session": "FP2",
            "compound": compound_key,
            "compoundLabel": compound["label"],
            "tyreAge": tyre_age,
            "lapTime": round(lap_time, 3),
            "sector1": round(s1, 3), "sector2": round(s2, 3), "sector3": round(s3, 3),
            "fuelLoad": round(fuel_this_lap, 1),
            "fuelEstimated": True,
            "trafficScore": traffic_score,
            "trackTemperature": None,   # filled in by the caller (shared per session)
            "airTemperature": None,
            "flagStatus": flag_status,
            "pitLap": pit_lap,
            "stintId": f"{driver['code']}-{compound_key}-{stint_start_session_lap}",
            # ground truth — internal only, prefixed so it's obvious it's not "real" data
            "_hidden_true_tyre_degradation": round(true_degradation, 4),
            "_hidden_fuel_effect": round(fuel_effect_hidden, 4),
            "_hidden_track_evolution": round(track_evolution_hidden, 4),
            "_hidden_traffic_penalty": round(traffic_penalty_hidden, 4),
            "_hidden_driver_noise": round(driver_noise, 4),
        })
    return laps


def generate_session(seed=42):
    """
    Generates one full deterministic (seeded) practice session across all
    3 drivers, each running 2 stints (their compound assignment varies so
    every compound gets covered across the field — enough for the compound
    comparison feature).
    """
    rnd = _seeded_random(seed)
    all_laps = []

    # give each driver two stints on two different compounds
    driver_plans = [
        ["soft", "medium"],
        ["medium", "hard"],
        ["hard", "soft"],
    ]

    for driver, plan in zip(DRIVERS, driver_plans):
        cursor = 0
        for compound_key in plan:
            stint_seed = seed + zlib.crc32(f"{driver['code']}-{compound_key}".encode()) % 1000
            stint_len = random.Random(stint_seed).randint(9, 15)
            stint = _build_stint(rnd, driver, compound_key, cursor, stint_len, cursor)
            all_laps.extend(stint)
            cursor += stint_len

    # shared session-level track/air temperature drift
    max_session_lap = max(l["lapNumber"] for l in all_laps)
    for lap in all_laps:
        progress = lap["lapNumber"] / max(max_session_lap, 1)
        lap["trackTemperature"] = round(38 + progress * 6 + math.sin(lap["lapNumber"] * 0.3) * 1.2, 1)
        lap["airTemperature"] = round(24 + progress * 3, 1)

    all_laps.sort(key=lambda l: (l["driver"], l["lapNumber"]))
    return all_laps


# Module-level cache: one generated session, regenerable on demand via the API.
_session_cache = {"seed": 42, "laps": generate_session(42)}


def get_session(strip_hidden=True):
    laps = _session_cache["laps"]
    if strip_hidden:
        return [{k: v for k, v in lap.items() if not k.startswith("_hidden")} for lap in laps]
    return laps


def regenerate_session(seed=None):
    if seed is None:
        seed = random.randint(1, 999999)
    _session_cache["seed"] = seed
    _session_cache["laps"] = generate_session(seed)
    return get_session()


def get_drivers():
    return [{"code": d["code"], "name": d["name"], "car": d["car"]} for d in DRIVERS]


def get_compounds():
    return {k: {"label": v["label"], "code": v["code"], "color": v["color"]} for k, v in COMPOUNDS.items()}
