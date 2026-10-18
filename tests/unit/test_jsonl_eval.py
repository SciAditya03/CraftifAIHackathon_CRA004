import os

import pytest

import eval_lib

SAMPLES = os.path.join(os.path.dirname(__file__), "..", "samples")


def s(name):
    return os.path.join(SAMPLES, name)


@pytest.mark.unit
def test_empty_file_yields_nothing():
    recs, errs = eval_lib.read_jsonl(s("fixture_empty.jsonl"))
    assert recs == [] and errs == []
    assert eval_lib.summarize(s("fixture_empty.jsonl")) == {"events": 0, "invalid": 0, "duplicates": 0}


@pytest.mark.unit
def test_malformed_lines_reported_not_raised():
    recs, errs = eval_lib.read_jsonl(s("fixture_malformed.jsonl"))
    assert len(errs) == 1, "exactly one unparsable line expected"
    assert len(recs) == 3
    summ = eval_lib.summarize(s("fixture_malformed.jsonl"))
    assert summ == {"events": 1, "invalid": 3, "duplicates": 0}, summ


@pytest.mark.unit
def test_duplicate_detection_counts_repeat_track():
    summ = eval_lib.summarize(s("fixture_duplicate_intrusion.jsonl"))
    assert summ["events"] == 2 and summ["duplicates"] == 1, summ


@pytest.mark.unit
def test_null_track_ids_are_not_counted_as_duplicates():
    """Scenario F: null track must not be treated as one identity."""
    summ = eval_lib.summarize(s("fixture_null_track.jsonl"))
    assert summ["events"] == 2 and summ["duplicates"] == 0, summ


@pytest.mark.unit
def test_judge_requires_exact_count_and_no_invalid():
    assert eval_lib.judge(1, {"events": 1, "invalid": 0, "duplicates": 0}) == "PASS"
    assert eval_lib.judge(1, {"events": 2, "invalid": 0, "duplicates": 1}) == "FAIL"
    assert eval_lib.judge(0, {"events": 0, "invalid": 1, "duplicates": 0}) == "FAIL"


@pytest.mark.unit
def test_write_results_roundtrip(tmp_path):
    import csv
    p = tmp_path / "r.csv"
    eval_lib.write_results(str(p), [{"scenario_id": "X", "status": "PASS"}])
    rows = list(csv.DictReader(open(p, encoding="utf-8")))
    assert rows[0]["scenario_id"] == "X" and rows[0]["status"] == "PASS"
    assert list(rows[0].keys()) == eval_lib.RESULT_FIELDS


@pytest.mark.unit
def test_repeated_processing_is_idempotent():
    a = eval_lib.summarize(s("fixture_single_intrusion.jsonl"))
    b = eval_lib.summarize(s("fixture_single_intrusion.jsonl"))
    assert a == b == {"events": 1, "invalid": 0, "duplicates": 0}
