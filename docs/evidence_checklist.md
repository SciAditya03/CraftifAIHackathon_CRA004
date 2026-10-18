# Evidence Checklist (Track A)

Status as of 2026-10-18. Only mark verified after the file exists (`python tools/check_release.py`).

| # | Item | Folder | Status | Collection procedure |
|---|---|---|---|---|
| 1 | Requirement-stage screenshot | evidence/pipeline-ir | Awaiting access (Person 1) | Screenshot PipeGen Requirement page with the workplace-safety requirement text |
| 2 | Pipeline IR node graph screenshot | evidence/pipeline-ir | Awaiting access | Screenshot IR graph |
| 3 | Selected model + configuration | evidence/pipeline-ir | Awaiting access | Screenshot/export model stage; note precision |
| 4 | TensorRT compilation success | evidence/tensorrt-report | Awaiting access | Screenshot/log of Compiler stage completing; engine file listing |
| 5 | PipeGen speed report | evidence/tensorrt-report | Awaiting access | Save report file/screenshot unedited |
| 6 | Live run screenshot/recording (video source visible) | evidence/live-run | Awaiting access | Run generated pipeline per demo/runbook.md |
| 7 | Actionable output (real JSON incident) | evaluation/outputs/J.jsonl | Awaiting access | Copy JSONL produced by the real run; no mock substitution |
| 8 | Automated test output | evidence/test-results | **Verified and present** (`pytest_run1.txt`; unit only, 11 blocked) | `python -m pytest` |
| 9 | Evaluation results + limitations | evidence/evaluation | Missing (only BLOCKED/fixture rows exist) | After integration run |
| 10 | Tested startup instructions + repo link | demo/runbook.md | Missing (unverified) | 3 clean-start rehearsals |
| 11 | PipeGen export folder `pipegen-export/` | repo root | Missing | Person 1 commits export |
| 12 | 60–90 s backup recording | evidence/live-run | Missing | Record after item 6 |
