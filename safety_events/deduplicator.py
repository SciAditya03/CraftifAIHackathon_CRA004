"""Event deduplication, cooldown, and flood prevention logic.

Supports tracked detections (via TrackerStateManager) and untracked detections
(via spatial-temporal grid debouncing).
"""

from __future__ import annotations

import datetime
from typing import Dict, List, Optional, Tuple

from safety_events.models import (
    BoundingBox,
    EventStatus,
    EventType,
    RawDetection,
    RestrictedZone,
    SafetyEvent,
    Severity,
)
from safety_events.tracker_state import TrackerStateManager
from safety_events.zone_rules import evaluate_detection


class EventDeduplicator:
    """Orchestrates event evaluation, deduplication, and cooldown across zones."""

    def __init__(
        self,
        min_inside_frames: int = 2,
        exit_grace_frames: int = 5,
        re_alert_cooldown_seconds: Optional[float] = None,
        untracked_cooldown_seconds: float = 4.0,
        untracked_grid_cell_size: float = 0.08,
        emit_clear_events: bool = True,
    ) -> None:
        """
        Args:
            min_inside_frames: Debounce frames for tracked intrusion.
            exit_grace_frames: Grace frames before declaring clear.
            re_alert_cooldown_seconds: Cooldown for repeating tracked alerts (None = once per intrusion).
            untracked_cooldown_seconds: Cooldown in seconds before alerting same spatial region if track_id is null.
            untracked_grid_cell_size: Normalized spatial cell size for untracked debouncing.
            emit_clear_events: Whether to emit ZONE_CLEAR events.
        """
        self.tracker_manager = TrackerStateManager(
            min_inside_frames=min_inside_frames,
            exit_grace_frames=exit_grace_frames,
            re_alert_cooldown_seconds=re_alert_cooldown_seconds,
            emit_clear_events=emit_clear_events,
        )
        self.untracked_cooldown_seconds = untracked_cooldown_seconds
        self.untracked_grid_cell_size = untracked_grid_cell_size

        # Untracked spatial cache: (zone_id, grid_x, grid_y) -> last_alert_datetime
        self._untracked_alerts: Dict[Tuple[str, int, int], datetime.datetime] = {}

    def reset(self) -> None:
        """Clear all active tracks and cooldown caches (e.g. on video rewind/restart)."""
        self.tracker_manager._tracks.clear()
        self._untracked_alerts.clear()

    def process_frame_detections(
        self,
        detections: List[RawDetection],
        zones: List[RestrictedZone],
        frame_width: Optional[float] = None,
        frame_height: Optional[float] = None,
        current_time: Optional[datetime.datetime] = None,
    ) -> List[SafetyEvent]:
        """Process all detections in a single frame against registered restricted zones.
        
        Returns all actionable safety events generated for this frame.
        """
        if current_time is None:
            current_time = datetime.datetime.now(datetime.timezone.utc)

        emitted_events: List[SafetyEvent] = []

        # Group detections by zone
        for zone in zones:
            active_track_ids_in_frame: set[int] = set()

            for det in detections:
                if det.track_id is not None:
                    active_track_ids_in_frame.add(det.track_id)

                is_inside = evaluate_detection(
                    detection=det,
                    zone=zone,
                    frame_width=frame_width,
                    frame_height=frame_height,
                )

                if det.track_id is not None:
                    # Tracked object: update state machine
                    events = self.tracker_manager.update_track_detection(
                        detection=det,
                        zone=zone,
                        is_inside=is_inside,
                        current_time=current_time,
                    )
                    emitted_events.extend(events)
                else:
                    # Untracked object fallback: spatial debouncing
                    if is_inside:
                        untracked_event = self._process_untracked_detection(
                            detection=det,
                            zone=zone,
                            current_time=current_time,
                        )
                        if untracked_event:
                            emitted_events.append(untracked_event)

            # Check for lost tracks that were previously in zone
            missing_events = self.tracker_manager.handle_missing_tracks(
                active_track_ids=active_track_ids_in_frame,
                zone=zone,
                current_time=current_time,
            )
            emitted_events.extend(missing_events)

        return emitted_events

    def _process_untracked_detection(
        self,
        detection: RawDetection,
        zone: RestrictedZone,
        current_time: datetime.datetime,
    ) -> Optional[SafetyEvent]:
        """Spatial-temporal debouncer for detections without track_id."""
        pt = detection.bbox.feet_point
        grid_x = int(pt.x / self.untracked_grid_cell_size)
        grid_y = int(pt.y / self.untracked_grid_cell_size)
        grid_key = (zone.zone_id, grid_x, grid_y)

        last_alert = self._untracked_alerts.get(grid_key)
        if last_alert is not None:
            time_diff = (current_time - last_alert).total_seconds()
            if time_diff < self.untracked_cooldown_seconds:
                # Suppress flood
                return None

        # Emit untracked intrusion event
        self._untracked_alerts[grid_key] = current_time
        return SafetyEvent(
            camera_id=detection.camera_id,
            class_name=detection.class_name,
            zone_id=zone.zone_id,
            event_type=EventType.ZONE_INTRUSION,
            severity=zone.severity,
            status=EventStatus.ACTIVE,
            timestamp_utc=current_time.isoformat(),
            track_id=None,
            confidence=detection.confidence,
            bbox=detection.bbox.as_list(),
            dwell_time_seconds=None,
            details={
                "untracked": True,
                "spatial_cell": [grid_x, grid_y],
                "cooldown_seconds": self.untracked_cooldown_seconds,
            },
        )

    def create_health_event(
        self,
        camera_id: str,
        message: str,
        severity: Severity = Severity.LOW,
        details: Optional[dict] = None,
    ) -> SafetyEvent:
        """Create a SYSTEM_HEALTH event conforming to schema."""
        return SafetyEvent(
            camera_id=camera_id,
            class_name="system",
            zone_id="system-health",
            event_type=EventType.SYSTEM_HEALTH,
            severity=severity,
            status=EventStatus.INFO,
            details={"message": message, **(details or {})},
        )
