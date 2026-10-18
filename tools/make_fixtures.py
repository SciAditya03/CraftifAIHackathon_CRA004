"""Regenerate deterministic synthetic contract fixtures in tests/samples/.

These are SYNTHETIC records following the frozen event contract. They are not
PipeGen output and must never be presented as live-run evidence.
"""
import json
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "tests", "samples")


def ev(n, sec, track, etype="ZONE_INTRUSION", status="active"):
    return {
        "schema_version": "1.0",
        "event_id": f"{n * 11111111:08d}-0000-4000-8000-000000000000",
        "event_type": etype,
        "timestamp_utc": f"2026-10-18T12:00:{sec:02d}Z",
        "camera_id": "video-demo-01",
        "track_id": track,
        "class_name": "person",
        "confidence": 0.91,
        "zone_id": "restricted-zone-01",
        "severity": "high",
        "status": status,
        "source": "synthetic-fixture",
    }


def write(name, lines):
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as fh:
        for l in lines:
            fh.write((l if isinstance(l, str) else json.dumps(l)) + "\n")


os.makedirs(OUT, exist_ok=True)
write("fixture_single_intrusion.jsonl", [ev(1, 1, 12)])
write("fixture_duplicate_intrusion.jsonl", [ev(1, 1, 12), ev(2, 2, 12)])
write("fixture_null_track.jsonl", [ev(1, 1, None), ev(2, 2, None)])
write("fixture_malformed.jsonl", [ev(1, 1, 7), '{"broken json', '{"event_type":"ZONE_INTRUSION"}', "[1,2]"])
write("fixture_empty.jsonl", [])
