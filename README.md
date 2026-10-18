Workplace Safety Sentinel CraftifAI Physical AI Hackathon --- Track A
Only A PipeGen-Powered, TensorRT-Accelerated Workplace Safety &
Restricted-Zone Analytics System

Tests PipeGen TensorRT DeepStream Schema Scope

## Latest Integration Status --- 18 October 2026

**Repository status:** `person3-evaluation` has been merged into `main`
and pushed to GitHub.\
**Integration commit:** `009b069`\
**Integrated components:** Person 1's PipeGen perception pipeline,
Person 2's safety events engine, and Person 3's evaluation and
release-verification tooling.

### Person 3 Deliverables Integrated

-   Evaluation matrix runner: `evaluation/run_evaluation.py`
-   Evaluation helpers: `evaluation/eval_lib.py`
-   Scenario matrix: `evaluation/person3_test_matrix.csv`
-   Integration tests: `tests/integration/test_person2_integration.py`
-   Unit tests: `tests/unit/test_event_contract.py`,
    `tests/unit/test_jsonl_eval.py`
-   Release gate verifier: `tools/check_release.py`
-   Runbook and status documentation: `demo/runbook.md`,
    `docs/integration_issues.md`, `docs/project_status.md`
-   Evaluation output generator: `tools/generate_evaluation_outputs.py`
-   Release evidence report: `evidence/evaluation/evaluation_report.md`
-   Generated scenario outputs: `evaluation/outputs/` (A--J)

### Reliability Fix

**ISSUE-1 resolved:** The integration test identified that
`payload.get("detections")` could return `None`, which could cause a
`TypeError`. The adapter handling in `safety_events/adapters.py` was
hardened to validate that the raw detections value is a list.
`parse_single_detection` was also safeguarded against non-dictionary and
non-numeric inputs.

### Latest Verification Results

  -----------------------------------------------------------------------
  Check                               Result
  ----------------------------------- -----------------------------------
  Live demo                           Completed; 10 frames processed
  (`python run_sentinel.py --demo`)   

  Detections processed                10

  Intrusion events emitted            1

  Clear events emitted                1

  System-health events emitted        1

  Scenario matrix A--J                **10/10 PASS (100%)**

  Full pytest suite                   **87 passed, 1 skipped**

  Release evidence gate               **All 7 mandatory Track A evidence
                                      gates present**
  -----------------------------------------------------------------------

The evaluator's `FX3` self-check deliberately supplies a
duplicate-intrusion fixture and expects the evaluator to flag it. Its
`FAIL` line means the evaluator correctly detected the intentionally
invalid fixture; it is not one of the ten A--J product scenarios. All
A--J scenarios passed.

### Commands --- Current Evaluation and Release Checks

Run these from the repository root:

``` bash
# Live perception and safety event demonstration
python run_sentinel.py --demo

# Person 3's A–J scenario evaluation matrix
python evaluation/run_evaluation.py

# Verify mandatory Track A release evidence
python tools/check_release.py

# Run the complete test suite
python -m pytest -v
```

The latest recorded full-suite result is **87 passed, 1 skipped**. The
release verifier confirmed the presence of the PipeGen export, Pipeline
IR evidence, TensorRT engine/speed report, live-run evidence, automated
test output, evaluation evidence, and actionable event log at
`evaluation/outputs/J.jsonl`.

------------------------------------------------------------------------

1.  Executive Summary Workplace Safety Sentinel is an edge
    computer-vision safety system designed to prevent severe injuries
    near dangerous industrial machinery and automated robotic workcells.
    Built using CraftifAI PipeGen, the system executes a
    person-detection pipeline compiled into a high-performance TensorRT
    engine and deployed via NVIDIA DeepStream.

When personnel enter designated hazardous zones, the sentinel evaluates
geometric safety boundaries (ground-plane feet contact or bounding box
centroid) and emits structured, debounced, actionable incident records
(in standardized JSONL, console alerts, and optional MQTT/Webhook
feeds).

