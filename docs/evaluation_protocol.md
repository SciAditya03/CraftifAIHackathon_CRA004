# Evaluation Protocol

This is a **functional evaluation**, not a formal accuracy benchmark. No labelled dataset is used; model mAP/precision/recall are **not claimed**.

## Result levels (never mix)
1. **Unit** — isolated logic, no GPU (`tests/unit`).
2. **Fixture self-check** — evaluator run on synthetic fixtures (`FX*` rows). Not system results.
3. **Integration** — Person 2 engine fed scripted detections; output JSONL at `evaluation/outputs/<ID>.jsonl`.
4. **Live** — real PipeGen/DeepStream run (H, J).

## Procedure
1. Choose a short, licence-cleared clip; hand-label expected events per scenario (frame ranges, expected count). Record in `evaluation/labels/`.
2. Produce `evaluation/outputs/<ID>.jsonl` for each scenario.
3. `python evaluation/run_evaluation.py` → `evaluation/results.csv`.
4. A scenario is PASS only if the file exists, every record validates against the contract, and the event count equals the label.
5. Copy PipeGen-reported FPS/latency verbatim from the speed report into `evaluation/evaluation_summary.md`; record model, precision, resolution.
6. End-to-end latency: only if both timestamps come from one clock; otherwise report "not measured".

Statuses: PASS, FAIL, BLOCKED, NOT_TESTED. Scenarios A–J are defined in `evaluation/test_matrix.csv`. Repeated startup (H): ≥3 clean starts, record each outcome.
