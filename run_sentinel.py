"""Top-level CLI runner for Workplace Safety Sentinel."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from safety_events import (
    CompositeDispatcher,
    ConsoleAlertDispatcher,
    JsonlDispatcher,
    JsonlEventWriter,
    MqttDispatcher,
    RawDetection,
    RestrictedZone,
    SentinelEngine,
    WebhookDispatcher,
    ZoneRuleType,
    create_rectangular_zone,
    parse_deepstream_msgbroker,
    parse_pipegen_frame,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Workplace Safety Sentinel — Track A PipeGen / DeepStream Safety Analytics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_sentinel.py --demo
  python run_sentinel.py --stream tests/samples/mock_pipegen_stream.jsonl --fps 15
  python run_sentinel.py --pipegen-json tests/samples/mock_pipegen_stream.jsonl
  python run_sentinel.py --deepstream-json tests/samples/deepstream_sample.json
  python run_sentinel.py --test
        """,
    )
    parser.add_argument("--demo", action="store_true", help="Run interactive demo simulation")
    parser.add_argument("--stream", type=str, help="Stream JSONL file containing frame detections")
    parser.add_argument("--pipegen-json", type=str, help="Process single PipeGen JSON payload file")
    parser.add_argument("--deepstream-json", type=str, help="Process DeepStream nvmsgbroker JSON payload file")
    parser.add_argument("--output", type=str, default="demo/sample_events.jsonl", help="Output incident JSONL path")
    parser.add_argument("--fps", type=float, default=15.0, help="Stream playback FPS")
    parser.add_argument("--mqtt", type=str, default=None, help="Optional MQTT broker host (e.g. localhost)")
    parser.add_argument("--webhook", type=str, default=None, help="Optional HTTP POST alert webhook URL")
    parser.add_argument("--test", action="store_true", help="Run full automated unit test suite")
    parser.add_argument("--no-clear", action="store_true", help="Disable ZONE_CLEAR events")
    args = parser.parse_args()

    if args.test:
        import unittest
        loader = unittest.TestLoader()
        suite = loader.discover("tests", pattern="test_*.py")
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        sys.exit(0 if result.wasSuccessful() else 1)

    if args.demo or (not args.stream and not args.pipegen_json and not args.deepstream_json):
        from demo.simulate_live_run import run_simulation
        stream_file = "tests/samples/mock_pipegen_stream.jsonl"
        run_simulation(stream_path=stream_file, output_jsonl=args.output, fps=args.fps)
        return

    # Initialize Engine
    engine = SentinelEngine(
        output_jsonl_path=args.output,
        enable_console_alerts=True,
        webhook_url=args.webhook,
        mqtt_broker=args.mqtt,
        emit_clear_events=not args.no_clear,
    )

    # Standard Zone Configuration
    zone = create_rectangular_zone(
        zone_id="restricted-zone-01",
        x1=0.3,
        y1=0.3,
        x2=0.7,
        y2=0.7,
        name="Industrial Hazard Perimeter",
        rule_type=ZoneRuleType.FEET_POINT,
    )
    engine.add_zone(zone)
    engine.emit_system_health("video-demo-01", "Sentinel Engine started.")

    if args.pipegen_json:
        with open(args.pipegen_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        events = engine.process_pipegen_frame(data)
        print(f"Processed PipeGen payload: {len(events)} events generated.")

    elif args.deepstream_json:
        with open(args.deepstream_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        events = engine.process_deepstream_msg(data)
        print(f"Processed DeepStream payload: {len(events)} events generated.")

    elif args.stream:
        delay = 1.0 / max(1.0, args.fps)
        with open(args.stream, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                engine.process_pipegen_frame(data)
                time.sleep(delay)
        print(f"\nCompleted streaming. Metrics: {engine.metrics}")


if __name__ == "__main__":
    main()
