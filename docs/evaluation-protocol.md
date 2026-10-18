# Workplace Safety Sentinel — Evaluation Protocol

## 1. Objectives & Principles
This protocol defines the repeatable, empirical evaluation procedure for **Workplace Safety Sentinel (Track A)**. In accordance with the project's **Truthfulness Rule**, only actually measured metrics from execution runs and benchmark reports are recorded.

---

## 2. Evaluation Dimensions

### A. Perception & Inference Latency
- **Metric:** Per-frame TensorRT engine inference latency (ms) and throughput (FPS).
- **Target:** $\le 33.3\text{ ms}$ ($\ge 30\text{ FPS}$) for real-time video processing.
- **Measurement Tool:** PipeGen compiler profiling report (`pipegen-export/speed_report.json`) and DeepStream frame timestamp logging.

### B. Functional Safety Accuracy
- **True Positive Rate (Sensitivity):** Fraction of actual zone intrusions correctly generating a `ZONE_INTRUSION` event. Target: $100\%$.
- **False Alert Rate:** Number of false intrusion alerts triggered when personnel walk near, but outside, the restricted perimeter. Target: $0\%$.
- **Alert Suppression (Debouncing):** Ratio of emitted events to frames while a subject remains stationary in the zone. Target: Exactly 1 alert per intrusion episode (0 alert floods).
- **Zone Clear Resolution:** Successful detection of person exiting zone with accurate dwell time calculation ($\pm 0.5\text{s}$).

### C. System Robustness & Fault Tolerance
- **Tracker Loss / Occlusion:** Ability to bridge $1\text{ to }4$ missing detection frames using the 3-frame exit grace period without premature `ZONE_CLEAR` firing.
- **Untracked Fallback:** Ability to process un-tracked detections (`track_id = null`) using spatial grid debouncing without generating continuous frame-by-frame spam.
- **Network Sink Outage:** Continued uninterrupted logging to `sample_events.jsonl` when MQTT broker or HTTP webhook endpoints are unreachable.

---

## 3. Evaluation Procedure

1. **Step 1: Automated Unit Suite Verification**
   ```bash
   python run_sentinel.py --test
   ```
   *Success Criterion:* All 30 unit tests pass in $< 1.0\text{ second}$.

2. **Step 2: Execution against Test Matrix**
   ```bash
   python evaluation/evaluate_results.py
   ```
   *Success Criterion:* All 6 test scenarios in `evaluation/test_matrix.csv` pass with 0 false alerts and 0 duplicate floods.

3. **Step 3: End-to-End Live Stream Demonstration**
   ```bash
   python run_sentinel.py --demo
   ```
   *Success Criterion:* Live terminal alert displayed with color-coded severity, and valid JSONL lines appended to `demo/sample_events.jsonl`.
