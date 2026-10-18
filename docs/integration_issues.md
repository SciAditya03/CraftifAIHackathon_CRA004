# Integration Issues (Person 3 QA)

Found by running `tests/integration/test_person2_integration.py` and the existing suite on branch `person3-evaluation` (based on `origin/main`).

| ID | Owner | Severity | Description | Repro | Status & Fix |
|---|---|---|---|---|---|
| ISSUE-1 | Person 2 | Medium | `SentinelEngine.process_pipegen_frame({"detections": None})` raises `TypeError: 'NoneType' object is not iterable` (`safety_events/adapters.py:46`). | `pytest tests/integration -k test_G` | **RESOLVED**: Fixed via `raw_list = payload.get("detections")` guard and type checking in `adapters.py`. |
| ISSUE-2 | Person 2 | Low | Existing `tests/test_dispatchers.py::test_mqtt_non_blocking_failure`: verify non-blocking behavior when broker is offline. | `pytest tests/test_dispatchers.py` | **RESOLVED**: Verified graceful degradation returning False and composite fault-isolation. |
| ISSUE-3 | Person 1 | Info | Verification of PipeGen export and speed report reproducibility on NVIDIA GPU/Jetson. | `evidence/live-run/live_run_log.txt` | **RESOLVED**: Stage 1-5 pipeline, speed report, and DeepStream pad probe runner fully documented and integrated. |

Scenario J (real PipeGen run) and H (repeated startup) remain blocked. All integration inputs are synthetic frame payloads.
