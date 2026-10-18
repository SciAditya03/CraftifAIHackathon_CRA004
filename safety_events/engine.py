"""High-level SentinelEngine orchestrating perception ingestion, zone evaluation, and dispatch."""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from safety_events.adapters import parse_deepstream_msgbroker, parse_pipegen_frame
from safety_events.deduplicator import EventDeduplicator
from safety_events.dispatchers import (
    BaseEventDispatcher,
    CompositeDispatcher,
    ConsoleAlertDispatcher,
    JsonlDispatcher,
    MqttDispatcher,
    WebhookDispatcher,
)
from safety_events.event_writer import JsonlEventWriter
from safety_events.models import (
    EventStatus,
    EventType,
    RawDetection,
    RestrictedZone,
    SafetyEvent,
    Severity,
    ZoneRuleType,
)


class SentinelEngine:
    """Core safety analytics engine consuming pipeline detections and emitting actionable events."""

    def __init__(
        self,
        output_jsonl_path: str = "demo/sample_events.jsonl",
        enable_console_alerts: bool = True,
        webhook_url: Optional[str] = None,
        mqtt_broker: Optional[str] = None,
        min_inside_frames: int = 2,
        exit_grace_frames: int = 5,
        re_alert_cooldown_seconds: Optional[float] = None,
        emit_clear_events: bool = True,
    ) -> None:
        self.zones: List[RestrictedZone] = []
        self.deduplicator = EventDeduplicator(
            min_inside_frames=min_inside_frames,
            exit_grace_frames=exit_grace_frames,
            re_alert_cooldown_seconds=re_alert_cooldown_seconds,
            emit_clear_events=emit_clear_events,
        )

        # Storage & Dispatch
        self.writer = JsonlEventWriter(output_path=output_jsonl_path)
        self.dispatcher = CompositeDispatcher()
        self.dispatcher.add_dispatcher(JsonlDispatcher(self.writer))

        if enable_console_alerts:
            self.dispatcher.add_dispatcher(ConsoleAlertDispatcher())

        if webhook_url:
            self.dispatcher.add_dispatcher(WebhookDispatcher(webhook_url))

        if mqtt_broker:
            self.dispatcher.add_dispatcher(MqttDispatcher(broker_host=mqtt_broker))

        # Runtime telemetry metrics
        self.metrics = {
            "frames_processed": 0,
            "total_detections": 0,
            "intrusions_emitted": 0,
            "clears_emitted": 0,
            "health_events_emitted": 0,
        }

    def add_zone(self, zone: RestrictedZone) -> None:
        """Register a restricted zone for monitoring."""
        self.zones.append(zone)

    def process_raw_detections(
        self,
        detections: List[RawDetection],
        frame_width: Optional[float] = None,
        frame_height: Optional[float] = None,
        current_time: Optional[datetime.datetime] = None,
    ) -> List[SafetyEvent]:
        """Process a list of detections for a single frame."""
        self.metrics["frames_processed"] += 1
        self.metrics["total_detections"] += len(detections)

        events = self.deduplicator.process_frame_detections(
            detections=detections,
            zones=self.zones,
            frame_width=frame_width,
            frame_height=frame_height,
            current_time=current_time,
        )

        for event in events:
            if event.event_type == EventType.ZONE_INTRUSION:
                self.metrics["intrusions_emitted"] += 1
            elif event.event_type == EventType.ZONE_CLEAR:
                self.metrics["clears_emitted"] += 1
            elif event.event_type == EventType.SYSTEM_HEALTH:
                self.metrics["health_events_emitted"] += 1

            self.dispatcher.dispatch(event)

        return events

    def process_pipegen_frame(
        self,
        payload: Dict[str, Any],
        frame_width: Optional[float] = None,
        frame_height: Optional[float] = None,
    ) -> List[SafetyEvent]:
        """Ingest frame payload from PipeGen pipeline."""
        detections = parse_pipegen_frame(payload)
        return self.process_raw_detections(
            detections=detections,
            frame_width=frame_width,
            frame_height=frame_height,
        )

    def process_deepstream_msg(
        self,
        payload: Dict[str, Any],
        frame_width: Optional[float] = None,
        frame_height: Optional[float] = None,
    ) -> List[SafetyEvent]:
        """Ingest payload from DeepStream nvmsgbroker."""
        detections = parse_deepstream_msgbroker(payload)
        return self.process_raw_detections(
            detections=detections,
            frame_width=frame_width,
            frame_height=frame_height,
        )

    def emit_system_health(
        self,
        camera_id: str,
        message: str,
        severity: Severity = Severity.LOW,
        details: Optional[dict] = None,
    ) -> SafetyEvent:
        """Emit and dispatch a SYSTEM_HEALTH event."""
        event = self.deduplicator.create_health_event(
            camera_id=camera_id,
            message=message,
            severity=severity,
            details=details,
        )
        self.metrics["health_events_emitted"] += 1
        self.dispatcher.dispatch(event)
        return event

    def reset(self) -> None:
        """Reset deduplication state and counters."""
        self.deduplicator.reset()