Scope & Guardrails Track A Focused: 100% pure software, edge perception,
and actionable digital analytics. Explicitly Out of Scope: No ESP32,
STM32, FirmGen, physical relays, or embedded actuation. Privacy-First:
Strict bounding-box and tracking analytics only. Zero face recognition
or biometric identification. 2. 3-Person Parallel Ownership Role Core
Ownership Independent Deliverables Hackathon Artifacts Person 1
Perception & PipeGen Five-stage PipeGen flow, model selection, TensorRT
engine compilation, live video run. PipeGen project export, compiled
engine specs, speed profiling report, Pipeline IR DAG. pipegen-export/
evidence/pipeline-ir/ evidence/tensorrt-report/ Person 2 Safety Logic &
Output Frozen event schema v1.0, polygon ray casting, per-track state
debouncing, crash-safe JSONL writer, adapters. Geometric zone evaluator,
cooldown logic, fault-isolated dispatchers, unit tests. safety_events/
safety_events/schema.json tests/ Person 3 Evaluation & Reliability Test
video matrix, evaluation protocol, failure analysis, 2-minute demo
pitch, documentation. Evaluation protocol, test matrix scorecard,
repeatability checklist, demo rehearsal. evaluation/ demo/ docs/ 3.
System Architecture Local Video File (MP4) / RTSP \| v CraftifAI PipeGen
Pipeline: Requirement -\> Pipeline IR -\> Model -\> Compiler -\> Run \|
v TensorRT FP16 Engine + DeepStream 7.0 Pipeline (9.8 ms latency, 78.4
FPS) \| +----\> Annotated Video Display / OSD Sink \| v Metadata Adapter
(PipeGen Frame / DeepStream nvmsgbroker / pyds Probe) \| v Safety
Sentinel Engine: - Ray-Casting Point-in-Polygon (Feet ground-plane
rule) - Per-Track State Machine (2-frame debounce, 3-frame exit grace) -
Spatial-Temporal Debouncer (Untracked object fallback) \| +----\>
Primary Sink: Durable JSONL Incident Log (Crash-safe atomic fsync)
+----\> Primary Sink: Colorized Real-Time Console Alert Streamer +----\>
Secondary Sink (Optional): HTTP Webhook / MQTT Alert Feed 4. CraftifAI
PipeGen Five-Stage Gates Detailed walkthrough:
docs/pipegen-five-stages.md \| Perception Handoff Contract:
docs/person1-perception-handoff.md

All five mandatory PipeGen gates have been executed and documented:

Requirement Stage (pipegen-export/requirement.yaml): Defined industrial
person detection, restricted dangerous zones, real-time latency target (
≤ 33 ms ), and JSONL incident output. Pipeline IR Stage
(pipegen-export/pipeline_ir.json): Generated 7-node declarative
computation graph linking video demuxing, GPU decoder, nvstreammux,
TensorRT nvinfer, nvtracker, safety pad probe, and OSD sink. Renderable
via python scripts/render_pipeline_ir.py. Model Selection Stage
(pipegen-export/model_config.json): Selected CSPDarknet/YOLO person
detector ( 640 × 640 input) from the PipeGen catalog. Compiler Stage
(pipegen-export/speed_report.json): Compiled engine to TensorRT FP16 via
python pipegen-export/compile_tensorrt.py, dropping latency from 42.14
ms to 9.82 ms (4.29x speedup, 101.8 FPS engine / 78.4 FPS end-to-end).
Run Stage (pipegen-export/deepstream_pipeline.py / run_sentinel.py):
Live execution on local video stream with GStreamer pad probe streaming
validated actionable events. 5. Frozen Event Schema (v1.0) All events
emitted by Workplace Safety Sentinel strictly adhere to
safety_events/schema.json:

{ "schema_version": "1.0", "event_id":
"8d39f72a-4bc1-49b0-9a2c-901d8194b150", "event_type": "ZONE_INTRUSION",
"timestamp_utc": "2026-10-18T12:00:04.120Z", "camera_id":
"video-demo-01", "track_id": 12, "class_name": "person", "confidence":
0.934, "zone_id": "restricted-zone-01", "severity": "high", "status":
"active", "source": "pipegen-deepstream", "bbox": \[0.412, 0.355, 0.518,
0.612\], "dwell_time_seconds": 0.0, "details": { "rule_type":
"feet_point", "consecutive_frames": 2 } } Event Types ZONE_INTRUSION:
Emitted when an unauthorized person crosses into a restricted zone.
ZONE_CLEAR: Emitted when a person leaves the zone and remains outside
through the grace period (includes total dwell duration). SYSTEM_HEALTH:
Emitted on pipeline initialization, frame rate degradation, or camera
disconnection. 6. Repeatable Quickstart Instructions The core safety
logic, geometry engine, and test suite are implemented with zero
external dependencies using Python 3.8+ standard library.

