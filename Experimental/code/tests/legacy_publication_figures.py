from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

from lexpr.publication_figures import (
    paired_bootstrap_ci,
    publication_style,
    significance_groups,
    wilson_interval,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_mechanistic_cd_only_groups_lexpr_with_cp():
    ranks = {"MMR": 2.8521, "ASF": 2.9385, "CP": 3.4208, "LexPR": 3.4406}

    groups = [set(group) for group in significance_groups(ranks, 0.479243)]
    lexpr_groups = [group for group in groups if "LexPR" in group]

    assert {"CP", "LexPR"} in lexpr_groups
    assert not any({"MMR", "LexPR"} <= group for group in lexpr_groups)
    assert not any({"ASF", "LexPR"} <= group for group in lexpr_groups)


def test_publication_style_uses_truetype_fonts():
    with publication_style():
        assert matplotlib.rcParams["pdf.fonttype"] == 42
        assert matplotlib.rcParams["ps.fonttype"] == 42


def test_paired_bootstrap_interval_is_deterministic():
    values = np.array([0.1, 0.2, 0.3, 0.4])

    first = paired_bootstrap_ci(values, n_resamples=500, seed=17)
    second = paired_bootstrap_ci(values, n_resamples=500, seed=17)

    assert first == second
    assert first[0] <= values.mean() <= first[1]


def test_wilson_interval_contains_observed_rate():
    lower, upper = wilson_interval(successes=40, trials=100)

    assert lower < 0.4 < upper


def test_wilson_interval_respects_probability_bounds_at_zero():
    lower, upper = wilson_interval(successes=0, trials=3)

    assert lower == 0.0
    assert lower <= upper <= 1.0


class TestFigureContracts:
    tables = REPO_ROOT / "results" / "tables"

    def test_figure_6_reports_cluster_count(self):
        frame = pd.read_csv(self.tables / "probe_reduction.csv")
        expected = frame["m"] + 2 + 2 * frame["nontrivial_clusters"]
        assert frame["cluster_probes"].equals(expected)

    def test_figure_12_contains_all_registered_ablations(self):
        frame = pd.read_csv(self.tables / "ablation_concave_m8.csv")
        assert len(frame) == 5
        assert {"loss_lower", "loss_upper", "wcr_lower", "wcr_upper"} <= set(frame)

    def test_figure_13_distance_is_normalized(self):
        frame = pd.read_csv(self.tables / "agreement_smaa.csv")
        assert frame["mean_rms_distance"].between(0, 1).all()
        assert frame["tolerance_jaccard"].between(0, 1).all()

    def test_figure_14_is_paired_across_error_levels(self):
        frame = pd.read_csv(self.tables / "sensitivity_nadir_observations.csv")
        levels = frame["error_level"].nunique()
        assert frame.groupby("problem_id")["error_level"].nunique().eq(levels).all()

    def test_figure_15_reports_intervals(self):
        frame = pd.read_csv(self.tables / "stochastic_consistency.csv")
        assert {"exact_lower", "exact_upper", "tolerance_lower", "tolerance_upper"} <= set(frame)
