"""
TrackShift simulation engine (Race Ops module — the original race-strategy
simulator this project started as, kept intact alongside the newer Tyre
Intelligence module).

Everything here is a procedurally generated SIMULATION for demo purposes.
No real Formula 1 telemetry, drivers, or teams are used or represented.
"""
import random
import math
import time
from copy import deepcopy

COMPOUNDS = {
    "soft":   {"label": "SOFT",   "code": "C4", "color": "#e8101f", "wear_rate": 0.061, "pace_delta": -0.85, "max_life": 20},
    "medium": {"label": "MEDIUM", "code": "C3", "color": "#ffb648", "wear_rate": 0.036, "pace_delta": 0.0,   "max_life": 32},
    "hard":   {"label": "HARD",   "code": "C2", "color": "#f3f4f6", "wear_rate": 0.019, "pace_delta": 0.55,  "max_life": 44},
}

DRIVERS = [
    {"car": 16, "name": "J. Reyes",     "team": "Vantage GP",     "me": True},
    {"car": 4,  "name": "H. Lindqvist", "team": "Nova Motorsport"},
    {"car": 55, "name": "R. Castillo",  "team": "Orion Racing"},
    {"car": 23, "name": "M. Dubois",    "team": "Kestrel F1"},
    {"car": 81, "name": "T. Nakashima", "team": "Vantage GP"},
    {"car": 63, "name": "A. Bekker",    "team": "Halcyon Team"},
    {"car": 7,  "name": "S. Ferreira",  "team": "Orion Racing"},
    {"car": 44, "name": "D. Kowalski",  "team": "Nova Motorsport"},
]


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def rnd(a, b):
    return a + random.random() * (b - a)


def pick(seq):
    return random.choice(seq)


