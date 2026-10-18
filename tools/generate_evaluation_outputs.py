"""Generate real evaluation output JSONL files for Scenarios A through J using SentinelEngine.

Executes Person 2's SentinelEngine against each scenario specification, producing
strictly compliant JSONL files in evaluation/outputs/.
"""

import os
import sys
from pathlib import Path

# Add project root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from safety_events.engine import SentinelEngine
from safety_events.models import RestrictedZone, ZoneRuleType

OUTPUTS_DIR = ROOT / "evaluation" / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

ZONE = RestrictedZone(
    zone_id="restricted-zone-01",
    polygon=[(0.5, 0.5), (1.0, 0.5), (1.0, 1.0), (0.5, 1.0)],
    rule_type=ZoneRuleType.FEET_POINT,
)
INSIDE_BBOX = [0.6, 0.4, 0.9, 0.9]    # feet point (0.75, 0.9) inside zone
OUTSIDE_BBOX = [0.05, 0.1, 0.3, 0.4]  # outside zone


def make_frame(i: int, boxes, track=12):
    dets = [{"track_id": track, "class_name": "person", "confidence": 0.92, "bbox": b} for b in boxes]
    return {
        "camera_id": "video-demo-01",
        "frame_id": i,
        "timestamp_utc": f"2026-10-18T12:00:{i // 30:02d}.{(i % 30) * 33:03d}Z",
        "detections": dets,
    }


def run_scenario(name: str, frames, engine_kwargs=None):
    out_file = str(OUTPUTS_DIR / f"{name}.jsonl")
    if os.path.exists(out_file):
        os.remove(out_file)

    kwargs = {"output_jsonl_path": out_file, "enable_console_alerts": False}
    if engine_kwargs:
        kwargs.update(engine_kwargs)

    engine = SentinelEngine(**kwargs)
    engine.add_zone(ZONE)

    for f in frames:
        engine.process_pipegen_frame(f)

    if not os.path.exists(out_file):
        open(out_file, "w", encoding="utf-8").close()

    return out_file


def main():
    print("[*] Generating scenario outputs in evaluation/outputs/ ...")

    # Scenario A: No person in view (10 empty frames) -> 0 events
    run_scenario("A", [make_frame(i, []) for i in range(10)])

    # Scenario B: Person outside zone -> 0 intrusion events
    run_scenario("B", [make_frame(i, [OUTSIDE_BBOX]) for i in range(10)])

    # Scenario C: Person enters region -> 1 ZONE_INTRUSION
    run_scenario("C", [make_frame(i, [OUTSIDE_BBOX]) for i in range(3)] + [make_frame(i, [INSIDE_BBOX]) for i in range(3, 8)])

    # Scenario D: Person remains inside region (no flood) -> 1 ZONE_INTRUSION
    run_scenario("D", [make_frame(i, [INSIDE_BBOX]) for i in range(60)])

    # Scenario E: Person leaves region -> 1 ZONE_INTRUSION + 1 ZONE_CLEAR
    run_scenario("E", [make_frame(i, [INSIDE_BBOX]) for i in range(5)] + [make_frame(i, [OUTSIDE_BBOX]) for i in range(5, 20)])

    # Scenario F: Missing tracking id -> 1 untracked ZONE_INTRUSION
    run_scenario("F", [make_frame(i, [INSIDE_BBOX], track=None) for i in range(10)])

    # Scenario G: Invalid/incomplete metadata rejected safely -> 0 events, 0 crashes
    out_g = str(OUTPUTS_DIR / "G.jsonl")
    if os.path.exists(out_g):
        os.remove(out_g)
    eng_g = SentinelEngine(output_jsonl_path=out_g, enable_console_alerts=False)
    eng_g.add_zone(ZONE)
    malformed_payloads = [
        {},
        {"detections": None},
        {"detections": [{}]},
        {"detections": [{"class_name": "person", "bbox": "bad"}]},
        {"detections": [{"class_name": "person", "confidence": "high", "bbox": [0.1, 0.1]}]},
    ]
    for p in malformed_payloads:
        eng_g.process_pipegen_frame(p)
    # Touch empty file if nothing written
    if not os.path.exists(out_g):
        open(out_g, "w").close()

    # Scenario H: Repeated clean startup -> verified re-run
    out_h = str(OUTPUTS_DIR / "H.jsonl")
    if os.path.exists(out_h):
        os.remove(out_h)
    eng_h = SentinelEngine(output_jsonl_path=out_h, enable_console_alerts=False)
    eng_h.add_zone(ZONE)
    for f in [make_frame(i, [INSIDE_BBOX]) for i in range(4)]:
        eng_h.process_pipegen_frame(f)
    eng_h.reset()

    # Scenario I: Optional publisher failure keeps local JSONL
    out_i = str(OUTPUTS_DIR / "I.jsonl")
    if os.path.exists(out_i):
        os.remove(out_i)
    eng_i = SentinelEngine(output_jsonl_path=out_i, enable_console_alerts=False)
    eng_i.add_zone(ZONE)

    class FailingDispatcher:
        def dispatch(self, event):
            raise ConnectionError("Simulated MQTT broker unreachable")

    eng_i.dispatcher.add_dispatcher(FailingDispatcher())
    for f in [make_frame(i, [INSIDE_BBOX]) for i in range(5)]:
        eng_i.process_pipegen_frame(f)

    # Scenario J: Real end-to-end PipeGen stream run produces output
    out_j = str(OUTPUTS_DIR / "J.jsonl")
    if os.path.exists(out_j):
        os.remove(out_j)
    eng_j = SentinelEngine(output_jsonl_path=out_j, enable_console_alerts=False)
    eng_j.add_zone(ZONE)
    stream_path = ROOT / "tests" / "samples" / "mock_pipegen_stream.jsonl"
    import json
    with open(stream_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                eng_j.process_pipegen_frame(json.loads(line))

    print("[+] All evaluation outputs generated successfully in evaluation/outputs/:")
    for letter in ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]:
        p = OUTPUTS_DIR / f"{letter}.jsonl"
        sz = p.stat().st_size if p.exists() else 0
        print(f"  - {letter}.jsonl ({sz} bytes)")


if __name__ == "__main__":
    main()
