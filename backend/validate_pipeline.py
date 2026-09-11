import json
import os
import urllib.request

B = os.environ.get("TRACKSHIFT_API", "http://127.0.0.1:8000")


def get(path):
    with urllib.request.urlopen(B + path) as r:
        return json.loads(r.read())


def post(path, body):
    req = urllib.request.Request(
        B + path, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


print("=== meta / stints ===")
meta = get("/tyre-intel/meta")
stints = get("/tyre-intel/stints")
print("drivers:", [d["code"] for d in meta["drivers"]])
print("compounds:", list(meta["compounds"].keys()))
print("default stint:", stints["defaultStintId"])
for s in stints["stints"]:
    print(" ", s["stintId"], s["compound"], "conf", s["degradationConfidence"], "laps", s["stintLength"])

print("\n=== overview ===")
ov = get("/tyre-intel/overview")
print(json.dumps(ov, indent=2))
assert not ov["insufficientData"]
assert 0 <= ov["confidence"] <= 100

print("\n=== degradation hero ===")
deg = get("/tyre-intel/degradation")
print(json.dumps({k: v for k, v in deg.items() if k != "curve"}, indent=2))
assert not deg["insufficientData"]
# sanity: corrected != raw (the whole point of the feature)
assert deg["rawObservedChange"] != deg["estimatedTrueDegradation"]

print("\n=== compare compounds ===")
cmp = get("/tyre-intel/compare")
for k, v in cmp["compounds"].items():
    print(" ", k, v.get("degradationRate"), v.get("degradationLabel"), v.get("initialPaceLabel"), v.get("confidence"))
rates = {k: v["degradationRate"] for k, v in cmp["compounds"].items() if not v.get("insufficientData")}
assert rates["soft"] > rates["medium"] > rates["hard"], f"expected soft>medium>hard, got {rates}"
paces = {k: v["avgInitialPace"] for k, v in cmp["compounds"].items() if not v.get("insufficientData")}
assert paces["soft"] < paces["medium"] < paces["hard"], f"expected soft fastest, got {paces}"
print("compound ranking assertions PASSED")

print("\n=== FORENSICS INVARIANT CHECK (every lap, every stint) ===")
total_checked = 0
max_error = 0.0
for s in stints["stints"]:
    sid = s["stintId"]
    driver = s["driver"]
    lapsResp = get(f"/tyre-intel/laps?stintId={sid}")
    for lap in lapsResp["laps"]:
        ln = lap["lapNumber"]
        exp = get(f"/tyre-intel/lap-forensics?driver={driver}&lapNumber={ln}")
        contrib_sum = sum(exp["contributions"].values())
        error = abs(contrib_sum - exp["rawDelta"])
        max_error = max(max_error, error)
        assert error < 0.01, f"INVARIANT BROKEN: {sid} lap {ln}: sum={contrib_sum} rawDelta={exp['rawDelta']}"
        total_checked += 1
print(f"checked {total_checked} laps across {len(stints['stints'])} stints, max invariant error = {max_error:.6f}s")
print("INVARIANT HOLDS for all laps")

print("\n=== remaining life ===")
life = get("/tyre-intel/remaining-life")
print(json.dumps(life, indent=2)[:400])

print("\n=== strategy simulator ===")
strat = post("/tyre-intel/strategy", {"stintId": stints["defaultStintId"], "nextCompound": "hard"})
print(json.dumps(strat, indent=2))
assert not strat["insufficientData"]
assert strat["recommendedOption"] in ("stay", "now", "plus3")

print("\n=== AI race engineer ===")
for q in [
    "Why is the Medium degrading?",
    "Which tyre is most consistent?",
    "When should we pit?",
    "Which compound is best for a long stint?",
    "How much of the slowdown is actually tyre wear?",
    "Which laps should be excluded?",
    "What's your favorite color?",
]:
    a = post("/tyre-intel/ask", {"question": q})
    print(f"Q: {q}\nA: {a['answer']}\n")

print("=== ALL CHECKS PASSED ===")
