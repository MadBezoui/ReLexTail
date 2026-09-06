"""The three frozen rational examples must keep exhibiting their property."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from certrelex import examples as ex  # noqa: E402


def test_boundary_example_separates_the_two_gates():
    out = ex.check_boundary()
    assert out["candidates_leaving_cells"], "no candidate leaves its cell"
    assert not out["global_gate_passes"]
    assert out["decision_gate_certifies_root"]


def test_slack_example_separates_the_two_enclosures():
    out = ex.check_slack(budget=1024)
    assert out["joint"]["certified"] and out["joint"]["boxes"] == 1
    assert not out["independent"]["certified"]
    assert out["independent"]["certified_volume"] < 1.0


def test_switch_example_brackets_the_radius():
    out = ex.check_switch(budget=256)
    assert out["nominal_winner"] == ex.SWITCH["nominal_winner"]
    assert out["witness_winner_class"] == [ex.SWITCH["witness_winner"]]
    assert out["bracket_is_valid"]
    assert 0.0 < out["certified_radius_lower"] < ex.SWITCH["witness_level"]
