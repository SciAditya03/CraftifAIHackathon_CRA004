# Workplace Safety Sentinel — Comprehensive Test Plan

## 1. Test Overview
This test plan provides comprehensive verification for **Workplace Safety Sentinel (Track A)**, covering unit tests, metadata adapters, debouncing logic, and end-to-end integration.

---

## 2. Test Cases Specification

| Test ID | Scenario Description | Input Stimulus | Expected Behavior | Verification Test File |
|---|---|---|---|---|
| **TC-01** | Person outside restricted zone | Detections at $(x=0.1, y=0.1)$ outside $[0.3..0.7]$ zone. | Zero `ZONE_INTRUSION` events generated. | `test_end_to_end.py`<br>`test_zone_rules.py` |
| **TC-02** | Person enters restricted zone | Detections entering $[0.5, 0.5]$ for $\ge 2$ consecutive frames. | Exactly 1 `ZONE_INTRUSION` event emitted on 2nd frame. | `test_tracker_state.py`<br>`test_end_to_end.py` |
| **TC-03** | Person remains/lingers in zone | Track remains at $[0.5, 0.5]$ for 50 consecutive frames. | Zero repeated events; no event flood; dwell time increases. | `test_tracker_state.py` |
| **TC-04** | Person exits restricted zone | Track moves to $[0.9, 0.9]$ for 3 consecutive frames. | Exactly 1 `ZONE_CLEAR` event emitted with accurate dwell time. | `test_tracker_state.py`<br>`test_end_to_end.py` |
| **TC-05** | Missing track ID (`track_id = null`) | Detector without tracking module outputs detection in zone. | Spatial-temporal grid debouncer alerts once, suppresses within cooldown. | `test_deduplicator.py` |
| **TC-06** | Incomplete or malformed metadata | Missing bounding box, null coordinates, or out-of-range confidence. | Handled gracefully without crash; malformed record ignored. | `test_adapters.py`<br>`test_event_writer.py` |
| **TC-07** | Network destination outage | MQTT broker offline, HTTP webhook endpoint returns timeout/500. | Non-fatal warning logged; local JSONL log completes without error. | `test_dispatchers.py` |
| **TC-08** | Video rewind / repeated playback | Video loops back to frame 1 after completion. | `engine.reset()` clears track cache; subsequent intrusions alert cleanly. | `test_end_to_end.py` |

---

## 3. Geometric Boundary Tests
- **Point-in-Polygon (Ray Casting):** Verified for convex squares and non-convex L-shaped polygons (`test_zone_rules.py`).
- **Ground Contact vs Centroid:** Verified that standing worker with feet in hazard pit triggers alert, while center-only rule ignores it (`test_zone_rules.py`).
- **Pixel to Normalized Auto-Conversion:** Verified that pixel bounding boxes ($1920\times 1080$) automatically convert to $[0.0, 1.0]$ when evaluated against normalized zones.

---

## 4. Execution Commands
```bash
# Run complete test suite (all 30 tests)
python -m unittest discover -s tests -p "test_*.py" -v

# Run via CLI wrapper
python run_sentinel.py --test
```
