# Demo Script (~2 min) — draft; fill `[ ]` only with measured values

- **0:00–0:15 Problem:** Restricted areas at workplaces need actionable alerts, not just boxes. This prototype detects people with a PipeGen-built pipeline and logs intrusions. Video-based only; no hardware.
- **0:15–0:40 PipeGen:** Show Requirement → Pipeline IR → Model → Compiler → Run (`evidence/pipeline-ir`).
- **0:40–1:00 TensorRT:** Show compiled engine and PipeGen speed report: model [ ], precision [ ], FPS [ ] (copy from report).
- **1:00–1:30 Live:** Run the generated pipeline on the clip (command from runbook); show detections.
- **1:30–1:50 Actionable result:** `tail` the real JSONL; show one event [ ] (only if genuinely generated).
- **1:50–2:00 Results/limits:** Scenario results from `evaluation/results.csv`; state functional (not benchmark) evaluation, and any BLOCKED/failed items.

Fallback: backup recording in `evidence/live-run` (not yet captured). Adjust if zone metadata isn't available — then show the supported analytics output and say so.
