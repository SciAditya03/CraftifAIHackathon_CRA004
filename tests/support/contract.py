"""Validator for the FROZEN event contract (docs/event-contract in master plan, schema 1.0).

This is a QA-side checker, NOT a production event engine. It only decides whether a
dict conforms to the agreed contract, so it can be used against Person 2's output.
"""
import math
import re
import uuid

SCHEMA_VERSION = "1.0"
EVENT_TYPES = {"ZONE_INTRUSION", "ZONE_CLEAR", "SYSTEM_HEALTH"}
REQUIRED = [
    "schema_version", "event_id", "event_type", "timestamp_utc", "camera_id",
    "track_id", "class_name", "confidence", "zone_id", "severity", "status", "source",
]
NULLABLE = {"track_id", "confidence", "zone_id", "class_name"}
_TS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|\+00:00)$")


def validate_event(ev):
    """Return a list of error strings; empty list means valid."""
    if not isinstance(ev, dict):
        return ["event is not an object"]
    errs = []
    for k in REQUIRED:
        if k not in ev:
            errs.append(f"missing field: {k}")
    if errs:
        return errs
    if ev["schema_version"] != SCHEMA_VERSION:
        errs.append(f"schema_version must be {SCHEMA_VERSION!r}")
    try:
        uuid.UUID(str(ev["event_id"]))
    except ValueError:
        errs.append("event_id is not a UUID")
    if ev["event_type"] not in EVENT_TYPES:
        errs.append(f"unknown event_type {ev['event_type']!r}")
    ts = ev["timestamp_utc"]
    if not isinstance(ts, str) or not _TS.match(ts):
        errs.append("timestamp_utc must be ISO-8601 UTC")
    for k in ("camera_id", "severity", "status", "source"):
        if not isinstance(ev[k], str) or not ev[k]:
            errs.append(f"{k} must be a non-empty string")
    t = ev["track_id"]
    if t is not None and (isinstance(t, bool) or not isinstance(t, int) or t < 0):
        errs.append("track_id must be a non-negative int or null")
    c = ev["confidence"]
    if c is not None:
        if isinstance(c, bool) or not isinstance(c, (int, float)) or not math.isfinite(c) or not 0 <= c <= 1:
            errs.append("confidence must be a number in [0,1] or null")
    for k in ("class_name", "zone_id"):
        if ev[k] is not None and not isinstance(ev[k], str):
            errs.append(f"{k} must be a string or null")
    return errs
