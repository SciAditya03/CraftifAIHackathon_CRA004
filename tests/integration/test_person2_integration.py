"""Integration tests: Person 2's SentinelEngine fed PipeGen-format frame payloads.

Input is SYNTHETIC (frame payloads shaped like tests/samples/mock_pipegen_stream.jsonl,
bbox = [left, top, right, bottom] normalized). It is NOT live PipeGen output; scenario J
(real pipeline) stays blocked. Output JSONL is validated against the frozen contract.
"""
import json

import pytest

from contract import validate_event

se = pytest.importorskip("safety_events", reason="BLOCKED: safety_events package not present")
from safety_events.engine import SentinelEngine  # noqa: E402
from safety_events.models import RestrictedZone  # noqa: E402

ZONE = RestrictedZone(zone_id="restricted-zone-01", polygon=[(0.5, 0.5), (1.0, 0.5), (1.0, 1.0), (0.5, 1.0)])
INSIDE = [0.6, 0.4, 0.9, 0.9]    # feet point (0.75, 0.9) inside zone
OUTSIDE = [0.05, 0.1, 0.3, 0.4]  # far from zone


def frame(i, boxes, track=12):
    dets = [{"track_id": track, "class_name": "person", "confidence": 0.9, "bbox": b} for b in boxes]
    return {"camera_id": "video-demo-01", "frame_id": i,
            "timestamp_utc": f"2026-10-18T12:00:{i // 30:02d}.{(i % 30) * 33:03d}Z", "detections": dets}


@pytest.fixture
def engine(tmp_path):
    e = SentinelEngine(output_jsonl_path=str(tmp_path / "ev.jsonl"), enable_console_alerts=False)
    e.add_zone(ZONE)
    return e


def run(engine, frames):
    for f in frames:
        engine.process_pipegen_frame(f)
    return [json.loads(l) for l in open(engine.writer.output_path, encoding="utf-8") if l.strip()] \
        if _exists(engine) else []


def _exists(engine):
    import os
    return os.path.exists(engine.writer.output_path)


def types(evs, t):
    return [e for e in evs if e["event_type"] == t]


@pytest.mark.integration
def test_A_no_person(engine):
    assert run(engine, [frame(i, []) for i in range(10)]) == []


@pytest.mark.integration
def test_B_outside_zone(engine):
    evs = run(engine, [frame(i, [OUTSIDE]) for i in range(10)])
    assert types(evs, "ZONE_INTRUSION") == [], evs


@pytest.mark.integration
def test_C_enter_zone_one_event_and_contract_valid(engine):
    evs = run(engine, [frame(i, [OUTSIDE]) for i in range(3)] + [frame(i, [INSIDE]) for i in range(3, 8)])
    intr = types(evs, "ZONE_INTRUSION")
    assert len(intr) == 1, f"expected 1 intrusion, got {len(intr)}"
    for e in evs:
        assert validate_event(e) == [], f"contract violation: {validate_event(e)} in {e}"


@pytest.mark.integration
def test_D_stay_inside_no_flood(engine):
    evs = run(engine, [frame(i, [INSIDE]) for i in range(60)])
    assert len(types(evs, "ZONE_INTRUSION")) == 1, "duplicate alerts while track remains inside"


@pytest.mark.integration
def test_E_leave_zone_emits_clear(engine):
    evs = run(engine, [frame(i, [INSIDE]) for i in range(5)] + [frame(i, [OUTSIDE]) for i in range(5, 20)])
    assert len(types(evs, "ZONE_INTRUSION")) == 1
    assert len(types(evs, "ZONE_CLEAR")) == 1, evs


@pytest.mark.integration
def test_F_missing_track_id_no_crash_no_invented_id(engine):
    evs = run(engine, [frame(i, [INSIDE], track=None) for i in range(10)])
    for e in evs:
        assert e["track_id"] is None, f"invented track id: {e['track_id']}"
        assert validate_event(e) == []
    assert len(types(evs, "ZONE_INTRUSION")) <= 1, "untracked person flooded alerts"


@pytest.mark.integration
@pytest.mark.parametrize("payload", [
    {},
    pytest.param({"detections": None}, marks=pytest.mark.xfail(
        strict=True, reason="ISSUE-1 (Person 2): adapters.parse_pipegen_frame raises TypeError on null detections")),
    {"detections": [{}]}, {"detections": [{"class_name": "person", "bbox": "bad"}]},
    {"detections": [{"class_name": "person", "confidence": "high", "bbox": [0.1, 0.1]}]},
])
def test_G_invalid_metadata_does_not_crash(engine, payload):
    try:
        engine.process_pipegen_frame(payload)
    except Exception as exc:  # report precisely which input breaks the engine
        pytest.fail(f"engine raised {type(exc).__name__}: {exc} for payload {payload}")


@pytest.mark.integration
def test_I_failing_publisher_keeps_local_jsonl(engine):
    class Boom:
        def dispatch(self, event):
            raise RuntimeError("network down")

    engine.dispatcher.add_dispatcher(Boom())
    evs = run(engine, [frame(i, [INSIDE]) for i in range(5)])
    assert len(types(evs, "ZONE_INTRUSION")) == 1, "local JSONL lost when publisher failed"


@pytest.mark.live
@pytest.mark.skip(reason="BLOCKED: requires real PipeGen/DeepStream run (Person 1); see runbook")
def test_scenario_j_live_pipeline():
    pass
