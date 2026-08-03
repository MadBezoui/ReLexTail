import pandas as pd
import pytest

from lexpr.reporting import (
    analyze_benchmark,
    build_gate_report,
    ensure_registered_gates,
)
from run_protocol import _benchmark_finalize_from_records, configure_output_root


def _gate(rows, name):
    return next(row for row in rows if row["gate"] == name)


def test_gate_report_uses_current_benchmark_analysis_not_stale_legacy_stats():
    current = {
        "run_id": "new",
        "noninferiority": {
            "ASF": {
                "noninferior": True,
                "mean_diff": 0.001,
                "ci": [-0.001, 0.003],
            },
            "MMR": {
                "noninferior": True,
                "mean_diff": 0.002,
                "ci": [0.0, 0.004],
            },
        },
        "wilcoxon_vs_LexPR": {},
    }
    stale = {
        "run_id": "old",
        "noninferiority": {
            "ASF": {"noninferior": False},
            "MMR": {"noninferior": False},
        },
    }

    rows = build_gate_report(
        {"benchmark_analysis": current, "benchmark_stats": stale},
        cfg={},
        run_id="new",
    )

    assert _gate(rows, "tail_noninferiority_asf")["result"] == "PASS"
    assert _gate(rows, "tail_noninferiority_mmr")["result"] == "PASS"


def test_gate_report_rejects_analysis_from_another_run():
    with pytest.raises(ValueError, match="run_id"):
        build_gate_report(
            {"benchmark_analysis": {"run_id": "old"}},
            cfg={},
            run_id="new",
        )


def test_gate_report_marks_missing_benchmark_evidence():
    rows = build_gate_report({}, cfg={}, run_id="new")
    assert _gate(rows, "tail_noninferiority_asf")["result"] == "MISSING"
    assert _gate(rows, "tail_noninferiority_mmr")["result"] == "MISSING"


def test_gate_report_preserves_failed_adaptive_probe_evidence():
    analysis = {
        "run_id": "new", "noninferiority": {}, "wilcoxon_vs_LexPR": {}
    }
    adaptive = {
        "run_id": "new",
        "predictive_quality": False,
        "certificate_approximation": False,
        "decision_set_agreement": False,
        "worst_regret_gap": 0.09,
        "certificate_sup_norm_gap": 0.60,
        "winner_agreement": 0.25,
        "thresholds": {
            "max_worst_regret_gap": 0.05,
            "max_certificate_gap": 0.1,
            "min_winner_agreement": 0.8,
        },
    }

    rows = build_gate_report(
        {"benchmark_analysis": analysis, "adaptive": adaptive},
        cfg={},
        run_id="new",
    )

    assert _gate(rows, "probe_tail_gap")["result"] == "CHECK"
    assert _gate(rows, "probe_certificate_gap")["result"] == "CHECK"
    assert _gate(rows, "probe_tolerance_overlap")["result"] == "CHECK"



def test_registered_gate_without_evidence_is_explicitly_missing():
    claims = {"C1": {"gates": ["present", "absent"]}}
    rows = [{
        "run_id": "new", "gate": "present", "result": "PASS",
        "threshold": None, "estimate": None, "detail": "ok",
    }]

    completed = ensure_registered_gates(rows, claims, "new")

    assert _gate(completed, "absent")["result"] == "MISSING"


def test_analyze_benchmark_records_design_and_noninferiority():
    methods = ["ASF", "MMR", "LexPR"]
    rows = []
    for replication in range(4):
        for method, loss in zip(methods, [0.20, 0.21, 0.205]):
            rows.append({
                "run_id": "run-a",
                "N": 10,
                "m": 3,
                "geometry": "linear",
                "replication": replication,
                "method": method,
                "mean_loss": loss - 0.05,
                "tail_loss": loss,
            })
    cfg = {
        "methods": methods,
        "seed": 7,
        "noninferiority": {
            "metric": "tail_loss",
            "margin_absolute": 0.01,
            "confidence": 0.95,
            "controls": ["ASF", "MMR"],
            "bootstrap_unit": ["N", "m", "geometry", "replication"],
            "bootstrap_repetitions": 100,
        },
    }

    result = analyze_benchmark(pd.DataFrame(rows), cfg)

    assert result["run_id"] == "run-a"
    assert result["n_instances"] == 4
    assert result["n_methods"] == 3
    assert set(result["noninferiority"]) == {"ASF", "MMR"}


def test_finalize_does_not_treat_worst_family_scope_as_paired_factor(tmp_path):
    cfg = {
        "candidate_sizes": [10],
        "criteria": [3],
        "geometries": ["linear"],
        "replications": 2,
        "methods": ["ASF", "MMR", "LexPR"],
        "family_scopes": {"linear": "in_class", "choquet": "out_of_class"},
        "seed": 7,
        "noninferiority": {
            "metric": "tail_loss",
            "margin_absolute": 0.01,
            "confidence": 0.95,
            "controls": ["ASF", "MMR"],
            "bootstrap_unit": ["N", "m", "geometry", "replication"],
            "bootstrap_repetitions": 20,
        },
    }
    rows = []
    for replication in range(2):
        for method, family, scope, loss in (
            ("ASF", "linear", "in_class", 0.20),
            ("MMR", "choquet", "out_of_class", 0.21),
            ("LexPR", "linear", "in_class", 0.205),
        ):
            rows.append({
                "run_id": "run-a", "config_sha256": "cfg-a", "seed": 1,
                "N": 10, "m": 3, "geometry": "linear",
                "replication": replication, "dirichlet_alpha": 1.0,
                "method": method, "utility_scope": scope,
                "mean_loss": loss - 0.05, "tail_loss": loss,
                "worst_family": family, "worst_family_loss": loss,
                "selected_index": 0,
            })
    paths = configure_output_root(tmp_path, "run-a")
    paths["root"].mkdir(parents=True)
    (paths["root"] / "run_manifest.json").write_text(
        '{"run_id": "run-a"}', encoding="utf-8"
    )

    _benchmark_finalize_from_records(cfg, pd.DataFrame(rows))

    assert (paths["tables"] / "benchmark_analysis.json").exists()
    assert not (paths["tables"] / "benchmark_by_utility_scope.csv").exists()
