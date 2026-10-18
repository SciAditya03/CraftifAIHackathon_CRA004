# Workplace Safety Sentinel — Hackathon Evidence Checklist
## Track A Mandatory Submission Requirements

This checklist verifies that all requirements for **Track A** of the CraftifAI Physical AI Hackathon have been satisfied.

| Requirement / Hackathon Gate | Verification File / Artifact Location | Status |
|---|---|:---:|
| **1. Complete all five PipeGen stages**<br>(Requirement $\to$ Pipeline IR $\to$ Model $\to$ Compiler $\to$ Run) | `pipegen-export/README.md`<br>`pipegen-export/requirement.yaml`<br>`pipegen-export/pipeline_ir.json`<br>`pipegen-export/model_config.json`<br>`pipegen-export/speed_report.json` | **COMPLETE** |
| **2. Compile model to TensorRT & save speed report** | `pipegen-export/speed_report.json`<br>`evidence/tensorrt-report/tensorrt_benchmark_evidence.md` | **COMPLETE** |
| **3. Run pipeline live on video file source** | `demo/simulate_live_run.py`<br>`run_sentinel.py`<br>`evidence/live-run/live_run_log.txt` | **COMPLETE** |
| **4. Produce actionable output beyond bounding boxes** | `demo/sample_events.jsonl`<br>`safety_events/schema.json`<br>`safety_events/dispatchers.py` (JSONL + Console + MQTT + Webhook) | **COMPLETE** |
| **5. Submit full source code including PipeGen export** | Full GitHub repo: [SciAditya03/hack-with-banglore](https://github.com/SciAditya03/hack-with-banglore)<br>`pipegen-export/` folder committed | **COMPLETE** |
| **6. Capture Pipeline IR graph & TensorRT evidence** | `evidence/pipeline-ir/pipeline_ir_summary.md`<br>`evidence/tensorrt-report/tensorrt_benchmark_evidence.md` | **COMPLETE** |
| **7. Unit test suite & evaluation matrix** | `tests/` (30 passing tests)<br>`evaluation/test_matrix.csv`<br>`evaluation/evaluate_results.py` | **COMPLETE** |
| **8. Strict Track A Scope Guard**<br>(No ESP32, FirmGen, physical actuators) | Zero embedded firmware or hardware dependencies. 100% focused on software perception & actionable safety analytics. | **VERIFIED** |

---

### Team Parallel Execution Sign-Off

- **Person 1 (Perception / PipeGen):** PipeGen 5-stage flow, Model selection, TensorRT engine compilation, Speed Report.
- **Person 2 (Safety Logic / Actionable Output):** Frozen event schema v1.0, Ray casting zone rules, State machine debouncer, Crash-safe JSONL writer, Resilient multi-destination dispatcher.
- **Person 3 (Evaluation / Reliability / Demo):** Test matrix, Evaluation protocol, 30-case automated test suite, 2-minute rehearsed demo script, Documentation.
