# Architecture

```text
Local video file -> [PipeGen: Requirement -> Pipeline IR -> Model -> Compiler -> Run]
                 -> TensorRT engine + DeepStream inference   (REQUIRED, Person 1)
                 -> detection/analytics metadata (format: TBD by Person 1)
                 -> event rule + JSONL writer (Person 2, supporting Python)
                 -> JSONL incident log (baseline), optional MQTT (never blocks JSONL)
Person 3: tests/, evaluation/, tools/check_release.py, evidence/, docs/, demo/
```

## Required vs supporting
| Component | Role | Status |
|---|---|---|
| PipeGen export / DeepStream / TensorRT | **Required inference path** | Not yet in repo |
| `safety_events/` | Supporting event logic over PipeGen output | Not yet in repo |
| `tests/`, `evaluation/`, `tools/` | QA only; **no inference** | Present |

## Event contract (frozen, schema 1.0)
Fields: schema_version, event_id (UUID), event_type (ZONE_INTRUSION | ZONE_CLEAR | SYSTEM_HEALTH), timestamp_utc (ISO-8601 UTC), camera_id, track_id (int|null), class_name, confidence ([0,1]|null), zone_id, severity, status, source. Enforced by `tests/support/contract.py`.

Open decisions needing Person 1/2 confirmation: zone rule (box centre vs overlap), whether tracking IDs exist, timestamp source (wall clock vs stream PTS).

Out of scope: ESP32/STM32, FirmGen, sensors, actuators.
