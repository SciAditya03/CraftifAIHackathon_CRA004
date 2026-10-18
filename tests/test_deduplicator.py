"""Unit tests for EventDeduplicator with tracked and untracked detections."""

import datetime
import unittest
from safety_events.deduplicator import EventDeduplicator
from safety_events.models import BoundingBox, EventType, RawDetection, ZoneRuleType
from safety_events.zone_rules import create_rectangular_zone


class TestEventDeduplicator(unittest.TestCase):

    def setUp(self):
        self.zone = create_rectangular_zone(
            zone_id="restricted-zone-01",
            x1=0.2,
            y1=0.2,
            x2=0.8,
            y2=0.8,
            rule_type=ZoneRuleType.FEET_POINT,
        )
        self.dedup = EventDeduplicator(
            min_inside_frames=1,  # immediate for testing
            untracked_cooldown_seconds=3.0,
            untracked_grid_cell_size=0.1,
        )
        self.now = datetime.datetime(2026, 10, 18, 12, 0, 0, tzinfo=datetime.timezone.utc)

    def test_untracked_detection_cooldown(self):
        # Detection with track_id = None
        det = RawDetection(
            camera_id="cam-01",
            frame_id=1,
            timestamp_utc=self.now.isoformat(),
            class_name="person",
            bbox=BoundingBox(left=0.45, top=0.3, right=0.55, bottom=0.5),
            track_id=None,
            confidence=0.88,
        )

        # Frame 1: emits intrusion event
        events1 = self.dedup.process_frame_detections(
            detections=[det],
            zones=[self.zone],
            current_time=self.now,
        )
        self.assertEqual(len(events1), 1)
        self.assertEqual(events1[0].event_type, EventType.ZONE_INTRUSION)
        self.assertIsNone(events1[0].track_id)

        # Frame 2 (0.1s later): same spatial cell, suppressed by cooldown!
        t2 = self.now + datetime.timedelta(seconds=0.1)
        events2 = self.dedup.process_frame_detections(
            detections=[det],
            zones=[self.zone],
            current_time=t2,
        )
        self.assertEqual(len(events2), 0)

        # Frame 3 (4.0s later): cooldown expired, re-emits alert
        t3 = self.now + datetime.timedelta(seconds=4.0)
        events3 = self.dedup.process_frame_detections(
            detections=[det],
            zones=[self.zone],
            current_time=t3,
        )
        self.assertEqual(len(events3), 1)

    def test_untracked_different_spatial_grid_can_alert(self):
        # Two untracked people at different positions in the zone
        det_left = RawDetection(
            camera_id="cam-01",
            frame_id=1,
            timestamp_utc=self.now.isoformat(),
            class_name="person",
            bbox=BoundingBox(left=0.25, top=0.3, right=0.35, bottom=0.4),
            track_id=None,
        )
        det_right = RawDetection(
            camera_id="cam-01",
            frame_id=1,
            timestamp_utc=self.now.isoformat(),
            class_name="person",
            bbox=BoundingBox(left=0.65, top=0.5, right=0.75, bottom=0.7),
            track_id=None,
        )

        events = self.dedup.process_frame_detections(
            detections=[det_left, det_right],
            zones=[self.zone],
            current_time=self.now,
        )
        # Both distinct grid cells alert
        self.assertEqual(len(events), 2)

    def test_reset_clears_state(self):
        det = RawDetection(
            camera_id="cam-01",
            frame_id=1,
            timestamp_utc=self.now.isoformat(),
            class_name="person",
            bbox=BoundingBox(left=0.45, top=0.3, right=0.55, bottom=0.5),
            track_id=10,
        )
        self.dedup.process_frame_detections([det], [self.zone], current_time=self.now)
        self.assertIn((10, "restricted-zone-01"), self.dedup.tracker_manager._tracks)

        self.dedup.reset()
        self.assertEqual(len(self.dedup.tracker_manager._tracks), 0)
        self.assertEqual(len(self.dedup._untracked_alerts), 0)

    def test_create_health_event(self):
        ev = self.dedup.create_health_event(
            camera_id="cam-01",
            message="Pipeline FPS dropped below threshold",
            details={"current_fps": 12.4},
        )
        self.assertEqual(ev.event_type, EventType.SYSTEM_HEALTH)
        self.assertEqual(ev.status.value, "info")
        self.assertEqual(ev.details["current_fps"], 12.4)


if __name__ == "__main__":
    unittest.main()