Step 1: Run the Full Automated Test Suite python -m pytest -v Latest
integrated result: 87 passed, 1 skipped.

Step 2: Run the Integrated Person 3 Evaluation Matrix python
evaluation/run_evaluation.py Latest integrated result: all 10 scenarios
(A--J) passed.

Step 3: Run Interactive Live Simulation Demo python run_sentinel.py
--demo Demonstrates live colorized alert streaming in terminal and
records incident events to demo/sample_events.jsonl.

Step 4: Stream Custom Detections or DeepStream Metadata \# Ingest mock
PipeGen stream: python run_sentinel.py --stream
tests/samples/mock_pipegen_stream.jsonl --fps 15

# Ingest DeepStream nvmsgbroker payload:

python run_sentinel.py --deepstream-json
tests/samples/deepstream_sample.json Step 5: Execute PipeGen Compilation
& DeepStream Pipeline (Person 1 Lead) \# Compile TensorRT FP16 engine
and generate speed report (Stage 4): python
pipegen-export/compile_tensorrt.py --precision FP16 --workspace 2048

# Render Pipeline IR DAG diagram (Stage 2):

python scripts/render_pipeline_ir.py

# Run live DeepStream pipeline with pad probe (Stage 5):

python pipegen-export/deepstream_pipeline.py --source
test_assets/safety_video.mp4 7. Evaluation & Test Matrix Results
Measured results against the hackathon evaluation criteria:

Scenario ID Scenario Description Expected Behavior Actual Measured
Result Status SC-01 Person outside zone No intrusion event 0 false
alerts observed PASS SC-02 Person enters zone Exactly 1 intrusion event
1 intrusion event emitted after 2-frame debounce PASS SC-03 Person
lingers in zone No event flood 0 duplicate alerts across 50 frames PASS
SC-04 Person exits zone Clear event with dwell time 1 ZONE_CLEAR emitted
with 7.73s dwell time PASS SC-05 Incomplete metadata Graceful handling /
no crash Safely parsed without uncaught errors PASS SC-06 Repeated clean
startup Deterministic reproducibility Engine reset restores pristine
state PASS 8. 2-Minute Demo Flow See demo/demo_script.md for the
rehearsed 120-second pitch:

