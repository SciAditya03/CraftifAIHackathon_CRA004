"""End-to-end integration tests simulating realistic multi-frame video inference."""

import datetime
import os
import shutil
import tempfile
import unittest
from safety_events.engine import SentinelEngine
from safety_events.models import BoundingBox, EventType, RawDetection, ZoneRuleType
from safety_events.zone_rules import create_rectangular_zone


class TestEndToEnd(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.output_jsonl = os.path.join(self.test_dir, "incident_log.jsonl")
        self.engine = SentinelEngine(
            output_jsonl_path=self.output_jsonl,
            enable_console_alerts=False,
            min_inside_frames=2,
            exit_grace_frames=3,
            emit_clear_events=True,
        )
        # Define safety zone [0.3, 0.3] to [0.7, 0.7]
        self.zone = create_rectangular_zone(
            zone_id="restricted-zone-assembly",
            x1=0.3,
            y1=0.3,
            x2=0.7,
            y2=0.7,
            name="Robotic Assembly Restricted Zone",
            rule_type=ZoneRuleType.FEET_POINT,
        )
        self.engine.add_zone(self.zone)
        self.start_time = datetime.datetime(2026, 10, 18, 14, 0, 0, tzinfo=datetime.timezone.utc)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_full_intrusion_and_clear_lifecycle(self):
        # 10 Frame Video Sequence:
        # Frames 1-2: Outside zone (x=0.1, y=0.1)
        # Frames 3-4: Enters zone (x=0.5, y=0.5) -> Intrusion emitted on frame 4
        # Frames 5-7: Lingering inside zone (x=0.5, y=0.5) -> Suppressed
        # Frames 8-10: Exits zone (x=0.9, y=0.9) -> Clear emitted on frame 10

        all_emitted = []
        fps_delta = datetime.timedelta(milliseconds=33)

        for frame_idx in range(1, 11):
            curr_time = self.start_time + (frame_idx * fps_delta)

            if frame_idx in (1, 2):
                feet_x, feet_y = 0.1, 0.1  # Outside
            elif frame_idx in (3, 4, 5, 6, 7):
                feet_x, feet_y = 0.5, 0.5  # Inside
            else:
                feet_x, feet_y = 0.9, 0.9  # Outside

            det = RawDetection(
                camera_id="video-demo-01",
                frame_id=frame_idx,
                timestamp_utc=curr_time.isoformat(),
                class_name="person",
                bbox=BoundingBox(left=feet_x - 0.05, top=feet_y - 0.2, right=feet_x + 0.05, bottom=feet_y),
                track_id=101,
                confidence=0.93,
            )

            events = self.engine.process_raw_detections([det], current_time=curr_time)
            all_emitted.extend(events)

        # Total events should be exactly 2: 1 ZONE_INTRUSION and 1 ZONE_CLEAR
        self.assertEqual(len(all_emitted), 2)
        self.assertEqual(all_emitted[0].event_type, EventType.ZONE_INTRUSION)
        self.assertEqual(all_emitted[0].track_id, 101)

        self.assertEqual(all_emitted[1].event_type, EventType.ZONE_CLEAR)
        self.assertEqual(all_emitted[1].track_id, 101)
        self.assertGreater(all_emitted[1].dwell_time_seconds, 0.0)

        # Verify JSONL log file
        logged = self.engine.writer.read_events()
        self.assertEqual(len(logged), 2)
        self.assertEqual(logged[0]["event_type"], "ZONE_INTRUSION")
        self.assertEqual(logged[1]["event_type"], "ZONE_CLEAR")

    def test_pipegen_and_deepstream_ingestion(self):
        # PipeGen ingestion test
        pipegen_msg = {
            "camera_id": "video-demo-01",
            "frame_id": 1,
            "timestamp_utc": self.start_time.isoformat(),
            "detections": [
                {
                    "track_id": 202,
                    "class_name": "person",
                    "confidence": 0.88,
                    "bbox": [0.45, 0.3, 0.55, 0.5],
                }
            ],
        }
        # Frame 1
        self.engine.process_pipegen_frame(pipegen_msg)
        # Frame 2 to confirm intrusion
        pipegen_msg["frame_id"] = 2
        pipegen_msg["timestamp_utc"] = (self.start_time + datetime.timedelta(milliseconds=33)).isoformat()
        events = self.engine.process_pipegen_frame(pipegen_msg)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].track_id, 202)
        self.assertEqual(events[0].event_type, EventType.ZONE_INTRUSION)

    def test_reset_and_replay(self):
        # Run intrusion
        det = RawDetection(
            camera_id="cam-01",
            frame_id=1,
            timestamp_utc=self.start_time.isoformat(),
            class_name="person",
            bbox=BoundingBox(left=0.45, top=0.3, right=0.55, bottom=0.5),
            track_id=303,
            confidence=0.9,
        )
        # 2 frames to trigger
        self.engine.process_raw_detections([det], current_time=self.start_time)
        ev1 = self.engine.process_raw_detections([det], current_time=self.start_time + datetime.timedelta(seconds=1))
        self.assertEqual(len(ev1), 1)

        # Reset engine (simulating video replay)
        self.engine.reset()

        # Re-running detection should re-evaluate cleanly from initial state
        self.engine.process_raw_detections([det], current_time=self.start_time)
        ev2 = self.engine.process_raw_detections([det], current_time=self.start_time + datetime.timedelta(seconds=1))
        self.assertEqual(len(ev2), 1)


if __name__ == "__main__":
    unittest.main()
