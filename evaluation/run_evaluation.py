"""Run the scenario matrix and write evaluation/results.csv.

Status vocabulary: PASS, FAIL, BLOCKED (input/component absent), NOT_TESTED.
A scenario is never PASS unless its input file exists and counts match exactly.
FX* rows only self-check the evaluator on synthetic fixtures; they are not system results.
"""
import csv
import os
import platform
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import eval_lib  # noqa: E402


def main():
    env = f"{platform.platform()}; python {platform.python_version()}; no PipeGen/DeepStream verified"
    rows = []
    with open(os.path.join(HERE, "person3_test_matrix.csv"), encoding="utf-8") as fh:
        for m in csv.DictReader(fh):
            row = {
                "scenario_id": m["scenario_id"], "level": m["level"], "input": m["input"],
                "expected_outcome": m["description"], "expected_events": m["expected_events"],
                "environment": env,
            }
            path = os.path.join(ROOT, m["input"]) if m["input"] else ""
            if not m["input"] or not os.path.isfile(path):
                row.update(status="BLOCKED", observed_outcome="not run",
                           error_details=f"requires {m['requires']}; input missing: {m['input'] or 'n/a'}")
            elif m["expected_events"] == "":
                row.update(status="NOT_TESTED", error_details="expected count not yet labelled")
            else:
                s = eval_lib.summarize(path, m["event_type"])
                st = eval_lib.judge(int(m["expected_events"]), s)
                row.update(status=st, actual_events=s["events"], invalid_records=s["invalid"],
                           duplicate_events=s["duplicates"], evidence=m["input"],
                           observed_outcome=f"{s['events']} {m['event_type']} event(s)")
            rows.append(row)
    out = os.path.join(HERE, "results.csv")
    eval_lib.write_results(out, rows)
    for r in rows:
        print(f"{r['scenario_id']:4} {r['status']:10} {r.get('error_details', '')}")
    print("wrote", out)


if __name__ == "__main__":
    main()
