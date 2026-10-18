# Test Plan

## Run
```
python -m pytest              # all tests (11 are BLOCKED until teammates deliver)
python -m pytest -m unit      # unit only
python evaluation/run_evaluation.py
python tools/check_release.py # exit 1 while mandatory evidence missing
python tools/make_fixtures.py # regenerate synthetic fixtures
```
Requires Python 3 + pytest only; no GPU or network.

## Coverage
| Topic | Test | Status |
|---|---|---|
| Event schema (missing/invalid fields, null track, confidence bounds, roundtrip) | `tests/unit/test_event_contract.py` | Implemented, passing |
| JSONL parsing, empty/malformed, null-track, duplicates, idempotence | `tests/unit/test_jsonl_eval.py` | Implemented, passing |
| Zone membership, dedup/cooldown, clear event, fallback for null track, optional publisher failure, startup config validation | `tests/integration/test_person2_integration.py` | **BLOCKED** (no `safety_events`) |
| Live PipeGen run (scenario J), repeated startup (H) | `test_scenario_j_live_pipeline` | **BLOCKED** |

When Person 2 delivers, replace the placeholder scenario tests with real behavioural assertions; do not weaken them to pass.
