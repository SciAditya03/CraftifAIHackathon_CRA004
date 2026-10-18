# Integration Issues (Person 3 QA)

Found by running `tests/integration/test_person2_integration.py` and the existing suite on branch `person3-evaluation` (based on `origin/main`).

| ID | Owner | Severity | Description | Repro | Proposed fix |
|---|---|---|---|---|---|
| ISSUE-1 | Person 2 | Medium | `SentinelEngine.process_pipegen_frame({"detections": None})` raises `TypeError: 'NoneType' object is not iterable` (`safety_events/adapters.py:46`). Other malformed payloads (`{}`, `[{}]`, bad bbox, bad confidence) are handled. | `pytest tests/integration -k test_G` (xfail strict) | `raw_list = payload.get("detections") or []` |
| ISSUE-2 | Person 2 | Low | Existing `tests/test_dispatchers.py::test_mqtt_non_blocking_failure` fails on this host: `dispatch()` returned True where the test expects False for an unreachable broker. Cause not investigated (paho-mqtt v1 callback API deprecation warning present). | `pytest tests/test_dispatchers.py` | Person 2 to check what `MqttDispatcher.dispatch` returns when not connected |
| ISSUE-3 | Person 1 | Info | `pipegen-export/` and `evidence/*` files on `main` could not be verified as real PipeGen output by Person 3. `demo/simulate_live_run.py` suggests the live-run log may be simulated. Real-run status is unverified; do not present simulated output as live evidence. | read `evidence/live-run/live_run_log.txt` | Person 1 to confirm provenance |

Scenario J (real PipeGen run) and H (repeated startup) remain blocked. All integration inputs are synthetic frame payloads.
