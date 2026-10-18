"""Evaluation helpers: tolerant JSONL reading, event counting, result rows."""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tests", "support"))
from contract import validate_event  # noqa: E402

RESULT_FIELDS = [
    "scenario_id", "level", "input", "expected_outcome", "observed_outcome",
    "expected_events", "actual_events", "invalid_records", "duplicate_events",
    "status", "error_details", "evidence", "environment",
]


def read_jsonl(path):
    """Return (records, errors). Malformed lines are reported, never raised."""
    records, errors = [], []
    with open(path, "r", encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                errors.append(f"line {n}: {e.msg}")
    return records, errors


def summarize(path, event_type="ZONE_INTRUSION"):
    records, parse_errors = read_jsonl(path)
    valid, invalid = [], len(parse_errors)
    for r in records:
        if validate_event(r):
            invalid += 1
        else:
            valid.append(r)
    matching = [r for r in valid if r["event_type"] == event_type]
    seen, dups = set(), 0
    for r in matching:
        key = (r["track_id"], r["zone_id"], r["status"])
        if r["track_id"] is not None and key in seen:
            dups += 1
        seen.add(key)
    return {"events": len(matching), "invalid": invalid, "duplicates": dups}


def judge(expected, summary):
    """PASS only if count matches and no invalid records."""
    if summary["events"] == expected and summary["invalid"] == 0:
        return "PASS"
    return "FAIL"


def write_results(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=RESULT_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in RESULT_FIELDS})
