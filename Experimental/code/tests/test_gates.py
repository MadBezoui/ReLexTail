import numpy as np

from lexpr import gates, problems
from lexpr import probe_validation
from run_protocol import _bench_block, configure_output_root, stage_probes


def test_nadir_gate_reuses_problem_identity_across_error_levels(monkeypatch):
    calls = []
    original = problems.make_candidate_set

    def record(*args, **kwargs):
        value = original(*args, **kwargs)
        calls.append(value.copy())
        return value

    monkeypatch.setattr(problems, "make_candidate_set", record)

    result = gates.gate_nadir_error(
        [0.0, 0.1, 0.2], reps=4, n=20, m=3, n_test=10
    )

    assert len(calls) == 4
    assert len(result["records"]) == 12


def test_normalization_gate_has_explicit_evidence_and_thresholds():
    result = gates.gate_normalization_stability(reps=2, n_samples=4, n=20, m=3, seed=42, n_test=10)
    assert result["name"] == "normalization_stability"
    assert "regimes" in result
    assert "minmax" in result["regimes"]
    assert "quality_degradation" in result["regimes"]["minmax"]
    for evidence in result["regimes"].values():
        assert "quality_degradation" in evidence


def _benchmark_config(methods):
    return {
        "geometries": ["linear"],
        "_geoms": None,
        "replications": 2,
        "utilities_per_family": 10,
        "dirichlet_alphas": [1.0],
        "families": ["linear"],
        "methods": methods,
        "tail_q": 0.9,
        "seed": 17,
        "family_scopes": {"linear": "in_class"},
    }


def test_randomized_method_results_do_not_depend_on_method_order():
    methods = ["RW", "SMAA", "MMR", "ChebMMR"]
    manifest = {"run_id": "run-a", "config_sha256": "cfg-a"}

    forward = _bench_block(_benchmark_config(methods), [30], [3], manifest)
    reverse = _bench_block(
        _benchmark_config(list(reversed(methods))), [30], [3], manifest
    )

    key = lambda row: (row["replication"], row["method"])
    forward = {key(row): row for row in forward}
    reverse = {key(row): row for row in reverse}
    assert forward.keys() == reverse.keys()
    for cell in forward:
        assert forward[cell]["worst_family"] == "linear"
        assert forward[cell]["utility_scope"] == "in_class"
        assert forward[cell]["selected_index"] == reverse[cell]["selected_index"]
        assert np.isclose(forward[cell]["mean_loss"], reverse[cell]["mean_loss"])
        assert np.isclose(forward[cell]["tail_loss"], reverse[cell]["tail_loss"])


def test_probe_stage_uses_registered_scale(tmp_path, monkeypatch):
    calls = []

    def fake_compare(F, tolerance, theta):
        calls.append((F.shape, theta))
        return {
            "winner_agreement": 1.0,
            "tolerance_jaccard": 1.0,
            "worst_regret_gap": 0.0,
            "certificate_sup_norm_gap": 0.0,
            "probes_adaptive": 1,
            "probes_full": 1,
            "time_adaptive": 0.0,
            "time_full": 0.0,
        }

    monkeypatch.setattr(probe_validation, "compare_probe_families", fake_compare)
    configure_output_root(tmp_path, "run-a")
    cfg = {
        "seed": 3,
        "geometries": ["linear", "convex"],
        "probe_validation": {
            "replications": 2,
            "candidate_size": 20,
            "criteria": [3],
            "thetas": [0.5, 0.7],
            "max_worst_regret_gap": 0.05,
            "max_certificate_gap": 0.1,
            "min_winner_agreement": 0.8,
        },
    }

    stage_probes(cfg)

    assert len(calls) == 2 * 2 * 1 * 2
    assert {shape for shape, _ in calls} == {(20, 3)}
