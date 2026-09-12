"""Decision-value and resource-allocation layer for TrackShift.

Uses normalized Resource Credits rather than claiming real F1 financial costs.
The goal is to quantify whether additional analysis/testing is worth doing.
"""
from copy import deepcopy
import math

DEFAULT_ACTIONS = [
    {"key": "additional_tyre_analysis", "label": "Additional tyre analysis", "cost": 10.0, "confidence_gain": 0.08, "impact_multiplier": 0.75},
    {"key": "setup_simulation", "label": "Setup simulation", "cost": 8.0, "confidence_gain": 0.05, "impact_multiplier": 1.00},
    {"key": "long_run_simulation", "label": "Long-run simulation", "cost": 20.0, "confidence_gain": 0.11, "impact_multiplier": 0.90},
    {"key": "extra_tyre_run", "label": "Extra tyre run", "cost": 15.0, "confidence_gain": 0.12, "impact_multiplier": 1.15},
]


def _clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def decision_sensitivity(deg, current_age, strategy_options):
    """Estimate how much the recommended strategy moves when degradation is uncertain."""
    confidence = _clamp((deg.get("confidence", 0) or 0) / 100)
    rate = max(0.0, float(deg.get("degradationRate", 0) or 0))
    accel = max(0.0, float(deg.get("degradationAcceleration", 0) or 0))
    uncertainty = max(0.002, rate * (1.0 - confidence) * 0.65)
    scenario_costs = []
    for factor in (max(0.35, 1 - uncertainty / max(rate, 0.01)), 1.0, 1 + uncertainty / max(rate, 0.01)):
        vals = []
        for opt in strategy_options:
            delay = opt.get("delay", 0)
            cost = sum(rate * factor * (current_age + i) + accel * (current_age + i) ** 2 for i in range(delay))
            cost += opt.get("pitLoss", 0) or 0
            vals.append(cost)
        if vals:
            scenario_costs.append(min(range(len(vals)), key=lambda i: vals[i]))
    spread = len(set(scenario_costs)) / max(1, len(strategy_options))
    sensitivity = _clamp(spread * 1.35 + (1 - confidence) * 0.35)
    label = "LOW" if sensitivity < .25 else "MEDIUM" if sensitivity < .55 else "HIGH"
    return {"score": round(sensitivity * 100), "label": label, "uncertaintyRate": round(uncertainty, 4)}


def calculate_decision_value(deg, current_age, strategy_options, actions=None, budget=100.0):
    actions = actions or DEFAULT_ACTIONS
    confidence = _clamp((deg.get("confidence", 0) or 0) / 100)
    sensitivity = decision_sensitivity(deg, current_age, strategy_options)
    base_risk_seconds = max(0.02, (1 - confidence) * (0.35 + sensitivity["score"] / 100 * 1.8))
    results = []
    for raw in actions:
        a = deepcopy(raw)
        cost = float(a.get("cost", 0))
        confidence_gain = float(a.get("confidence_gain", 0))
        impact = float(a.get("impact_multiplier", 1))
        # Value is a normalized expected race-performance-equivalent benefit.
        # It intentionally depends on uncertainty and decision sensitivity.
        expected_value = base_risk_seconds * sensitivity["score"] / 100 * confidence_gain * 8.0 * impact
        if sensitivity["label"] == "LOW":
            expected_value *= 0.45
        roi = expected_value / cost if cost > 0 else 0
        results.append({
            "key": a["key"], "label": a["label"], "cost": round(cost, 2),
            "expectedValue": round(expected_value, 3), "netValue": round(expected_value - cost / 100, 3),
            "roi": round(roi, 2), "projectedConfidence": round(min(99, confidence * 100 + confidence_gain * 100)),
            "affordable": cost <= budget,
        })
    # A test is worthwhile only when its expected value is greater than its normalized cost.
    viable = [r for r in results if r["affordable"]]
    best = max(viable, key=lambda r: r["netValue"]) if viable else None
    recommend_test = bool(best and best["netValue"] > 0.02 and sensitivity["label"] != "LOW")
    if not recommend_test:
        recommendation = {"action": "save_resources", "label": "Do not spend resources yet", "reason": "Current uncertainty is unlikely to change the decision enough to justify another analysis."}
    else:
        recommendation = {"action": best["key"], "label": f"Run {best['label'].lower()}", "reason": "The expected decision value exceeds the normalized resource cost and the strategy is sensitive to current uncertainty."}
    return {
        "budget": round(budget, 2), "confidence": round(confidence * 100),
        "decisionSensitivity": sensitivity, "baseRiskSeconds": round(base_risk_seconds, 3),
        "actions": sorted(results, key=lambda x: x["netValue"], reverse=True),
        "recommendation": recommendation,
    }


def optimize_resource_budget(actions, budget):
    """Greedy knapsack approximation for transparent resource allocation."""
    items = []
    for a in actions:
        cost = float(a.get("cost", 0))
        value = float(a.get("expectedValue", 0))
        if cost > 0:
            items.append((value / cost, value, cost, a))
    items.sort(reverse=True, key=lambda x: x[0])
    selected, spent, value = [], 0.0, 0.0
    for _, v, c, a in items:
        if spent + c <= budget:
            selected.append(a)
            spent += c
            value += v
    return {"budget": round(budget, 2), "spent": round(spent, 2), "remaining": round(budget - spent, 2), "expectedValue": round(value, 3), "selected": selected}
