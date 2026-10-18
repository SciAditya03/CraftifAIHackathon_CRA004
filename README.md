# Workplace Safety Sentinel
### CraftifAI Physical AI Hackathon — Track A Only
**A PipeGen-Powered, TensorRT-Accelerated Workplace Safety & Restricted-Zone Analytics System**

[![Tests](https://img.shields.io/badge/tests-30%20passed-brightgreen.svg)]()
[![PipeGen](https://img.shields.io/badge/PipeGen-v0.5.1-blue.svg)]()
[![TensorRT](https://img.shields.io/badge/TensorRT-FP16%20Compiled-76b900.svg)]()
[![DeepStream](https://img.shields.io/badge/DeepStream-7.0%20%2F%206.4-success.svg)]()
[![Schema](https://img.shields.io/badge/Schema-v1.0%20Frozen-orange.svg)]()
[![Scope](https://img.shields.io/badge/Scope-Track%20A%20Software%20Only-lightgrey.svg)]()

---

## 1. Executive Summary

**Workplace Safety Sentinel** is an edge computer-vision safety system designed to prevent severe injuries near dangerous industrial machinery and automated robotic workcells. Built using **CraftifAI PipeGen**, the system executes a person-detection pipeline compiled into a high-performance **TensorRT engine** and deployed via **NVIDIA DeepStream**.

When personnel enter designated hazardous zones, the sentinel evaluates geometric safety boundaries (ground-plane feet contact or bounding box centroid) and emits structured, debounced, actionable incident records (in standardized **JSONL**, console alerts, and optional **MQTT/Webhook** feeds).

### Scope & Guardrails
- **Track A Focused:** 100% pure software, edge perception, and actionable digital analytics.
- **Explicitly Out of Scope:** No ESP32, STM32, FirmGen, physical relays, or embedded actuation.
- **Privacy-First:** Strict bounding-box and tracking analytics only. **Zero face recognition or biometric identification**.

---

## 2. 3-Person Parallel Ownership

| Role | Core Ownership | Independent Deliverables | Hackathon Artifacts |
|---|---|---|---|
| **Person 1**<br>Perception & PipeGen | Five-stage PipeGen flow, model selection, TensorRT engine compilation, live video run. | PipeGen project export, compiled engine specs, speed profiling report, Pipeline IR DAG. | [`pipegen-export/`](pipegen-export/)<br>[`evidence/pipeline-ir/`](evidence/pipeline-ir/)<br>[`evidence/tensorrt-report/`](evidence/tensorrt-report/) |
| **Person 2**<br>Safety Logic & Output | Frozen event schema v1.0, polygon ray casting, per-track state debouncing, crash-safe JSONL writer, adapters. | Geometric zone evaluator, cooldown logic, fault-isolated dispatchers, unit tests. | [`safety_events/`](safety_events/)<br>[`safety_events/schema.json`](safety_events/schema.json)<br>[`tests/`](tests/) |
| **Person 3**<br>Evaluation & Reliability | Test video matrix, evaluation protocol, failure analysis, 2-minute demo pitch, documentation. | Evaluation protocol, test matrix scorecard, repeatability checklist, demo rehearsal. | [`evaluation/`](evaluation/)<br>[`demo/`](demo/)<br>[`docs/`](docs/) |

---

## 3. System Architecture

```text
Local Video File (MP4) / RTSP
        |
        v
CraftifAI PipeGen Pipeline: Requirement -> Pipeline IR -> Model -> Compiler -> Run
        |
        v
TensorRT FP16 Engine + DeepStream 7.0 Pipeline (9.8 ms latency, 78.4 FPS)
        |
        +----> Annotated Video Display / OSD Sink
        |
        v
Metadata Adapter (PipeGen Frame / DeepStream nvmsgbroker / pyds Probe)
        |
        v
Safety Sentinel Engine:
  - Ray-Casting Point-in-Polygon (Feet ground-plane rule)
  - Per-Track State Machine (2-frame debounce, 3-frame exit grace)
  - Spatial-Temporal Debouncer (Untracked object fallback)
        |
        +----> Primary Sink: Durable JSONL Incident Log (Crash-safe atomic fsync)
        +----> Primary Sink: Colorized Real-Time Console Alert Streamer
        +----> Secondary Sink (Optional): HTTP Webhook / MQTT Alert Feed
```

---

## 4. CraftifAI PipeGen Five-Stage Gates

All five mandatory PipeGen gates have been executed and documented:

1. **Requirement Stage (`pipegen-export/requirement.yaml`):** Defined industrial person detection, restricted dangerous zones, real-time latency target ($\le 33\text{ ms}$), and JSONL incident output.
2. **Pipeline IR Stage (`pipegen-export/pipeline_ir.json`):** Generated 7-node declarative computation graph linking video demuxing, GPU decoder, nvstreammux, TensorRT nvinfer, nvtracker, safety pad probe, and OSD sink.
3. **Model Selection Stage (`pipegen-export/model_config.json`):** Selected CSPDarknet/YOLO person detector ($640\times 640$ input) from the PipeGen catalog.
4. **Compiler Stage (`pipegen-export/speed_report.json`):** Compiled engine to **TensorRT FP16**, dropping latency from 42.14 ms to **9.82 ms** (**4.29x speedup**, 101.8 FPS engine / 78.4 FPS end-to-end).
5. **Run Stage (`run_sentinel.py` / `demo/simulate_live_run.py`):** Live execution on local video stream generating validated actionable events.

---

## 5. Frozen Event Schema (v1.0)

All events emitted by Workplace Safety Sentinel strictly adhere to [`safety_events/schema.json`](safety_events/schema.json):

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
    "consecutive_frames": 2
  }
}
```

### Event Types
- `ZONE_INTRUSION`: Emitted when an unauthorized person crosses into a restricted zone.
- `ZONE_CLEAR`: Emitted when a person leaves the zone and remains outside through the grace period (includes total dwell duration).
- `SYSTEM_HEALTH`: Emitted on pipeline initialization, frame rate degradation, or camera disconnection.

---

## 6. Repeatable Quickstart Instructions

The core safety logic, geometry engine, and test suite are implemented with **zero external dependencies** using Python 3.8+ standard library.

### Step 1: Run Automated Test Suite (30 Tests)
```bash
python run_sentinel.py --test
```
*Expected Output: `Ran 30 tests in ~0.56s ... OK`.*

### Step 2: Run Evaluation Test Matrix
```bash
python evaluation/evaluate_results.py
```
*Expected Output: `Summary: 6/6 Scenarios Passed (100.0% Success Rate)`.*

### Step 3: Run Interactive Live Simulation Demo
```bash
python run_sentinel.py --demo
```
*Demonstrates live colorized alert streaming in terminal and records incident events to `demo/sample_events.jsonl`.*

### Step 4: Stream Custom Detections or DeepStream Metadata
```bash
# Ingest mock PipeGen stream:
python run_sentinel.py --stream tests/samples/mock_pipegen_stream.jsonl --fps 15

# Ingest DeepStream nvmsgbroker payload:
python run_sentinel.py --deepstream-json tests/samples/deepstream_sample.json
```

---

## 7. Evaluation & Test Matrix Results

Measured results against the hackathon evaluation criteria:

| Scenario ID | Scenario Description | Expected Behavior | Actual Measured Result | Status |
|---|---|---|---|:---:|
| **SC-01** | Person outside zone | No intrusion event | 0 false alerts observed | **PASS** |
| **SC-02** | Person enters zone | Exactly 1 intrusion event | 1 intrusion event emitted after 2-frame debounce | **PASS** |
| **SC-03** | Person lingers in zone | No event flood | 0 duplicate alerts across 50 frames | **PASS** |
| **SC-04** | Person exits zone | Clear event with dwell time | 1 `ZONE_CLEAR` emitted with 7.73s dwell time | **PASS** |
| **SC-05** | Incomplete metadata | Graceful handling / no crash | Safely parsed without uncaught errors | **PASS** |
| **SC-06** | Repeated clean startup | Deterministic reproducibility | Engine reset restores pristine state | **PASS** |

---

## 8. 2-Minute Demo Flow

See [`demo/demo_script.md`](demo/demo_script.md) for the rehearsed 120-second pitch:
1. **0:00 - 0:15:** Industrial restricted zone problem & solution overview.
2. **0:15 - 0:40:** PipeGen 5-stage workflow & Pipeline IR graph demonstration.
3. **0:40 - 1:00:** TensorRT engine compilation & speed report ($4.29\times$ speedup, 9.8 ms latency).
4. **1:00 - 1:30:** Live video inference, 2-frame debounce, and anti-flood suppression.
5. **1:30 - 1:50:** Frozen schema v1.0 JSONL incident log & dwell time calculation.
6. **1:50 - 2:00:** Measured evaluation scorecard & wrap-up.

---

## 9. Repository Structure

```text
workplace-safety-sentinel/
├── README.md                          # Master project documentation
├── requirements.txt                   # Optional dependencies (paho-mqtt, jsonschema)
├── run_sentinel.py                    # Top-level CLI runner & entrypoint
├── docs/                              # Formal engineering specifications
│   ├── architecture.md                # System topology & state machines
│   ├── event-schema.md                # Frozen schema v1.0 field specifications
│   ├── evaluation-protocol.md         # Methodology for measuring accuracy & latency
│   ├── test-plan.md                   # Complete test cases (TC-01 through TC-08)
│   └── evidence-checklist.md          # Track A submission gate verification
├── pipegen-export/                    # Mandatory PipeGen export artifacts
│   ├── README.md                      # PipeGen 5-stage workflow guide
│   ├── requirement.yaml               # Stage 1: Requirement specification
│   ├── pipeline_ir.json               # Stage 2: Pipeline IR computation graph
│   ├── model_config.json              # Stage 3: Person detector model configuration
│   └── speed_report.json              # Stage 4: TensorRT engine speed & latency report
├── safety_events/                     # Person 2: Core Safety Logic Package
│   ├── __init__.py                    # Public API exports
│   ├── schema.json                    # Formal JSON Schema (Draft 2020-12)
│   ├── models.py                      # Data models (SafetyEvent, BoundingBox, Zone)
│   ├── zone_rules.py                  # Geometric ray-casting & feet contact logic
│   ├── tracker_state.py               # Per-track state machine with debounce & dwell
│   ├── deduplicator.py                # Spatial-temporal debouncing & flood prevention
│   ├── event_writer.py                # Crash-safe JSONL writer with atomic fsync
│   ├── adapters.py                    # PipeGen & DeepStream metadata converters
│   ├── dispatchers.py                 # Multi-destination dispatcher (JSONL, Webhook, MQTT)
│   └── engine.py                      # High-level SentinelEngine orchestrator
├── tests/                             # Automated test suite (30 test cases)
│   ├── test_zone_rules.py             # Geometric ray-casting & overlap tests
│   ├── test_tracker_state.py          # State transitions & debounce tests
│   ├── test_deduplicator.py           # Cooldown & spatial debouncing tests
│   ├── test_event_writer.py           # JSONL atomic writes & validation tests
│   ├── test_adapters.py               # Metadata translation tests
│   ├── test_dispatchers.py            # Fault isolation & network resilience tests
│   ├── test_end_to_end.py             # Multi-frame video simulation tests
│   └── samples/                       # Sample test payloads
│       ├── sample_detections.json     # Raw detection samples
│       ├── deepstream_sample.json     # Sample DeepStream nvmsgbroker payload
│       └── mock_pipegen_stream.jsonl  # Simulated PipeGen frame stream
├── evaluation/                        # Empirical evaluation tools
│   ├── test_matrix.csv                # 6-scenario evaluation scorecard
│   ├── results_template.csv           # Multi-platform compute benchmark matrix
│   └── evaluate_results.py            # Automated scorecard evaluator
├── demo/                              # Live presentation materials
│   ├── sample_events.jsonl            # Exemplar incident log output
│   ├── demo_script.md                 # 2-minute timed pitch script
│   └── simulate_live_run.py           # Real-time simulation stream runner
└── evidence/                          # Submission evidence artifacts
    ├── pipeline-ir/                   # Pipeline IR graph summary & diagram
    ├── tensorrt-report/               # TensorRT engine benchmark evidence
    ├── live-run/                      # Live execution log transcript
    └── test-results/                  # Test run verification report
```

---

## 10. Truthfulness & Limitations

In accordance with the hackathon's truthfulness rule:
- **PPE / Hardhats:** Not detected in this baseline. The pipeline integrates a specialized personnel detector. Hardhat/vest detection is documented as a future model expansion.
- **Occlusion Handling:** The per-track state machine uses a 3-frame grace period. Prolonged occlusions ($> 3$ frames) will trigger a `ZONE_CLEAR` followed by a new intrusion upon re-acquisition.
- **Hardware Agnostic Logic:** The safety logic in `safety_events/` operates independently of hardware and has been thoroughly validated against mock and real pipeline outputs.