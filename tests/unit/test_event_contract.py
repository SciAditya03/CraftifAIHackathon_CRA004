import copy
import json
import os

import pytest

from contract import validate_event
import eval_lib

SAMPLES = os.path.join(os.path.dirname(__file__), "..", "samples")


def sample(name):
    return os.path.join(SAMPLES, name)


@pytest.fixture
def good():
    return eval_lib.read_jsonl(sample("fixture_single_intrusion.jsonl"))[0][0]


@pytest.mark.unit
def test_valid_event_passes(good):
    assert validate_event(good) == []


@pytest.mark.unit
@pytest.mark.parametrize("field", [
    "schema_version", "event_id", "event_type", "timestamp_utc", "camera_id",
    "track_id", "class_name", "confidence", "zone_id", "severity", "status", "source",
])
def test_missing_field_rejected(good, field):
    ev = copy.deepcopy(good)
    del ev[field]
    assert validate_event(ev), f"event without {field!r} must be rejected"


@pytest.mark.unit
@pytest.mark.parametrize("field,value", [
    ("event_type", "FIRE"),
    ("event_id", "not-a-uuid"),
    ("timestamp_utc", "yesterday"),
    ("timestamp_utc", "2026-10-18T12:00:00+05:30"),
    ("confidence", 1.5),
    ("confidence", -0.1),
    ("confidence", float("nan")),
    ("confidence", "0.9"),
    ("confidence", True),
    ("track_id", -1),
    ("track_id", "12"),
    ("track_id", 1.5),
    ("track_id", True),
    ("schema_version", "2.0"),
    ("camera_id", ""),
])
def test_invalid_value_rejected(good, field, value):
    ev = copy.deepcopy(good)
    ev[field] = value
    assert validate_event(ev), f"{field}={value!r} must be rejected"


@pytest.mark.unit
@pytest.mark.parametrize("field", ["track_id", "confidence", "zone_id", "class_name"])
def test_nullable_fields_accept_null(good, field):
    ev = copy.deepcopy(good)
    ev[field] = None
    assert validate_event(ev) == [], f"{field} may be null per contract"


@pytest.mark.unit
@pytest.mark.parametrize("bad", [None, [], "x", 5])
def test_non_object_rejected(bad):
    assert validate_event(bad)


@pytest.mark.unit
def test_event_roundtrip_serialization(good):
    again = json.loads(json.dumps(good))
    assert again == good and validate_event(again) == []


@pytest.mark.unit
def test_confidence_boundaries_ok(good):
    for c in (0, 1, 0.0, 1.0):
        ev = dict(good, confidence=c)
        assert validate_event(ev) == [], f"confidence {c} is within [0,1]"
