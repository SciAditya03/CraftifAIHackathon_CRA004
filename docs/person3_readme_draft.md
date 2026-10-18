# Workplace Safety Sentinel — Track A (CraftifAI PipeGen)

Video-based person detection and restricted-zone intrusion events for workplace safety. **Status: NOT READY — see [docs/project_status.md](docs/project_status.md).**

## Problem & Track A
Restricted areas need actionable alerts. Perception is a **CraftifAI PipeGen** pipeline (Requirement → Pipeline IR → Model → Compiler → Run) compiled to TensorRT and executed via DeepStream. Supporting Python (event logic, QA tools) only consumes its output. No embedded hardware (ESP32/STM32/FirmGen) is in scope.

## Architecture
See [docs/architecture.md](docs/architecture.md).

## Repository structure
```
docs/        status, architecture, protocol, test plan, evidence checklist
tests/       unit/ integration/ regression/ samples/ support/
evaluation/  test_matrix.csv, run_evaluation.py, results.csv
tools/       check_release.py, make_fixtures.py
demo/        runbook.md, demo_script.md
evidence/    pipeline-ir/ tensorrt-report/ live-run/ test-results/ evaluation/
pipegen-export/   (PENDING — Person 1)    safety_events/ (PENDING — Person 2)
```

## Prerequisites (verified on QA host)
Python 3.13.3, pytest 9.0.2. Pipeline requirements (PipeGen v0.5.1, Linux+NVIDIA GPU/Jetson) are **not yet verified**.

## Run the pipeline
Pending Person 1 — see [demo/runbook.md](demo/runbook.md). No pipeline command is documented yet.

## Tests
```
python -m pytest
python evaluation/run_evaluation.py
python tools/check_release.py
```
Last run: 45 passed, 11 skipped (BLOCKED). Output: `evidence/test-results/pytest_run1.txt`.

## Evaluation
Functional evaluation only; see [docs/evaluation_protocol.md](docs/evaluation_protocol.md). Actual results: scenarios A–J **BLOCKED** (components absent); fixture self-checks FX1/FX2 pass, FX3 fails by design. No FPS, latency, or accuracy figures exist yet.

## Evidence
[docs/evidence_checklist.md](docs/evidence_checklist.md) — only test output is present.

## Known limitations
No PipeGen export, no event engine, no real run, no labelled clip. Fixtures are synthetic.

## Team
Person 1: PipeGen/perception. Person 2: event logic/output. Person 3: evaluation, reliability, evidence, demo.
