import numpy as np
import pytest

from lexpr.experiments import (
    ablation_table,
    confidence_adjusted_objectives,
    probe_reduction_table,
    rms_choice_distance,
    run_redundancy,
    sensitivity_nadir,
    stochastic_demo,
)


def test_rms_choice_distance_is_dimension_invariant():
    assert rms_choice_distance(np.zeros(3), np.full(3, 0.5)) == pytest.approx(0.5)
    assert rms_choice_distance(np.zeros(12), np.full(12, 0.5)) == pytest.approx(0.5)


def test_confidence_adjustment_uses_standard_error():
    mu = np.zeros((1, 2))
    sd = np.ones((1, 2))

    adjusted = confidence_adjusted_objectives(mu, sd, n_obs=100, z=1.6449)

    assert adjusted[0, 0] == pytest.approx(0.16449)


def test_nadir_levels_reuse_problem_ids(tmp_path):
    _, observations = sensitivity_nadir(
        reps=3,
        n=25,
        n_test=8,
        error_levels=(0.0, 0.1, 0.2),
        outdir=tmp_path,
        return_observations=True,
    )

    levels_per_problem = observations.groupby("problem_id")["error_level"].nunique()
    assert levels_per_problem.eq(3).all()
    baseline = observations[observations["error_level"] == 0]
    assert baseline["winner_changed"].eq(0).all()


def test_stochastic_demo_reports_exact_and_tolerance_intervals(tmp_path):
    summary = stochastic_demo(
        reps=2,
        resamples=2,
        n=25,
        obs_grid=(2, 5),
        outdir=tmp_path,
    )

    expected = {
        "exact_recovery",
        "exact_lower",
        "exact_upper",
        "tolerance_coverage",
        "tolerance_lower",
        "tolerance_upper",
    }
    assert expected <= set(summary.columns)
    assert summary["trials"].eq(4).all()


def test_probe_reduction_reports_realized_nontrivial_clusters(tmp_path):
    summary = probe_reduction_table(n=30, outdir=tmp_path)

    assert "nontrivial_clusters" in summary
    expected = summary["m"] + 2 + 2 * summary["nontrivial_clusters"]
    assert summary["cluster_probes"].equals(expected)


def test_ablation_reports_all_configs_and_both_intervals(tmp_path):
    summary = ablation_table(reps=2, n=25, n_test=8, outdir=tmp_path)

    assert summary["config"].tolist() == [
        "Full LexPR",
        "No clustering",
        "No singletons",
        "Mean only",
        "Max only",
    ]
    assert {
        "loss_lower",
        "loss_upper",
        "wcr_lower",
        "wcr_upper",
    } <= set(summary.columns)


def test_redundancy_reports_intervals_for_both_metrics(tmp_path):
    summary, _ = run_redundancy(
        reps=2, n=25, n_test=8, outdir=tmp_path
    )

    assert {
        "grouped_lower",
        "grouped_upper",
        "tail_lower",
        "tail_upper",
    } <= set(summary.columns)
