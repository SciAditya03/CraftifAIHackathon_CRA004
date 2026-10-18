# Workplace Safety Sentinel — Event Schema Specification

## 1. Schema Versioning
- **Current Version:** `1.0` (Frozen on Day 1 across all roles)
- **JSON Schema:** [`safety_events/schema.json`](../safety_events/schema.json)
- **Format:** JSON Lines (JSONL), UTF-8, line-delimited records.

---

## 2. Field Definitions

| Field Name | Type | Required | Nullable | Allowed Values / Constraints | Description |
|---|---|---|---|---|---|
| `schema_version` | String | **Yes** | No | `"1.0"` | Schema version string for forward/backward compatibility. |
| `event_id` | String | **Yes** | No | UUIDv4 (e.g. `550e8400-...`) | Universally unique identifier for each generated safety event. |
| `event_type` | String | **Yes** | No | `"ZONE_INTRUSION"`, `"ZONE_CLEAR"`, `"SYSTEM_HEALTH"` | Category of incident or system notification. |
| `timestamp_utc` | String | **Yes** | No | ISO-8601 UTC string (`YYYY-MM-DDTHH:MM:SS.sssZ`) | Canonical timestamp of detection/event trigger. |
| `camera_id` | String | **Yes** | No | Non-empty string | Identifier of video source / camera feed. |
| `track_id` | Integer | No | **Yes** | $\ge 0$ or `null` | Persistent track identifier from DeepStream tracker (null if tracker disabled). |
| `class_name` | String | **Yes** | No | `"person"`, `"system"`, etc. | Detected object class label. |
| `confidence` | Float | No | **Yes** | $0.0 \le \text{conf} \le 1.0$ or `null` | Perception model confidence score. |
| `zone_id` | String | **Yes** | No | Non-empty string | Target restricted safety zone identifier. |
| `severity` | String | **Yes** | No | `"low"`, `"medium"`, `"high"`, `"critical"` | Incident severity level based on zone classification. |
| `status` | String | **Yes** | No | `"active"`, `"cleared"`, `"info"` | Lifecycle state of the safety event. |
| `source` | String | **Yes** | No | e.g. `"pipegen-deepstream"` | Originating perception pipeline identifier. |
| `bbox` | Array[4] | No | **Yes** | `[left, top, right, bottom]` | Optional bounding box coordinates (normalized or pixel space). |
| `dwell_time_seconds` | Float | No | **Yes** | $\ge 0.0$ or `null` | Cumulative duration spent inside the restricted zone in seconds. |
| `details` | Object | No | **Yes** | Key-value dictionary | Supplemental diagnostic details (e.g., rule type, debounce frame count). |

---

## 3. Standard Event Payloads

### 3.1 Zone Intrusion Event (`ZONE_INTRUSION`)
Emitted when a person is confirmed entering a restricted safety perimeter:
```json
{
  "schema_version": "1.0",
  "event_id": "8d39f72a-4bc1-49b0-9a2c-901d8194b150",
  "event_type": "ZONE_INTRUSION",
  "timestamp_utc": "2026-10-18T12:00:04.120Z",
  "camera_id": "video-demo-01",
  "track_id": 12,
  "class_name": "person",
  "confidence": 0.934,
  "zone_id": "restricted-zone-01",
  "severity": "high",
  "status": "active",
  "source": "pipegen-deepstream",
  "bbox": [0.412, 0.355, 0.518, 0.612],
  "dwell_time_seconds": 0.0,
  "details": {
    "rule_type": "feet_point",
    "zone_name": "Robotic Work Envelope",
    "consecutive_frames": 2
  }
}
```

### 3.2 Zone Clear Event (`ZONE_CLEAR`)
Emitted when a track previously in the zone exits and remains outside through the grace period:
```json
{
  "schema_version": "1.0",
  "event_id": "1e75a9b2-29fd-426b-871d-7cfa8449c210",
  "event_type": "ZONE_CLEAR",
  "timestamp_utc": "2026-10-18T12:00:11.850Z",
  "camera_id": "video-demo-01",
  "track_id": 12,
  "class_name": "person",
  "confidence": 0.902,
  "zone_id": "restricted-zone-01",
  "severity": "low",
  "status": "cleared",
  "source": "pipegen-deepstream",
  "bbox": [0.812, 0.685, 0.915, 0.942],
  "dwell_time_seconds": 7.73,
  "details": {
    "reason": "track_exited_zone",
    "total_dwell_seconds": 7.73
  }
}
```

### 3.3 System Health Event (`SYSTEM_HEALTH`)
Emitted on pipeline startup, heartbeat, or degraded FPS:
```json
{
  "schema_version": "1.0",
  "event_id": "2c91834e-862d-4f10-9721-39c4d9f84891",
  "event_type": "SYSTEM_HEALTH",
  "timestamp_utc": "2026-10-18T12:00:00.000Z",
  "camera_id": "video-demo-01",
  "track_id": null,
  "class_name": "system",
  "confidence": null,
  "zone_id": "system-health",
  "severity": "low",
  "status": "info",
  "source": "pipegen-deepstream",
  "bbox": null,
  "dwell_time_seconds": null,
  "details": {
    "message": "PipeGen TensorRT engine initialized. Monitoring restricted-zone-01."
  }
}
```

---

## 4. Zone Membership Semantics

The system provides three configurable membership strategies in `safety_events/zone_rules.py`:
1. **`feet_point` (Default & Recommended):** Evaluates bottom-center coordinate $(x_{\text{mid}}, y_{\text{bottom}})$. Ideal for ground-plane security where camera perspective might cause a standing person's head to overlap a zone while their feet remain safely outside.
2. **`box_center`:** Evaluates centroid $(x_{\text{mid}}, y_{\text{mid}})$.
3. **`box_overlap`:** Evaluates fractional bounding box intersection area against the zone polygon using uniform grid sampling.
