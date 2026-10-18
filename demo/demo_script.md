# Workplace Safety Sentinel — 2-Minute Demo Script
## CraftifAI Physical AI Hackathon | Track A

### Demo Target: Exactly 120 Seconds (2 Minutes)

---

### Pre-Demo Checklist (T-minus 5 minutes)
- [ ] Terminal 1: Ready with `python run_sentinel.py --demo` or live video pipeline.
- [ ] Terminal 2: Ready with `tail -f demo/sample_events.jsonl` or PowerShell `Get-Content -Wait`.
- [ ] Browser / Viewer: Open PipeGen Pipeline IR diagram (`evidence/pipeline-ir/pipeline_ir.png` or JSON viewer).
- [ ] Evidence Tab: Open TensorRT Speed Report (`pipegen-export/speed_report.json`).
- [ ] Backup Video: Pre-rendered MP4/GIF backup clip stored in `evidence/live-run/backup_run.mp4`.

---

### Step-by-Step Timing and Script

| Timestamp | Segment | Presenter Role / Action | Spoken Script | Screen Visual |
|---|---|---|---|---|
| **0:00 – 0:15** (15s) | **Problem & Use Case** | Person 3 / Team Lead | *"Workplace accidents near industrial machinery and automated robotic cells cause thousands of severe injuries annually. We built Workplace Safety Sentinel: a camera-based workplace safety system powered by CraftifAI PipeGen. It monitors restricted dangerous zones in real time and generates actionable intrusion alerts."* | Show industrial restricted zone problem slide / system diagram. |
| **0:15 – 0:40** (25s) | **PipeGen 5-Stage Flow & Pipeline IR** | Person 1 (Perception) | *"We executed all five mandatory PipeGen stages: Requirement, Pipeline IR, Model, Compiler, and Run. Here is our Pipeline IR graph: it defines our video ingestion, video decoder, pre-processing, TensorRT inference engine, object tracker, and metadata emitter."* | Switch to PipeGen Pipeline IR Node Graph. Point out Source -> Decoder -> TensorRT Engine -> NvTracker -> Output. |
| **0:40 – 1:00** (20s) | **TensorRT Compilation & Speed Report** | Person 1 (Perception) | *"In the Compiler stage, PipeGen compiled our person detection model to a high-performance TensorRT FP16 engine. Looking at our speed report: baseline latency dropped from 42.1 ms to 9.8 ms, delivering 78 FPS throughput with 1.4 GB VRAM utilization, easily beating the 30 FPS real-time threshold."* | Show PipeGen Speed Report & TensorRT engine specs (`speed_report.json`). |
| **1:00 – 1:30** (30s) | **Live Inference & Zone Intrusion** | Person 1 & Person 2 | *"Now running the live pipeline on our test video. Watch as the worker approaches the danger perimeter. As their feet cross the safety polygon, the sentinel triggers within 2 frames. Notice that while they remain inside, repeated alerts are suppressed—preventing alarm fatigue."* | Execute `python run_sentinel.py --demo`. Show colorized console alert stream and bounding box tracking. |
| **1:30 – 1:50** (20s) | **Actionable Event & Incident Log** | Person 2 (Safety Logic) | *"Here is the actionable output: our frozen schema version 1.0 JSONL incident log. Each event contains unique UUID, ISO-8601 UTC timestamp, track ID, zone ID, confidence, and computed dwell time. As the worker leaves the zone, a ZONE_CLEAR event is automatically logged with the total dwell duration."* | Split screen showing formatted JSONL incident log updating live. |
| **1:50 – 2:00** (10s) | **Tested Metrics & Wrap-up** | Person 3 (Evaluation) | *"We validated our system across a 6-scenario test matrix: 0 false alerts outside the zone, 100% detection of restricted intrusions, and 30 unit tests passing in under 1 second. Workplace Safety Sentinel brings verifiable Physical AI safety to life. Thank you!"* | Show Evaluation Scorecard summary table with measured metrics. |

---

### Emergency Fallback Plan
- **If GPU / live pipeline hangs:** Instantly switch to the pre-recorded backup run: `evidence/live-run/backup_run.mp4` and demonstrate log parsing using `python run_sentinel.py --replay`.
- **If network/MQTT is offline:** Note to judges: *"Network output is designed as a resilient secondary sink; local crash-safe JSONL logging continues uninterrupted."*
- **Strict rule:** Never cite unmeasured metrics; cite only numbers from `pipegen-export/speed_report.json` and `evaluation/test_matrix.csv`.
