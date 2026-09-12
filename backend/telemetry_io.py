"""Normalize user-provided CSV telemetry into TrackShift's documented lap schema."""
import csv
import io
import re

REQUIRED = ["lapNumber", "tyreAge", "lapTime"]
ALIASES = {
    "lap": "lapNumber", "lap_number": "lapNumber", "laptime": "lapTime", "lap_time": "lapTime",
    "tyre_age": "tyreAge", "tireage": "tyreAge", "tire_age": "tyreAge", "compound": "compound",
    "fuel": "fuelLoad", "fuel_load": "fuelLoad", "traffic": "trafficScore", "traffic_score": "trafficScore",
    "sector_1": "sector1", "sector1": "sector1", "sector_2": "sector2", "sector2": "sector2",
    "sector_3": "sector3", "sector3": "sector3", "stint": "stintId", "stint_id": "stintId",
    "driver_code": "driver", "driver_name": "driverName", "flag": "flagStatus", "pit": "pitLap",
    "track_temp": "trackTemperature", "track_temperature": "trackTemperature", "air_temp": "airTemperature",
}


def _key(s):
    return re.sub(r"[^a-z0-9]+", "_", s.strip().lower()).strip("_")


def _bool(v):
    return str(v).strip().lower() in {"1", "true", "yes", "y"}


def normalize_csv(text):
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError("CSV has no header row.")
    mapping = {name: ALIASES.get(_key(name), name) for name in reader.fieldnames}
    rows = []
    for idx, raw in enumerate(reader, start=1):
        row = {mapping[k]: v for k, v in raw.items() if k is not None}
        missing = [k for k in REQUIRED if row.get(k, "") == ""]
        if missing:
            raise ValueError(f"Row {idx}: missing required values: {', '.join(missing)}")
        try:
            lap = {
                "lapNumber": int(float(row["lapNumber"])), "stintLap": int(float(row.get("stintLap") or row["tyreAge"])),
                "driver": str(row.get("driver") or "DRV").upper(), "driverName": str(row.get("driverName") or row.get("driver") or "Driver"),
                "car": int(float(row.get("car") or 0)), "session": str(row.get("session") or "Uploaded"),
                "compound": str(row.get("compound") or "medium").lower(), "compoundLabel": str(row.get("compoundLabel") or row.get("compound") or "MEDIUM").upper(),
                "tyreAge": int(float(row["tyreAge"])), "lapTime": float(row["lapTime"]),
                "sector1": float(row.get("sector1") or 0), "sector2": float(row.get("sector2") or 0), "sector3": float(row.get("sector3") or 0),
                "fuelLoad": float(row.get("fuelLoad") or 0), "fuelEstimated": True,
                "trafficScore": float(row.get("trafficScore") or 0), "trackTemperature": float(row.get("trackTemperature") or 0),
                "airTemperature": float(row.get("airTemperature") or 0), "flagStatus": str(row.get("flagStatus") or "green").lower(),
                "pitLap": _bool(row.get("pitLap", False)),
            }
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Row {idx}: invalid numeric value ({exc}).") from exc
        row["stintId"] = str(row.get("stintId") or f"{lap['driver']}-{lap['compound']}-uploaded")
        lap["stintId"] = row["stintId"]
        rows.append(lap)
    if len(rows) < 3:
        raise ValueError("Upload needs at least 3 laps.")
    return rows
