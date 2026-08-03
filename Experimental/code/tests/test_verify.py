"""Tests for the independent audit-record verifier.

The point of `lexpr.verify` is that it re-derives the winner class WITHOUT the
selector, so these tests deliberately construct records by hand rather than by
running LexPR: a verifier that agreed with the selector because it called the
selector would verify nothing.
"""
import json

import pytest

from lexpr.verify import contrastive_margin, extract_profiles, verify, winner_class


def test_winner_class_and_margin_on_a_hand_built_record():
    # C wins: sorted profiles are A=(1,1,0), B=(1,1,0), C=(0.5,0.4,0).
    profiles = {"A": [0.0, 1.0, 1.0], "B": [1.0, 0.0, 1.0], "C": [0.5, 0.4, 0.0]}
    cls, srt = winner_class(profiles)
    assert cls == ["C"]
    assert contrastive_margin(srt, "C") == pytest.approx(0.5)


def test_ties_produce_a_non_singleton_class_and_no_margin():
    profiles = {"A": [0.2, 0.7], "B": [0.7, 0.2], "C": [0.9, 0.9]}
    cls, srt = winner_class(profiles)
    assert cls == ["A", "B"]           # identical sorted profiles (0.7, 0.2)
    assert contrastive_margin(srt, "A") is None


def test_extract_profiles_accepts_label_keyed_dicts():
    rec = {"labelled_profiles": {"S1": {"f1": 0.3, "f2": 0.9}, "S2": {"f1": 0.8, "f2": 0.1}}}
    got = extract_profiles(rec)
    assert got == {"S1": [0.3, 0.9], "S2": [0.8, 0.1]}


def test_extract_profiles_rejects_unknown_shape():
    with pytest.raises(KeyError):
        extract_profiles({"something_else": {}})


def _write(tmp_path, obj):
    p = tmp_path / "rec.json"
    p.write_text(json.dumps(obj))
    return str(p)


def test_verify_returns_zero_on_a_consistent_record(tmp_path, capsys):
    rec = {
        "labelled_profiles": {"A": {"q1": 0.0, "q2": 1.0}, "B": {"q1": 0.4, "q2": 0.3}},
        "winner_class": ["B"],
        "contrastive_record": [{"rival": "A", "decide_coord": 1, "margin": 0.6}],
    }
    assert verify(_write(tmp_path, rec), expect_winner="B", expect_margin=0.6) == 0


def test_verify_flags_a_record_whose_stated_winner_is_wrong(tmp_path):
    rec = {
        "labelled_profiles": {"A": {"q1": 0.0, "q2": 1.0}, "B": {"q1": 0.4, "q2": 0.3}},
        "winner_class": ["A"],          # false: B wins
    }
    assert verify(_write(tmp_path, rec)) == 1


def test_verify_flags_a_record_whose_stated_margin_is_wrong(tmp_path):
    rec = {
        "labelled_profiles": {"A": {"q1": 0.0, "q2": 1.0}, "B": {"q1": 0.4, "q2": 0.3}},
        "winner_class": ["B"],
        "contrastive_record": [{"rival": "A", "decide_coord": 1, "margin": 0.99}],
    }
    assert verify(_write(tmp_path, rec)) == 1
