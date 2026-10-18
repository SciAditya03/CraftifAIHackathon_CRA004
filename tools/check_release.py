"""Release/evidence gate. Exit 0 only if every mandatory item exists. Never fakes presence."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = (".png", ".jpg", ".jpeg", ".webp", ".mp4", ".mkv", ".webm", ".txt", ".json", ".md", ".log", ".jsonl", ".pdf")


def has_files(rel, exclude=("README.md", ".gitkeep")):
    d = os.path.join(ROOT, rel)
    if not os.path.isdir(d):
        return False
    return any(f not in exclude and f.lower().endswith(IMG) for _, _, fs in os.walk(d) for f in fs)


CHECKS = [
    ("PipeGen export folder with content", "pipegen-export"),
    ("Pipeline IR screenshot", "evidence/pipeline-ir"),
    ("TensorRT engine/speed report", "evidence/tensorrt-report"),
    ("Live run screenshot/recording", "evidence/live-run"),
    ("Automated test output", "evidence/test-results"),
    ("Evaluation evidence", "evidence/evaluation"),
    ("Actionable event log from real run", "evaluation/outputs/J.jsonl"),
]


def main():
    missing = 0
    for label, rel in CHECKS:
        p = os.path.join(ROOT, rel)
        ok = os.path.isfile(p) if rel.endswith(".jsonl") else has_files(rel)
        print(f"[{'PRESENT' if ok else 'MISSING'}] {label}: {rel}")
        missing += not ok
    print(f"\n{missing} mandatory item(s) missing" if missing else "\nall mandatory evidence present")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
