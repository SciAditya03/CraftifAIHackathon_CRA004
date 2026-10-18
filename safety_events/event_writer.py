"""Durable JSONL incident log writer with schema validation and atomic flush."""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from safety_events.models import SafetyEvent

ALLOWED_EVENT_TYPES = {"ZONE_INTRUSION", "ZONE_CLEAR", "SYSTEM_HEALTH"}
ALLOWED_SEVERITIES = {"low", "medium", "high", "critical"}
ALLOWED_STATUSES = {"active", "cleared", "info"}
REQUIRED_FIELDS = [
    "schema_version",
    "event_id",
    "event_type",
    "timestamp_utc",
    "camera_id",
    "class_name",
    "zone_id",
    "severity",
    "status",
    "source",
]


def validate_event_dict(event_dict: Dict[str, Any]) -> List[str]:
    """Validate that an event dictionary conforms to schema_version 1.0.
    
    Returns a list of validation error strings. If empty, event is valid.
    """
    errors: List[str] = []

    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in event_dict or event_dict[field] is None:
            errors.append(f"Missing required field: '{field}'")

    if errors:
        return errors

    if event_dict.get("schema_version") != "1.0":
        errors.append(f"Invalid schema_version: expected '1.0', got {event_dict.get('schema_version')}")

    if event_dict.get("event_type") not in ALLOWED_EVENT_TYPES:
        errors.append(f"Invalid event_type: {event_dict.get('event_type')}. Must be one of {ALLOWED_EVENT_TYPES}")

    if event_dict.get("severity") not in ALLOWED_SEVERITIES:
        errors.append(f"Invalid severity: {event_dict.get('severity')}. Must be one of {ALLOWED_SEVERITIES}")

    if event_dict.get("status") not in ALLOWED_STATUSES:
        errors.append(f"Invalid status: {event_dict.get('status')}. Must be one of {ALLOWED_STATUSES}")

    track_id = event_dict.get("track_id")
    if track_id is not None and not isinstance(track_id, int):
        errors.append(f"track_id must be int or null, got {type(track_id).__name__}")

    conf = event_dict.get("confidence")
    if conf is not None:
        if not isinstance(conf, (int, float)) or not (0.0 <= conf <= 1.0):
            errors.append(f"confidence must be float between 0.0 and 1.0, got {conf}")

    bbox = event_dict.get("bbox")
    if bbox is not None:
        if not isinstance(bbox, list) or len(bbox) != 4:
            errors.append("bbox must be a list of 4 numbers [left, top, right, bottom] or null")

    return errors


class JsonlEventWriter:
    """Thread-safe, crash-resilient incident log writer for JSON Lines."""

    def __init__(self, output_path: str, auto_fsync: bool = True) -> None:
        """
        Args:
            output_path: Target path for the .jsonl file.
            auto_fsync: If True, flushes and syncs OS buffers on each write.
        """
        self.output_path = Path(output_path).resolve()
        self.auto_fsync = auto_fsync
        self._lock = threading.Lock()

        # Ensure parent directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def write_event(self, event: SafetyEvent) -> Dict[str, Any]:
        """Validate and append an event to the JSONL log file.
        
        Raises:
            ValueError: If event fails schema validation.
        """
        event_dict = event.to_dict()
        errors = validate_event_dict(event_dict)
        if errors:
            raise ValueError(f"Event failed schema validation: {'; '.join(errors)}")

        line = json.dumps(event_dict, separators=(",", ":")) + "\n"

        with self._lock:
            with open(self.output_path, "a", encoding="utf-8") as f:
                f.write(line)
                f.flush()
                if self.auto_fsync:
                    os.fsync(f.fileno())

        return event_dict

    def read_events(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Read logged events from the JSONL file."""
        if not self.output_path.exists():
            return []

        events: List[Dict[str, Any]] = []
        with self._lock:
            with open(self.output_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            events.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue

        if limit is not None:
            return events[-limit:]
        return events

    def count_events(self) -> int:
        """Return total number of logged events."""
        return len(self.read_events())

    def clear(self) -> None:
        """Truncate the log file."""
        with self._lock:
            if self.output_path.exists():
                with open(self.output_path, "w", encoding="utf-8") as f:
                    f.truncate(0)
