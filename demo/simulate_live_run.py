"""Interactive live simulation runner demonstrating real-time perception stream and alert output."""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from safety_events.engine import SentinelEngine
from safety_events.models import BoundingBox, RawDetection, ZoneRuleType
from safety_events.zone_rules import create_rectangular_zone


def run_simulation(
    stream_path: str = "tests/samples/mock_pipegen_stream.jsonl",
    output_jsonl: str = "demo/sample_events.jsonl",
    fps: float = 10.0,
    loop: bool = False,
) -> None:
    print("\n" + "=" * 70)
    print("  WORKPLACE SAFETY SENTINEL — LIVE PIPELINE DEMO")
    print("  CraftifAI PipeGen | DeepStream Perception Ingestion")
    print("=" * 70)

    # Initialize SentinelEngine
    engine = SentinelEngine(
        output_jsonl_path=output_jsonl,
        enable_console_alerts=True,
        min_inside_frames=2,
        exit_grace_frames=3,
        emit_clear_events=True,
    )

    # Register safety zone [0.3, 0.3] to [0.7, 0.7] (Robotic Workcell)
    workcell_zone = create_rectangular_zone(
        zone_id="restricted-zone-01",
        x1=0.3,
        y1=0.3,
        x2=0.7,
        y2=0.7,
        name="Robotic Work Envelope",
        rule_type=ZoneRuleType.FEET_POINT,
    )
    engine.add_zone(workcell_zone)

    # Emit initial system health event
    engine.emit_system_health(
        camera_id="video-demo-01",
        message="PipeGen TensorRT engine initialized. Monitoring restricted-zone-01.",
    )

    input_file = Path(stream_path)
    if not input_file.exists():
        print(f"Error: stream file '{stream_path}' not found.")
        return

    delay = 1.0 / max(1.0, fps)
    print(f"[*] Ingesting PipeGen stream from: {stream_path}")
    print(f"[*] Output incident log: {output_jsonl}")
    print(f"[*] Target playback speed: {fps} FPS")
    print("-" * 70)

    iteration = 0
    while True:
        iteration += 1
        with open(input_file, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                payload = json.loads(line)
                events = engine.process_pipegen_frame(payload)
                time.sleep(delay)

        if not loop:
            break

        print("[*] Replaying stream sequence (video loop)...")
        engine.reset()

    print("-" * 70)
    print("PIPELINE EXECUTION METRICS:")
    for k, v in engine.metrics.items():
        print(f"  - {k}: {v}")
    print(f"[*] Recorded events saved to: {output_jsonl}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Workplace Safety Sentinel Live Simulation")
    parser.add_argument("--stream", default="tests/samples/mock_pipegen_stream.jsonl", help="Path to JSONL stream")
    parser.add_argument("--output", default="demo/sample_events.jsonl", help="Output incident JSONL path")
    parser.add_argument("--fps", type=float, default=8.0, help="Simulated playback FPS")
    parser.add_argument("--loop", action="store_true", help="Loop playback repeatedly")
    args = parser.parse_args()

    run_simulation(stream_path=args.stream, output_jsonl=args.output, fps=args.fps, loop=args.loop)