class RaceEngine:
    def __init__(self):
        self.reset()

    # ------------------------------------------------------------------
    def reset(self):
        competitors = []
        for i, d in enumerate(DRIVERS):
            pos = 2 if d["car"] == 16 else (1 if i == 1 else i + 1)
            competitors.append({
                **d,
                "position": pos,
                "compound": "soft" if d["car"] == 55 else pick(["soft", "medium", "hard"]),
                "tyreAge": 15 if d["car"] == 55 else random.randint(2, 28),
                "lastLap": 81 + rnd(-1.2, 1.4),
                "gap": 0 if d["car"] == 16 else (rnd(1.2, 22) if pos > 2 else -rnd(1, 9)),
                "closing": 0.60 if d["car"] == 55 else rnd(-0.25, 0.35),
                "pace": rnd(-0.3, 0.3),
            })
        competitors.sort(key=lambda c: c["position"])

        self.state = {
            "lap": 31, "totalLaps": 57,
            "position": 2,
            "compound": "medium",
            "tyreAge": 17,
            "baseLap": 80.9,
            "lapTime": 81.884,
            "delta": 0.482,
            "flag": "green",  # green | vsc | sc | red
            "trackTemp": 42.0, "airTemp": 28.0, "rain": 0.0, "wind": 12.0, "grip": 98.0,
            "competitors": competitors,
            "scEventFired": False,
            "running": True,
            "speed": 1,
        }
        self.telemetry_buffer = []
        self.t_sec = 0.0
        self.lap_accum = 0.0
        self.tele_accum = 0.0
        self.last_tick_wall = time.time()

    # ------------------------------------------------------------------
    def tyre_wear_pct(self, compound, age):
        c = COMPOUNDS[compound]
        return clamp(1 - (1 - c["wear_rate"]) ** max(age, 0), 0, 1) * 100

    def remaining_laps(self, compound, age):
        laps = 0
        while self.tyre_wear_pct(compound, age + laps) < 92 and laps < 80:
            laps += 1
        return laps

    def predicted_lap_time(self, compound, age, base):
        c = COMPOUNDS[compound]
        wear = self.tyre_wear_pct(compound, age) / 100
        return base + c["pace_delta"] + wear * wear * 4.2

    # ------------------------------------------------------------------
    def compute_strategy(self):
        s = self.state
        pit_loss = 13.5 if s["flag"] == "sc" else (18.5 if s["flag"] == "vsc" else 21.8)
        horizon = 8
        next_compound = "hard"

        def project_pit(delay_laps):
            total = 0.0
            # laps completed on the current tyre before boxing
            for i in range(delay_laps):
                total += self.predicted_lap_time(s["compound"], s["tyreAge"] + i, s["baseLap"])
            total += pit_loss
            # remaining laps of the horizon on the fresh tyre
            remaining = horizon - delay_laps
            for i in range(remaining):
                total += self.predicted_lap_time(next_compound, i, s["baseLap"])
            return total

        opt_now = project_pit(0)
        opt_plus1 = project_pit(1)
        opt_plus2 = project_pit(2)
        opt_stay = sum(self.predicted_lap_time(s["compound"], s["tyreAge"] + i, s["baseLap"]) for i in range(horizon))

        rival = next((c for c in s["competitors"] if c["car"] == 55), s["competitors"][1])
        undercut_threat = clamp(rival["closing"] * 10 + (30 if rival["gap"] < 4 else 0) + (15 if rival["tyreAge"] > 12 else 0), 0, 100)
        undercut_label = "CRITICAL" if undercut_threat > 75 else "HIGH" if undercut_threat > 50 else "MEDIUM" if undercut_threat > 25 else "LOW"

        options = [
            {"key": "now", "label": "PIT NOW", "lap": s["lap"], "time": opt_now},
            {"key": "plus1", "label": "PIT +1 LAP", "lap": s["lap"] + 1, "time": opt_plus1},
            {"key": "plus2", "label": "PIT +2 LAPS", "lap": s["lap"] + 2, "time": opt_plus2},
            {"key": "stay", "label": "STAY OUT", "lap": None, "time": opt_stay},
        ]
        options.sort(key=lambda o: o["time"])
        best, second = options[0], options[1]
        margin = abs(second["time"] - best["time"])
        confidence = clamp(58 + margin * 9 + (12 if s["flag"] != "green" else 0), 55, 97)

        wear = self.tyre_wear_pct(s["compound"], s["tyreAge"])
        car_ahead = next((c for c in s["competitors"] if c["position"] == s["position"] - 1), None)
        car_ahead_gap = car_ahead["gap"] if car_ahead else 3
        clear_air = abs(car_ahead_gap) > 2.2

        reasons = []
        reasons.append("Tyre degradation increasing beyond optimal window" if wear > 55 else "Tyre degradation within manageable range")
        reasons.append("Clear air available for out-lap on rejoin" if clear_air else "Traffic risk on rejoin — window is tight")
        if undercut_label in ("HIGH", "CRITICAL"):
            reasons.append(f"Car {rival['car']} closing rapidly — undercut {undercut_label.lower()}")
        else:
            reasons.append("No immediate undercut threat from nearby rivals")
        reasons.append(f"{COMPOUNDS[next_compound]['label']} tyre suitable for remaining {s['totalLaps'] - s['lap']} laps")
        if s["flag"] != "green":
            reasons.append("Reduced pit-loss window under caution — strong case to box")

        reco = {
            "action": "STAY OUT" if best["key"] == "stay" else f"BOX LAP {best['lap']}",
            "compound": "—" if best["key"] == "stay" else f"{COMPOUNDS[next_compound]['code']} · {COMPOUNDS[next_compound]['label']}",
            "confidence": round(confidence),
            "gain": round(second["time"] - best["time"], 2),
            "undercutLabel": undercut_label,
            "undercutThreat": undercut_threat,
            "rejoin": f"P{s['position']}" if best["key"] == "stay" else f"P{clamp(s['position'] + (1 if undercut_label == 'CRITICAL' else 0), 1, 8)}",
            "reasons": reasons,
            "options": options,
            "best": best,
            "rivalCar": rival["car"],
            "rivalClosing": max(rival["closing"], 0),
            "wear": wear,
        }
        return reco

    def compute_feature_importance(self, reco):
        w = {
            "Tyre Temperature": clamp(20 + reco["wear"] * 0.3 + rnd(-2, 2), 10, 55),
            "Traffic Gap": clamp(15 + rnd(-3, 10), 8, 40),
            "Competitor Pace": clamp(reco["undercutThreat"] * 0.35 + rnd(-2, 2), 5, 40),
            "Track Evolution": clamp(10 + rnd(-3, 3), 5, 20),
        }
        w["Weather Stability"] = clamp(100 - sum(w.values()), 4, 25)
        total = sum(w.values())
        return {k: v / total * 100 for k, v in w.items()}

    # ------------------------------------------------------------------
    def tick_lap(self):
        s = self.state
        if s["lap"] >= s["totalLaps"]:
            s["running"] = False
            return
        s["lap"] += 1
        s["tyreAge"] += 1
        s["lapTime"] = self.predicted_lap_time(s["compound"], s["tyreAge"], s["baseLap"]) + rnd(-0.15, 0.15)
        s["delta"] = clamp(s["delta"] + rnd(-0.08, 0.12), -2, 6)

        s["trackTemp"] = clamp(s["trackTemp"] + rnd(-0.4, 0.4), 30, 52)
        s["airTemp"] = clamp(s["airTemp"] + rnd(-0.2, 0.2), 18, 35)
        s["rain"] = clamp(s["rain"] + (rnd(0, 20) if random.random() < 0.05 else rnd(-2, 1)), 0, 100)
        s["grip"] = clamp(100 - s["rain"] * 0.3 - rnd(0, 2), 60, 100)

        for c in s["competitors"]:
            if c.get("me"):
                continue
            c["tyreAge"] += 1
            c["gap"] = c["gap"] - c["closing"] + rnd(-0.15, 0.15)
            if c["car"] == 55:
                c["closing"] = clamp(c["closing"] + 0.01, 0.2, 1.1)
                c["gap"] = clamp(c["gap"] - c["closing"], -30, 30)
            c["lastLap"] = 81 + rnd(-1, 1.5) + self.tyre_wear_pct(c["compound"], c["tyreAge"]) / 100 * 1.5
            c["pace"] = clamp(c["pace"] + rnd(-0.05, 0.05), -0.5, 0.5)

        if not s["scEventFired"] and 34 <= s["lap"] <= 40 and random.random() < 0.35:
            self.trigger_safety_car()
        if s["flag"] == "sc" and random.random() < 0.3:
            s["flag"] = "green"
        elif s["flag"] == "vsc" and random.random() < 0.5:
            s["flag"] = "green"

    def trigger_safety_car(self):
        self.state["flag"] = "sc"
        self.state["scEventFired"] = True

    def tick_telemetry(self):
        s = self.state
        wear = self.tyre_wear_pct(s["compound"], s["tyreAge"]) / 100
        t = self.t_sec
        speed = clamp(310 - math.sin(t * 1.3) * 40 - wear * 15 + rnd(-4, 4), 60, 340)
        throttle = clamp(50 + math.sin(t * 1.3) * 50, 0, 100)
        brake = clamp(-math.sin(t * 1.3) * 60, 0, 100)
        rpm = clamp(9000 + throttle * 35 + rnd(-100, 100), 6000, 12500)
        tyre_temp = clamp(88 + wear * 20 + math.sin(t * 0.4) * 4, 70, 130)
        lap_delta = s["delta"] + math.sin(t * 0.2) * 0.15
        sector = clamp(27 + wear * 1.5 + rnd(-0.3, 0.3), 24, 32)

        point = {
            "t": round(t, 1), "speed": round(speed), "throttle": round(throttle), "brake": round(brake),
            "rpm": round(rpm), "tyreTemp": round(tyre_temp), "lapDelta": round(lap_delta, 2), "sector": round(sector, 2),
        }
        self.telemetry_buffer.append(point)
        if len(self.telemetry_buffer) > 30:
            self.telemetry_buffer.pop(0)
        return point

    # ------------------------------------------------------------------
    def advance(self, wall_dt):
        """Called frequently by the background loop. wall_dt is real seconds elapsed."""
        s = self.state
        if not s["running"]:
            return
        scaled = wall_dt * s["speed"]
        self.t_sec += scaled
        self.tele_accum += scaled
        self.lap_accum += scaled
        if self.tele_accum >= 0.5:
            self.tele_accum = 0.0
            self.tick_telemetry()
        if self.lap_accum >= 3.2:
            self.lap_accum = 0.0
            self.tick_lap()

    # ------------------------------------------------------------------
    def get_tyre_analytics(self):
        s = self.state
        out = []
        offsets = {"soft": 8, "medium": 0, "hard": -6}
        for key, c in COMPOUNDS.items():
            age = max(0, s["tyreAge"] - offsets[key]) if key != s["compound"] else s["tyreAge"]
            wear = self.tyre_wear_pct(key, age)
            wear_label = "HIGH" if wear > 60 else "MEDIUM" if wear > 30 else "LOW"
            out.append({
                "key": key, "label": c["label"], "code": c["code"], "color": c["color"],
                "wear": round(wear), "wearLabel": wear_label,
                "remainingLaps": self.remaining_laps(key, age),
                "predictedLapTime": round(self.predicted_lap_time(key, age, s["baseLap"]), 2),
            })
        return out

    def get_degradation_curve(self, stint_len=30):
        s = self.state
        curves = {}
        for key, c in COMPOUNDS.items():
            curves[key] = {
                "label": c["label"], "color": c["color"],
                "data": [round(self.predicted_lap_time(key, lap, s["baseLap"]), 2) for lap in range(1, stint_len + 1)],
            }
        return curves

    def get_competitors_public(self):
        out = []
        for c in sorted(self.state["competitors"], key=lambda x: x["position"]):
            closing = c["closing"]
            risk = "CRITICAL" if closing > 0.5 else "HIGH" if closing > 0.25 else "MEDIUM" if closing > 0 else "LOW"
            out.append({
                "car": c["car"], "name": c["name"], "team": c["team"], "me": bool(c.get("me")),
                "position": c["position"], "compound": c["compound"], "compoundLabel": COMPOUNDS[c["compound"]]["label"],
                "compoundColor": COMPOUNDS[c["compound"]]["color"], "tyreAge": c["tyreAge"],
                "lastLap": round(c["lastLap"], 3), "gap": round(c["gap"], 1),
                "trend": "up" if c["pace"] < 0 else "down", "undercutRisk": risk,
            })
        return out

    def get_weather_public(self):
        s = self.state
        return {"trackTemp": round(s["trackTemp"]), "airTemp": round(s["airTemp"]),
                "rain": round(s["rain"]), "wind": round(s["wind"]), "grip": round(s["grip"])}

    def get_state_public(self):
        s = self.state
        return {
            "lap": s["lap"], "totalLaps": s["totalLaps"], "position": s["position"],
            "compound": s["compound"], "compoundLabel": COMPOUNDS[s["compound"]]["label"],
            "tyreAge": s["tyreAge"], "lapTime": round(s["lapTime"], 3), "delta": round(s["delta"], 3),
            "flag": s["flag"], "running": s["running"], "speed": s["speed"],
            "weather": self.get_weather_public(),
        }

    # ------------------------------------------------------------------
    def run_monte_carlo(self, tyre="medium", start_position=2, weather="dry", sc_probability=0.15, iterations=1000):
        strategies = ["PIT NOW", "PIT +1", "PIT +2", "STAY OUT"]
        results = {st: {"positions": [], "times": []} for st in strategies}

        for _ in range(iterations):
            for st in strategies:
                wet_penalty = rnd(1, 4) if weather == "wet" else (rnd(0, 2) if weather == "changeable" else 0)
                sc_hit = random.random() < sc_probability
                pit_loss_rand = rnd(10, 15) if sc_hit else rnd(19, 24)
                deg_rand = rnd(0.8, 1.25)
                trac_rand = rnd(-0.6, 0.6)
                if st == "PIT NOW":
                    pos_change = rnd(-0.5, 1.5) - (1 if sc_hit else 0)
                    time_cost = pit_loss_rand * 0.4 + deg_rand * 2 + wet_penalty
                elif st == "PIT +1":
                    pos_change = rnd(-0.3, 1.8) - (0.6 if sc_hit else 0)
                    time_cost = pit_loss_rand * 0.45 + deg_rand * 2.4 + wet_penalty
                elif st == "PIT +2":
                    pos_change = rnd(0, 2.2) - (0.3 if sc_hit else 0)
                    time_cost = pit_loss_rand * 0.5 + deg_rand * 2.9 + wet_penalty
                else:  # STAY OUT
                    pos_change = rnd(0.2, 3) + trac_rand - (1.2 if sc_hit else 0)
                    time_cost = deg_rand * 4.6 + wet_penalty * 1.4
                final_pos = clamp(start_position + pos_change, 1, 12)
                results[st]["positions"].append(final_pos)
                results[st]["times"].append(time_cost)

        summary = []
        for st in strategies:
            arr = results[st]["positions"]
            mean = sum(arr) / len(arr)
            variance = sum((p - mean) ** 2 for p in arr) / len(arr)
            success = sum(1 for p in arr if p <= start_position + 0.5) / len(arr) * 100
            risk = "HIGH" if variance > 2.2 else "MEDIUM" if variance > 1.0 else "LOW"
            summary.append({
                "strategy": st, "expectedPosition": round(mean, 2),
                "successProbability": round(success, 1), "risk": risk, "variance": round(variance, 2),
            })
        return {"iterations": iterations, "params": {"tyre": tyre, "startPosition": start_position,
                "weather": weather, "scProbability": sc_probability}, "summary": summary}


engine = RaceEngine()
