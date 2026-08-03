from pathlib import Path

import pytest

from lexpr.manuscript import (
    PublicationEvidence,
    check_manuscript,
    load_publication_evidence,
)
from lexpr.figure_evidence import AUTHORITATIVE_RUN_ID


REPO_ROOT = Path(__file__).resolve().parents[2]
CLAIMS = REPO_ROOT / "code" / "configs" / "claims.yaml"


def test_evidence_is_pinned_to_frozen_run_not_mutable_config():
    """Manuscript constants must come from the immutable authoritative run,
    so editing code/configs/full_config.yaml cannot change them (no drift)."""
    evidence = load_publication_evidence(REPO_ROOT, CLAIMS)

    assert evidence.run_id == AUTHORITATIVE_RUN_ID
    assert evidence.instances == 7200
    assert evidence.methods == 11
    assert evidence.geometries == 8
    assert evidence.families == 10
    assert evidence.nemenyi_cd == pytest.approx(0.1779369, abs=1e-6)
    assert evidence.average_ranks["LexPR"] == pytest.approx(4.67, abs=0.05)
    # gates come from the frozen run and all carry its run id
    assert evidence.gates
    assert all(row["run_id"] == AUTHORITATIVE_RUN_ID for row in evidence.gates)


def _evidence():
    return PublicationEvidence(
        run_id="run-a",
        instances=7200,
        methods=11,
        geometries=8,
        families=10,
        nemenyi_cd=0.31,
        average_ranks={"LexPR": 4.67},
        noninferiority={},
        gates=[],
        claims={},
    )


def test_checker_rejects_stale_instance_count(tmp_path: Path):
    tex = tmp_path / "main.tex"
    tex.write_text("The protocol contains 2,400 paired instances.\n")

    result = check_manuscript([tex], _evidence())

    assert any("2,400" in error for error in result.errors)


def test_checker_accepts_generated_instance_macro(tmp_path: Path):
    tex = tmp_path / "main.tex"
    tex.write_text("The protocol contains \\protocolInstances{} paired instances.\n")

    result = check_manuscript([tex], _evidence())

    assert result.errors == []


def test_checker_rejects_stale_method_and_geometry_counts(tmp_path: Path):
    tex = tmp_path / "main.tex"
    tex.write_text("The audit uses 12 methods and 6 geometries.\n")

    result = check_manuscript([tex], _evidence())

    assert len(result.errors) == 2


def test_conceptual_figures_distinguish_exact_and_reporting_tolerances():
    pipeline = (REPO_ROOT / "paper/tikz/fig_pipeline.tex").read_text()
    algorithm = (REPO_ROOT / "paper/sections/04_direct.tex").read_text()
    pareto = (REPO_ROOT / "paper/tikz/fig_pareto_cert.tex").read_text()
    concept = (REPO_ROOT / "paper/tikz/fig_cert_concept.tex").read_text()

    assert "stability class" in pipeline
    assert r"\tau=0" in algorithm
    assert r"\tau$-class" in algorithm
    assert r"\beta=0.01" in pareto
    assert "illustrative" in concept.lower()
    assert r"\beta=0.01" in concept


def test_probe_figure_does_not_claim_cluster_probes_replace_singletons():
    text = (REPO_ROOT / "paper/tikz/fig_probes.tex").read_text()

    assert "instead of one per member" not in text
    assert "singleton probes remain" in text


def test_empirical_figure_captions_match_corrected_evidence():
    probes = (REPO_ROOT / "paper/sections/05_probes.tex").read_text()
    experiments = (REPO_ROOT / "paper/sections/07_experiments.tex").read_text()

    assert "$c=0$" in probes
    assert "LexPR groups with CP" in experiments
    assert "groups with the best methods" not in experiments
    assert "most balanced row" not in experiments
    assert "RMS normalised criterion distance" in experiments
    assert "paired" in experiments
    # Per referee revision: alpha=0.95 (which conflated significance and confidence
    # levels) was replaced by an explicit 95% confidence-level statement.
    assert r"\alpha=0.95" not in experiments
    assert "confidence level $0.95$" in experiments
