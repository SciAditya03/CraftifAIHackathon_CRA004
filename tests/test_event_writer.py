"""Unit tests for JsonlEventWriter and schema validation."""

import os
import shutil
import tempfile
import threading
import unittest
from safety_events.event_writer import JsonlEventWriter, validate_event_dict
from safety_events.models import EventStatus, EventType, SafetyEvent, Severity


class TestEventWriter(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.output_file = os.path.join(self.test_dir, "test_events.jsonl")
        self.writer = JsonlEventWriter(output_path=self.output_file, auto_fsync=False)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_write_and_read_event(self):
        ev = SafetyEvent(
            camera_id="cam-test",
            class_name="person",
            zone_id="restricted-zone-01",
            event_type=EventType.ZONE_INTRUSION,
            severity=Severity.HIGH,
            status=EventStatus.ACTIVE,
            track_id=42,
            confidence=0.95,
        )
        self.writer.write_event(ev)

        events = self.writer.read_events()
        self.assertEqual(len(events), 1)
        logged = events[0]

        self.assertEqual(logged["schema_version"], "1.0")
        self.assertEqual(logged["event_type"], "ZONE_INTRUSION")
        self.assertEqual(logged["camera_id"], "cam-test")
        self.assertEqual(logged["track_id"], 42)
        self.assertAlmostEqual(logged["confidence"], 0.95)
        self.assertEqual(logged["zone_id"], "restricted-zone-01")
        self.assertEqual(logged["severity"], "high")
        self.assertEqual(logged["status"], "active")
        self.assertEqual(logged["source"], "pipegen-deepstream")

    def test_schema_validation_catches_invalid_fields(self):
        # Missing camera_id
        bad_dict = {
            "schema_version": "1.0",
            "event_id": "1234",
            "event_type": "ZONE_INTRUSION",
            "timestamp_utc": "2026-10-18T12:00:00Z",
            "class_name": "person",
            "zone_id": "zone-1",
            "severity": "high",
            "status": "active",
            "source": "pipegen",
            # missing camera_id
        }
        errs = validate_event_dict(bad_dict)
        self.assertTrue(any("camera_id" in e for e in errs))

        # Invalid event_type
        bad_type = {**bad_dict, "camera_id": "cam-1", "event_type": "FIRE_ALARM"}
        errs2 = validate_event_dict(bad_type)
        self.assertTrue(any("Invalid event_type" in e for e in errs2))

        # Confidence out of [0, 1] range
        bad_conf = {**bad_dict, "camera_id": "cam-1", "confidence": 1.5}
        errs3 = validate_event_dict(bad_conf)
        self.assertTrue(any("confidence" in e for e in errs3))

    def test_concurrent_writes_thread_safety(self):
        num_threads = 10
        writes_per_thread = 20

        def worker(tid: int):
            for i in range(writes_per_thread):
                ev = SafetyEvent(
                    camera_id=f"cam-{tid}",
                    class_name="person",
                    zone_id="zone-A",
                    track_id=tid * 100 + i,
                )
                self.writer.write_event(ev)

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        events = self.writer.read_events()
        self.assertEqual(len(events), num_threads * writes_per_thread)


if __name__ == "__main__":
    unittest.main()
