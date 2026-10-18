"""Unit tests for per-track state machine and debouncing logic."""

import datetime
import unittest
from safety_events.models import (
    BoundingBox,
    EventType,
    RawDetection,
    RestrictedZone,
    ZoneRuleType,
)
from safety_events.tracker_state import TrackZoneState, TrackerStateManager
from safety_events.zone_rules import create_rectangular_zone


class TestTrackerState(unittest.TestCase):

    def setUp(self):
        self.zone = create_rectangular_zone(
            zone_id="restricted-zone-01",
            x1=0.2,
            y1=0.2,
            x2=0.8,
            y2=0.8,
            rule_type=ZoneRuleType.FEET_POINT,
        )
        self.manager = TrackerStateManager(
            min_inside_frames=2,
            exit_grace_frames=3,
            emit_clear_events=True,
        )
        self.base_time = datetime.datetime(2026, 10, 18, 12, 0, 0, tzinfo=datetime.timezone.utc)

    def _make_detection(self, track_id: int, feet_x: float, feet_y: float, frame_id: int = 1) -> RawDetection:
        # Bbox whose bottom center is at (feet_x, feet_y)
        return RawDetection(
            camera_id="cam-01",
            frame_id=frame_id,
            timestamp_utc=self.base_time.isoformat(),
            class_name="person",
            bbox=BoundingBox(left=feet_x - 0.05, top=feet_y - 0.2, right=feet_x + 0.05, bottom=feet_y),
            track_id=track_id,
            confidence=0.92,
        )

    def test_debounce_requires_two_frames(self):
        det_inside = self._make_detection(track_id=1, feet_x=0.5, feet_y=0.5, frame_id=1)

        # Frame 1: inside, but min_inside_frames=2 -> state ENTERING, no events yet
        events1 = self.manager.update_track_detection(det_inside, self.zone, is_inside=True, current_time=self.base_time)
        self.assertEqual(len(events1), 0)
        track = self.manager.get_track_state(1, self.zone.zone_id)
        self.assertEqual(track.state, TrackZoneState.ENTERING)

        # Frame 2: inside again -> transition to IN_ZONE, exactly 1 ZONE_INTRUSION event
        t2 = self.base_time + datetime.timedelta(milliseconds=33)
        events2 = self.manager.update_track_detection(det_inside, self.zone, is_inside=True, current_time=t2)
        self.assertEqual(len(events2), 1)
        self.assertEqual(events2[0].event_type, EventType.ZONE_INTRUSION)
        self.assertEqual(events2[0].track_id, 1)
        self.assertEqual(events2[0].zone_id, "restricted-zone-01")

        # Frame 3: still inside -> NO repeated alert (event flood prevented)
        t3 = self.base_time + datetime.timedelta(milliseconds=66)
        events3 = self.manager.update_track_detection(det_inside, self.zone, is_inside=True, current_time=t3)
        self.assertEqual(len(events3), 0)

    def test_single_frame_flicker_suppressed(self):
        # Frame 1: inside
        det_inside = self._make_detection(track_id=2, feet_x=0.5, feet_y=0.5, frame_id=1)
        self.manager.update_track_detection(det_inside, self.zone, is_inside=True, current_time=self.base_time)

        # Frame 2: flickered outside (noise/detector glitch)
        det_outside = self._make_detection(track_id=2, feet_x=0.1, feet_y=0.1, frame_id=2)
        events = self.manager.update_track_detection(det_outside, self.zone, is_inside=False, current_time=self.base_time)
        self.assertEqual(len(events), 0)
        track = self.manager.get_track_state(2, self.zone.zone_id)
        self.assertEqual(track.state, TrackZoneState.OUTSIDE)

    def test_exit_grace_period_and_clear_event(self):
        det_inside = self._make_detection(track_id=3, feet_x=0.5, feet_y=0.5)
        # Confirm intrusion with 2 frames
        t1 = self.base_time
        t2 = t1 + datetime.timedelta(seconds=1)
        self.manager.update_track_detection(det_inside, self.zone, is_inside=True, current_time=t1)
        self.manager.update_track_detection(det_inside, self.zone, is_inside=True, current_time=t2)

        det_outside = self._make_detection(track_id=3, feet_x=0.9, feet_y=0.9)

        # Outside frame 1 (grace frame 1/3) -> no clear event yet
        t3 = t2 + datetime.timedelta(seconds=1)
        ev1 = self.manager.update_track_detection(det_outside, self.zone, is_inside=False, current_time=t3)
        self.assertEqual(len(ev1), 0)

        # Outside frame 2 (grace frame 2/3) -> no clear event yet
        t4 = t3 + datetime.timedelta(seconds=1)
        ev2 = self.manager.update_track_detection(det_outside, self.zone, is_inside=False, current_time=t4)
        self.assertEqual(len(ev2), 0)

        # Outside frame 3 (grace frame 3/3 reached) -> exactly 1 ZONE_CLEAR event
        t5 = t4 + datetime.timedelta(seconds=1)
        ev3 = self.manager.update_track_detection(det_outside, self.zone, is_inside=False, current_time=t5)
        self.assertEqual(len(ev3), 1)
        self.assertEqual(ev3[0].event_type, EventType.ZONE_CLEAR)
        self.assertAlmostEqual(ev3[0].dwell_time_seconds, 3.0, delta=0.1)

    def test_handle_missing_tracks(self):
        det_inside = self._make_detection(track_id=4, feet_x=0.5, feet_y=0.5)
        t1 = self.base_time
        t2 = t1 + datetime.timedelta(seconds=1)
        self.manager.update_track_detection(det_inside, self.zone, is_inside=True, current_time=t1)
        self.manager.update_track_detection(det_inside, self.zone, is_inside=True, current_time=t2)

        # Track 4 vanishes from subsequent frames
        active_tracks = set()  # Empty
        t_miss1 = t2 + datetime.timedelta(seconds=1)
        self.manager.handle_missing_tracks(active_tracks, self.zone, current_time=t_miss1)

        t_miss2 = t_miss1 + datetime.timedelta(seconds=1)
        self.manager.handle_missing_tracks(active_tracks, self.zone, current_time=t_miss2)

        # 3rd missing frame -> clear triggered
        t_miss3 = t_miss2 + datetime.timedelta(seconds=1)
        ev = self.manager.handle_missing_tracks(active_tracks, self.zone, current_time=t_miss3)
        self.assertEqual(len(ev), 1)
        self.assertEqual(ev[0].event_type, EventType.ZONE_CLEAR)
        self.assertEqual(ev[0].track_id, 4)


if __name__ == "__main__":
    unittest.main()
