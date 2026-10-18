"""Data models for Workplace Safety Sentinel."""

from __future__ import annotations

import datetime
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class EventType(str, Enum):
    ZONE_INTRUSION = "ZONE_INTRUSION"
    ZONE_CLEAR = "ZONE_CLEAR"
    SYSTEM_HEALTH = "SYSTEM_HEALTH"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventStatus(str, Enum):
    ACTIVE = "active"
    CLEARED = "cleared"
    INFO = "info"


class ZoneRuleType(str, Enum):
    """Rule used to determine whether a bounding box is within a zone."""
    FEET_POINT = "feet_point"       # Bottom center (x_mid, y_max): where person touches ground
    BOX_CENTER = "box_center"       # Centroid (x_mid, y_mid)
    BOX_OVERLAP = "box_overlap"     # Bounding box / zone polygon intersection ratio


@dataclass
class Point:
    x: float
    y: float

    def as_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)


@dataclass
class BoundingBox:
    left: float
    top: float
    right: float
    bottom: float

    def __post_init__(self) -> None:
        if self.right < self.left:
            self.left, self.right = self.right, self.left
        if self.bottom < self.top:
            self.top, self.bottom = self.bottom, self.top

    @property
    def width(self) -> float:
        return max(0.0, self.right - self.left)

    @property
    def height(self) -> float:
        return max(0.0, self.bottom - self.top)

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def center(self) -> Point:
        """Centroid of bounding box."""
        return Point(x=(self.left + self.right) / 2.0, y=(self.top + self.bottom) / 2.0)

    @property
    def feet_point(self) -> Point:
        """Bottom-center point where person contacts floor."""
        return Point(x=(self.left + self.right) / 2.0, y=self.bottom)

    def as_list(self) -> List[float]:
        return [round(self.left, 4), round(self.top, 4), round(self.right, 4), round(self.bottom, 4)]


@dataclass
class RestrictedZone:
    zone_id: str
    polygon: List[Tuple[float, float]]  # List of (x, y) vertices
    name: str = "Restricted Area"
    severity: Severity = Severity.HIGH
    rule_type: ZoneRuleType = ZoneRuleType.FEET_POINT
    min_overlap_ratio: float = 0.20  # Only used if rule_type is BOX_OVERLAP
    is_normalized: bool = True       # True if coordinates are in [0.0, 1.0]

    def __post_init__(self) -> None:
        if len(self.polygon) < 3:
            raise ValueError(f"Zone {self.zone_id} polygon must have at least 3 vertices.")


@dataclass
class RawDetection:
    """Detection output from PipeGen/DeepStream pipeline."""
    camera_id: str
    frame_id: int
    timestamp_utc: str
    class_name: str
    bbox: BoundingBox
    track_id: Optional[int] = None
    confidence: Optional[float] = None
    source: str = "pipegen-deepstream"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SafetyEvent:
    """Actionable workplace safety event matching schema_version 1.0."""
    camera_id: str
    class_name: str
    zone_id: str
    event_type: EventType = EventType.ZONE_INTRUSION
    severity: Severity = Severity.HIGH
    status: EventStatus = EventStatus.ACTIVE
    source: str = "pipegen-deepstream"
    schema_version: str = "1.0"
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp_utc: str = field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    )
    track_id: Optional[int] = None
    confidence: Optional[float] = None
    bbox: Optional[List[float]] = None
    dwell_time_seconds: Optional[float] = None
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary matching schema.json."""
        data = {
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "event_type": self.event_type.value if isinstance(self.event_type, EventType) else self.event_type,
            "timestamp_utc": self.timestamp_utc,
            "camera_id": self.camera_id,
            "track_id": self.track_id,
            "class_name": self.class_name,
            "confidence": round(self.confidence, 4) if self.confidence is not None else None,
            "zone_id": self.zone_id,
            "severity": self.severity.value if isinstance(self.severity, Severity) else self.severity,
            "status": self.status.value if isinstance(self.status, EventStatus) else self.status,
            "source": self.source,
            "bbox": self.bbox,
            "dwell_time_seconds": round(self.dwell_time_seconds, 2) if self.dwell_time_seconds is not None else None,
            "details": self.details,
        }
        return data
