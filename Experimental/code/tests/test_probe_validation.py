import numpy as np
from lexpr.probe_validation import compare_probe_families


def test_two_criterion_complete_adaptive_family_has_zero_regret_gap():
    F = np.array([[0.0, 1.0], [0.4, 0.4], [1.0, 0.0]])
    result = compare_probe_families(F, tolerance=1e-9, theta=0.6)
    assert result["worst_regret_gap"] <= 1e-9
    assert 0.0 <= result["tolerance_jaccard"] <= 1.0