0:00 - 0:15: Industrial restricted zone problem & solution overview.
0:15 - 0:40: PipeGen 5-stage workflow & Pipeline IR graph demonstration.
0:40 - 1:00: TensorRT engine compilation & speed report ( 4.29 ×
speedup, 9.8 ms latency). 1:00 - 1:30: Live video inference, 2-frame
debounce, and anti-flood suppression. 1:30 - 1:50: Frozen schema v1.0
JSONL incident log & dwell time calculation. 1:50 - 2:00: Measured
evaluation scorecard & wrap-up. 9. Repository Structure
workplace-safety-sentinel/ ├── README.md \# Master project documentation
├── requirements.txt \# Optional dependencies (paho-mqtt, jsonschema)
├── run_sentinel.py \# Top-level CLI runner & entrypoint ├── docs/ \#
Formal engineering specifications │ ├── architecture.md \# System
topology & state machines │ ├── event-schema.md \# Frozen schema v1.0
field specifications │ ├── evaluation-protocol.md \# Methodology for
measuring accuracy & latency │ ├── test-plan.md \# Complete test cases
(TC-01 through TC-08) │ ├── evidence-checklist.md \# Track A submission
gate verification │ ├── pipegen-five-stages.md \# PipeGen v0.5.1 5-stage
comprehensive guide │ └── person1-perception-handoff.md \#
Perception-to-safety metadata contract ├── pipegen-export/ \# Mandatory
PipeGen export artifacts │ ├── README.md \# PipeGen 5-stage workflow
guide │ ├── requirement.yaml \# Stage 1: Requirement specification │ ├──
pipeline_ir.json \# Stage 2: Pipeline IR computation graph │ ├──
model_config.json \# Stage 3: Person detector model configuration │ ├──
speed_report.json \# Stage 4: TensorRT engine speed & latency report │
├── compile_tensorrt.py \# Stage 4: Engine compilation & profiling
utility │ ├── deepstream_pipeline.py \# Stage 5: Live DeepStream
GStreamer pipeline & pad probe │ ├── pipegen_cli_workflow.sh \# Stage
1-5 automated CLI workflow script │ ├── config_infer_primary.txt \#
DeepStream nvinfer configuration file │ ├── config_tracker_NvSORT.yml \#
DeepStream NvSORT tracker configuration │ └── labels.txt \# Class labels
(person) ├── scripts/ │ └── render_pipeline_ir.py \# Visual DAG diagram
renderer (SVG generator) ├── safety_events/ \# Person 2: Core Safety
Logic Package │ ├── **init**.py \# Public API exports │ ├── schema.json
\# Formal JSON Schema (Draft 2020-12) │ ├── models.py \# Data models
(SafetyEvent, BoundingBox, Zone) │ ├── zone_rules.py \# Geometric
ray-casting & feet contact logic │ ├── tracker_state.py \# Per-track
state machine with debounce & dwell │ ├── deduplicator.py \#
Spatial-temporal debouncing & flood prevention │ ├── event_writer.py \#
Crash-safe JSONL writer with atomic fsync │ ├── adapters.py \# PipeGen &
DeepStream metadata converters │ ├── dispatchers.py \# Multi-destination
dispatcher (JSONL, Webhook, MQTT) │ └── engine.py \# High-level
SentinelEngine orchestrator ├── tests/ \# Automated unit, integration,
and end-to-end tests │ ├── test_zone_rules.py \# Geometric ray-casting &
overlap tests │ ├── test_tracker_state.py \# State transitions &
debounce tests │ ├── test_deduplicator.py \# Cooldown & spatial
debouncing tests │ ├── test_event_writer.py \# JSONL atomic writes &
validation tests │ ├── test_adapters.py \# Metadata translation tests │
├── test_dispatchers.py \# Fault isolation & network resilience tests │
├── test_end_to_end.py \# Multi-frame video simulation tests │ └──
samples/ \# Sample test payloads │ ├── sample_detections.json \# Raw
detection samples │ ├── deepstream_sample.json \# Sample DeepStream
nvmsgbroker payload │ └── mock_pipegen_stream.jsonl \# Simulated PipeGen
frame stream ├── evaluation/ \# Empirical evaluation tools │ ├──
person3_test_matrix.csv \# Integrated A--J scenario matrix │ ├──
run_evaluation.py \# Scenario matrix runner │ ├── eval_lib.py \#
Evaluation helper library │ ├── outputs/ \# Generated JSONL outputs for
scenarios A--J │ └── results.csv \# Latest evaluation scorecard ├──
demo/ \# Live presentation materials │ ├── sample_events.jsonl \#
Exemplar incident log output │ ├── demo_script.md \# 2-minute timed
pitch script │ └── simulate_live_run.py \# Real-time simulation stream
runner └── evidence/ \# Submission evidence artifacts ├── pipeline-ir/
\# Pipeline IR graph summary & diagram ├── tensorrt-report/ \# TensorRT
engine benchmark evidence ├── live-run/ \# Live execution log transcript
└── test-results/ \# Test run verification report 10. Truthfulness &
Limitations In accordance with the hackathon's truthfulness rule:

PPE / Hardhats: Not detected in this baseline. The pipeline integrates a
specialized personnel detector. Hardhat/vest detection is documented as
a future model expansion. Occlusion Handling: The per-track state
machine uses a 3-frame grace period. Prolonged occlusions ( \> 3 frames)
will trigger a ZONE_CLEAR followed by a new intrusion upon
re-acquisition. Hardware Agnostic Logic: The safety logic in
safety_events/ operates independently of hardware and has been
thoroughly validated against mock and real pipeline outputs.
