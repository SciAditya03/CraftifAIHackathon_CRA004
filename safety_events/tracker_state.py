"""Per-track state machine with debouncing and dwell time tracking."""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from safety_events.models import BoundingBox, EventStatus, EventType, RawDetection, RestrictedZone, SafetyEvent, Severity


class TrackZoneState(str, Enum):
    OUTSIDE = "OUTSIDE"
    ENTERING = "ENTERING"   # Detected inside but waiting for debounce confirmation
    IN_ZONE = "IN_ZONE"     # Confirmed intrusion episode active
    EXITING = "EXITING"     # Detected outside or missing, within grace period
    CLEARED = "CLEARED"     # Fully exited, ZONE_CLEAR emitted


@dataclass
class TrackState:
    track_id: int
    zone_id: str
    camera_id: str
    state: TrackZoneState = TrackZoneState.OUTSIDE
    consecutive_inside: int = 0
    consecutive_outside: int = 0
    first_entered_utc: Optional[datetime.datetime] = None
    last_seen_utc: Optional[datetime.datetime] = None
    last_alert_utc: Optional[datetime.datetime] = None
    is_alerted: bool = False
    class_name: str = "person"
    last_confidence: Optional[float] = None
    last_bbox: Optional[BoundingBox] = None


class TrackerStateManager:
    """Maintains state of all active tracks across safety zones."""

    def __init__(
        self,
        min_inside_frames: int = 2,
        exit_grace_frames: int = 5,
        re_alert_cooldown_seconds: Optional[float] = None,
        emit_clear_events: bool = True,
    ) -> None:
        """
        Args:
            min_inside_frames: Frames required inside zone before emitting ZONE_INTRUSION.
            exit_grace_frames: Consecutive frames outside before transitioning to ZONE_CLEAR.
            re_alert_cooldown_seconds: Optional interval in seconds to re-alert lingering intrusion.
                                       If None, alert is emitted strictly once per intrusion episode.
            emit_clear_events: Whether to emit ZONE_CLEAR event when track leaves zone.
        """
        self.min_inside_frames = max(1, min_inside_frames)
        self.exit_grace_frames = max(1, exit_grace_frames)
        self.re_alert_cooldown_seconds = re_alert_cooldown_seconds
        self.emit_clear_events = emit_clear_events

        # Key: (track_id, zone_id) -> TrackState
        self._tracks: Dict[tuple[int, str], TrackState] = {}

    def get_track_state(self, track_id: int, zone_id: str) -> Optional[TrackState]:
        return self._tracks.get((track_id, zone_id))

    def update_track_detection(
        self,
        detection: RawDetection,
        zone: RestrictedZone,
        is_inside: bool,
        current_time: datetime.datetime,
    ) -> List[SafetyEvent]:
        """Update state for a detected track and return any triggered safety events."""
        if detection.track_id is None:
            return []

        key = (detection.track_id, zone.zone_id)
        if key not in self._tracks:
            self._tracks[key] = TrackState(
                track_id=detection.track_id,
                zone_id=zone.zone_id,
                camera_id=detection.camera_id,
                class_name=detection.class_name,
            )

        track = self._tracks[key]
        track.last_seen_utc = current_time
        track.last_confidence = detection.confidence
        track.last_bbox = detection.bbox
        track.class_name = detection.class_name

        events: List[SafetyEvent] = []

        if is_inside:
            track.consecutive_outside = 0
            track.consecutive_inside += 1

            if track.state in (TrackZoneState.OUTSIDE, TrackZoneState.CLEARED):
                track.state = TrackZoneState.ENTERING

            if track.state == TrackZoneState.ENTERING:
                if track.consecutive_inside >= self.min_inside_frames:
                    # Transition to IN_ZONE
                    track.state = TrackZoneState.IN_ZONE
                    track.first_entered_utc = current_time
                    track.is_alerted = True
                    track.last_alert_utc = current_time

                    events.append(
                        SafetyEvent(
                            camera_id=detection.camera_id,
                            class_name=detection.class_name,
                            zone_id=zone.zone_id,
                            event_type=EventType.ZONE_INTRUSION,
                            severity=zone.severity,
                            status=EventStatus.ACTIVE,
                            timestamp_utc=current_time.isoformat(),
                            track_id=detection.track_id,
                            confidence=detection.confidence,
                            bbox=detection.bbox.as_list(),
                            dwell_time_seconds=0.0,
                            details={
                                "rule_type": zone.rule_type.value,
                                "consecutive_frames": track.consecutive_inside,
                            },
                        )
                    )

            elif track.state in (TrackZoneState.IN_ZONE, TrackZoneState.EXITING):
                track.state = TrackZoneState.IN_ZONE
                # Check for optional re-alert cooldown if configured
                if (
                    self.re_alert_cooldown_seconds is not None
                    and track.last_alert_utc is not None
                ):
                    time_since_alert = (current_time - track.last_alert_utc).total_seconds()
                    if time_since_alert >= self.re_alert_cooldown_seconds:
                        track.last_alert_utc = current_time
                        dwell = (
                            (current_time - track.first_entered_utc).total_seconds()
                            if track.first_entered_utc
                            else 0.0
                        )
                        events.append(
                            SafetyEvent(
                                camera_id=detection.camera_id,
                                class_name=detection.class_name,
                                zone_id=zone.zone_id,
                                event_type=EventType.ZONE_INTRUSION,
                                severity=zone.severity,
                                status=EventStatus.ACTIVE,
                                timestamp_utc=current_time.isoformat(),
                                track_id=detection.track_id,
                                confidence=detection.confidence,
                                bbox=detection.bbox.as_list(),
                                dwell_time_seconds=dwell,
                                details={
                                    "status_note": "lingering_cooldown_realert",
                                    "rule_type": zone.rule_type.value,
                                },
                            )
                        )
        else:
            # Detected outside zone
            track.consecutive_inside = 0
            track.consecutive_outside += 1

            if track.state == TrackZoneState.ENTERING:
                # Flickered out before confirming intrusion
                track.state = TrackZoneState.OUTSIDE

            elif track.state == TrackZoneState.IN_ZONE:
                track.state = TrackZoneState.EXITING

            if track.state == TrackZoneState.EXITING:
                if track.consecutive_outside >= self.exit_grace_frames:
                    track.state = TrackZoneState.CLEARED
                    dwell = (
                        (current_time - track.first_entered_utc).total_seconds()
                        if track.first_entered_utc
                        else 0.0
                    )
                    if self.emit_clear_events and track.is_alerted:
                        events.append(
                            SafetyEvent(
                                camera_id=detection.camera_id,
                                class_name=detection.class_name,
                                zone_id=zone.zone_id,
                                event_type=EventType.ZONE_CLEAR,
                                severity=Severity.LOW,
                                status=EventStatus.CLEARED,
                                timestamp_utc=current_time.isoformat(),
                                track_id=detection.track_id,
                                confidence=detection.confidence,
                                bbox=detection.bbox.as_list(),
                                dwell_time_seconds=dwell,
                                details={
                                    "reason": "track_exited_zone",
                                    "total_dwell_seconds": dwell,
                                },
                            )
                        )
                    track.is_alerted = False

        return events

    def handle_missing_tracks(
        self,
        active_track_ids: set[int],
        zone: RestrictedZone,
        current_time: datetime.datetime,
    ) -> List[SafetyEvent]:
        """Process tracks that were not detected in current frame."""
        events: List[SafetyEvent] = []

        for (track_id, zone_id), track in list(self._tracks.items()):
            if zone_id != zone.zone_id:
                continue

            if track_id not in active_track_ids:
                if track.state in (TrackZoneState.IN_ZONE, TrackZoneState.EXITING):
                    track.consecutive_outside += 1
                    track.state = TrackZoneState.EXITING

                    if track.consecutive_outside >= self.exit_grace_frames:
                        track.state = TrackZoneState.CLEARED
                        dwell = (
                            (current_time - track.first_entered_utc).total_seconds()
                            if track.first_entered_utc
                            else 0.0
                        )
                        if self.emit_clear_events and track.is_alerted:
                            events.append(
                                SafetyEvent(
                                    camera_id=track.camera_id,
                                    class_name=track.class_name,
                                    zone_id=zone.zone_id,
                                    event_type=EventType.ZONE_CLEAR,
                                    severity=Severity.LOW,
                                    status=EventStatus.CLEARED,
                                    timestamp_utc=current_time.isoformat(),
                                    track_id=track.track_id,
                                    confidence=track.last_confidence,
                                    bbox=track.last_bbox.as_list() if track.last_bbox else None,
                                    dwell_time_seconds=dwell,
                                    details={
                                        "reason": "track_lost_or_exited",
                                        "total_dwell_seconds": dwell,
                                    },
                                )
                            )
                        track.is_alerted = False

        return events
