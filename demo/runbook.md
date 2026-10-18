# Runbook — UNVERIFIED TEMPLATE

> No PipeGen export exists yet; the commands for the pipeline are **pending Person 1**. Nothing below marked TODO has been run.

## Verified (QA tooling)
```
python -m pytest
python evaluation/run_evaluation.py
python tools/check_release.py
```

## Pipeline start (TODO — Person 1 to supply exact commands)
- Platform: x86-64 Linux + NVIDIA GPU, or Jetson JetPack 6; PipeGen v0.5.1 (confirm). Not verified on the current Windows host.
- Input: local video, path `TODO`.
- Start command: `TODO` (from `pipegen-export/`).
- Expected outputs: annotated output, JSONL at `TODO`.

## Clean-start rehearsal log (need ≥3)
| Run | Date | Result | Notes |
|---|---|---|---|
| 1 | — | NOT TESTED | |
| 2 | — | NOT TESTED | |
| 3 | — | NOT TESTED | |

## Pre-demo checks
Pre-open: PipeGen IR, speed report, terminal with pipeline command, JSONL tail. No internet dependency. Run `python tools/check_release.py` before presenting.
