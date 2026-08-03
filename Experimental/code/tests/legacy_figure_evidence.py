from pathlib import Path

import pytest

from lexpr.figure_evidence import AUTHORITATIVE_RUN_ID, load_protocol_evidence


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_protocol_loader_is_pinned_to_authoritative_run():
    evidence = load_protocol_evidence(REPO_ROOT)

    assert evidence.run_id == AUTHORITATIVE_RUN_ID
    assert evidence.n_instances == 7200
    assert len(evidence.method_names) == 11
    assert evidence.nemenyi_cd == pytest.approx(0.1779369200025672)


def test_figure_seven_generator_does_not_read_current_symlink():
    script = (REPO_ROOT / "code/scripts/regen_cd_protocol.py").read_text()

    assert "results/protocol/current" not in script
    assert "load_protocol_evidence" in script


def test_main_fallback_has_authoritative_cd():
    text = (REPO_ROOT / "paper/main.tex").read_text()

    assert r"\newcommand{\protocolCD}{0.178}" in text
    assert r"\newcommand{\protocolCD}{0.31}" not in text
