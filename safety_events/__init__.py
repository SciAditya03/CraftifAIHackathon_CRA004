"""Workplace Safety Sentinel - Track A Safety Logic & Actionable Output Package."""

from safety_events.models import (
    BoundingBox,
    EventStatus,
    EventType,
    Point,
    RawDetection,
    RestrictedZone,
    SafetyEvent,
    Severity,
    ZoneRuleType,
)
from safety_events.zone_rules import (
    box_polygon_overlap_ratio,
    create_rectangular_zone,
    evaluate_detection,
    is_bbox_in_zone,
    normalize_bbox,
    point_in_polygon,
)
from safety_events.tracker_state import TrackState, TrackZoneState, TrackerStateManager
from safety_events.deduplicator import EventDeduplicator
from safety_events.event_writer import JsonlEventWriter, validate_event_dict
from safety_events.adapters import (
    parse_deepstream_msgbroker,
    parse_deepstream_pyds_meta,
    parse_pipegen_frame,
    parse_single_detection,
)
from safety_events.dispatchers import (
    BaseEventDispatcher,
    CompositeDispatcher,
    ConsoleAlertDispatcher,
    JsonlDispatcher,
    MqttDispatcher,
    WebhookDispatcher,
)
from safety_events.engine import SentinelEngine

__all__ = [
    "BoundingBox",
    "Point",
    "RawDetection",
    "RestrictedZone",
    "SafetyEvent",
    "Severity",
    "EventType",
    "EventStatus",
    "ZoneRuleType",
    "point_in_polygon",
    "box_polygon_overlap_ratio",
    "normalize_bbox",
    "is_bbox_in_zone",
    "evaluate_detection",
    "create_rectangular_zone",
    "TrackState",
    "TrackZoneState",
    "TrackerStateManager",
    "EventDeduplicator",
    "JsonlEventWriter",
    "validate_event_dict",
    "parse_pipegen_frame",
    "parse_deepstream_msgbroker",
    "parse_deepstream_pyds_meta",
    "parse_single_detection",
    "BaseEventDispatcher",
    "CompositeDispatcher",
    "ConsoleAlertDispatcher",
    "JsonlDispatcher",
    "WebhookDispatcher",
    "MqttDispatcher",
    "SentinelEngine",
]
