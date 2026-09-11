"""
TrackShift Race Engineer — a deterministic analysis assistant.

There is no external LLM configured for this hackathon build. Rather than
fake an AI backend, this module answers a fixed set of question intents by
reading the SAME computed metrics the dashboards display (degradation
models, compound comparisons, lap forensics) and formatting them into a
sentence. It never invents a number that isn't already sitting in the
analysis bundle passed to it.

If a question doesn't match a known intent, it says so and lists example
questions — it does not attempt a free-form guess.
"""
import re

EXAMPLE_QUESTIONS = [
    "Why is the Medium degrading?",
    "Which tyre is most consistent?",
    "Why was Lap 24 slow?",
    "When should we pit?",
    "Which compound is best for a long stint?",
    "How much of the slowdown is actually tyre wear?",
    "Which laps should be excluded?",
]

_LAP_NUM_RE = re.compile(r"lap\s*#?\s*(\d+)", re.IGNORECASE)
_COMPOUND_RE = re.compile(r"\b(soft|medium|hard)\b", re.IGNORECASE)


def _find_compound(question, known_compounds):
    m = _COMPOUND_RE.search(question)
    if m:
        key = m.group(1).lower()
        if key in known_compounds:
            return key
    return None


def _find_lap_number(question):
    m = _LAP_NUM_RE.search(question)
    return int(m.group(1)) if m else None


def answer_question(question, context):
    """
    context is a dict assembled by the API layer:
        {
          "currentStint": <stint analysis dict from analyze_session>,
          "allStints": {stintId: stint dict, ...},
          "compare": {compound: comparison row, ...},
          "degModel": <current stint's degradation model>,
          "lapExplanations": {lapNumber: explanation dict, ...}  (current stint only)
        }
    """
    q = question.strip()
    ql = q.lower()
    compare = context.get("compare", {})
    current = context.get("currentStint")
    deg = context.get("degModel", {})

    # -- "why is <compound> degrading" ------------------------------------------------
    compound = _find_compound(ql, compare.keys())
    if compound and ("degrad" in ql or "wear" in ql):
        row = compare.get(compound)
        if not row or row.get("insufficientData"):
            return f"There isn't enough clean data on the {compound.upper()} compound yet to estimate its degradation reliably."
        return (
            f"The {compound.upper()} tyre is currently showing an estimated degradation of "
            f"{row['degradationRate']:.3f} sec/lap (confidence {row['confidence']}%), based on "
            f"{row['lapCount']} laps across {row['stintCount']} stint(s). This is the corrected rate — "
            f"after removing fuel burn, traffic-affected laps and track evolution from the raw lap times."
        )

    # -- "which tyre is most consistent" -----------------------------------------------
    if "consistent" in ql or "consistency" in ql:
        rows = [r for r in compare.values() if not r.get("insufficientData") and r.get("consistency") is not None]
        if not rows:
            return "Not enough clean laps across compounds yet to compare consistency."
        best = min(rows, key=lambda r: r["consistency"])
        return (
            f"{best['compound'].upper()} is currently the most consistent compound, with a residual "
            f"spread of ±{best['consistency']:.3f}s around its fitted degradation curve — the tightest "
            f"of the compounds tested this session."
        )

    # -- "why was lap N slow" -----------------------------------------------------------
    lap_num = _find_lap_number(ql)
    if lap_num is not None and ("slow" in ql or "why" in ql):
        exp = context.get("lapExplanations", {}).get(lap_num)
        if not exp:
            return f"I don't have Lap {lap_num} in the currently selected stint — pick a stint that includes it and ask again."
        c = exp["contributions"]
        parts = ", ".join(f"{_label(k)} {v:+.2f}s" for k, v in c.items())
        return (
            f"Lap {lap_num} was {exp['rawDelta']:+.2f}s vs the stint baseline. Breaking that down: {parts}. "
            f"The primary cause was {exp['primaryCause']}."
        )

    # -- "when should we pit" ------------------------------------------------------------
    if "pit" in ql and ("when" in ql or "should" in ql):
        pit = context.get("pitWindow")
        if not pit or pit.get("insufficientData"):
            return "Not enough clean laps on the current stint to recommend a pit window yet."
        if pit["recommendedWindowLabel"].startswith("hold"):
            return f"Recommended: {pit['recommendedWindowLabel']}. {pit['reason']}"
        return f"Recommended: pit {pit['recommendedWindowLabel']}. {pit['reason']}"

    # -- "which compound is best for a long stint" ---------------------------------------
    if "long stint" in ql or ("best" in ql and "compound" in ql):
        rows = [r for r in compare.values() if not r.get("insufficientData")]
        if not rows:
            return "Not enough data across compounds yet to recommend one for a long stint."
        best = min(rows, key=lambda r: r["degradationRate"])
        return (
            f"For a long stint, {best['compound'].upper()} looks strongest — its estimated degradation rate "
            f"({best['degradationRate']:.3f} sec/lap) is the lowest of the compounds tested, with an estimated "
            f"expected life of about {best['expectedLifeLaps']} competitive laps."
        )

    # -- "how much of the slowdown is actually tyre wear" ---------------------------------
    if ("how much" in ql and ("tyre" in ql or "wear" in ql)) or "actually tyre" in ql:
        if not current or deg.get("insufficientData"):
            return "Not enough clean laps on the current stint to isolate tyre wear from the raw slowdown yet."
        valid = [l for l in current["laps"] if not l["excluded"]]
        if len(valid) < 2:
            return "Not enough clean laps on the current stint to isolate tyre wear from the raw slowdown yet."
        raw_slowdown = valid[-1]["lapTime"] - valid[0]["lapTime"]
        corrected_slowdown = valid[-1]["correctedLapTime"] - valid[0]["correctedLapTime"]
        return (
            f"Across this stint the raw lap time changed by {raw_slowdown:+.2f}s, but after correcting for "
            f"estimated fuel burn, traffic-affected laps and track evolution, the tyre-attributable change is "
            f"approximately {corrected_slowdown:+.2f}s (estimated degradation rate: "
            f"{deg.get('degradationRate', 0):.3f} sec/lap, confidence {deg.get('confidence', 0)}%)."
        )

    # -- "which laps should be excluded" ---------------------------------------------------
    if "exclud" in ql or "invalid" in ql or "bad lap" in ql:
        if not current:
            return "No stint selected."
        excluded = [l["lapNumber"] for l in current["laps"] if l["excluded"]]
        if not excluded:
            return "No laps in the current stint were flagged for exclusion — all laps passed the validity checks."
        return (
            f"{len(excluded)} lap(s) were excluded from the degradation model for this stint: "
            f"{', '.join(str(n) for n in excluded)} — flagged for traffic, flags, pit activity, or abnormal sectors."
        )

    return (
        "I can only answer from what's actually been calculated for the current session — try one of these:\n"
        + "\n".join(f"• {q}" for q in EXAMPLE_QUESTIONS)
    )


def _label(key):
    return {
        "tyreDegradation": "Tyre",
        "traffic": "Traffic",
        "fuelEffect": "Fuel",
        "trackEvolution": "Track evolution",
        "driverVariation": "Driver variation",
    }.get(key, key)
