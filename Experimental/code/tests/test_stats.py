import warnings

import numpy as np

from lexpr.stats import holm_adjust, wilcoxon_holm


def test_holm_adjust_is_monotone_in_sorted_order():
    raw = np.array([0.01, 0.04, 0.03])
    adjusted = holm_adjust(raw)
    assert np.allclose(adjusted, [0.03, 0.06, 0.06])


def test_holm_adjust_caps_at_one():
    assert np.all(holm_adjust(np.array([0.6, 0.8])) <= 1.0)


def test_small_paired_wilcoxon_does_not_leak_scipy_warning():
    losses = np.array([
        [0.1, 0.1, 0.1],
        [0.2, 0.3, 0.2],
        [0.3, 0.4, 0.3],
        [0.4, 0.5, 0.4],
        [0.5, 0.5, 0.5],
        [0.6, 0.7, 0.6],
        [0.7, 0.8, 0.7],
        [0.8, 0.9, 0.8],
    ])
    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        result = wilcoxon_holm(losses, ["LexPR", "A", "B"], "LexPR")
    assert set(result) == {"A", "B"}
