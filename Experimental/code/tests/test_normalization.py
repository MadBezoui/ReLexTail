import numpy as np
import pytest
from lexpr.normalization import generate_bounds, lexpr_stable


def test_stable_result_returns_single_recommendation():
    F = np.array([[0.0, 1.0], [0.5, 0.5], [1.0, 0.0]])
    bounds = [(F.min(0), F.max(0))] * 10
    result = lexpr_stable(F, bounds, min_identity_rate=0.9, max_set_size=2)
    assert result.status == "recommend"
    assert len(result.indices) == 1


def test_unstable_result_does_not_claim_unique_recommendation():
    F = np.array([
        [0.0, 10.0, 10.0],
        [10.0, 0.0, 10.0],
        [10.0, 10.0, 0.0],
    ])
    bounds = [
        (np.zeros(3), np.array([1.0, 10.0, 10.0])),
        (np.zeros(3), np.array([10.0, 1.0, 10.0])),
        (np.zeros(3), np.array([10.0, 10.0, 1.0])),
    ]
    result = lexpr_stable(F, bounds, min_identity_rate=0.9, max_set_size=1)
    assert result.status in {"set", "abstain"}


@pytest.mark.parametrize("mode", ["minmax", "asymmetric_error", "correlated_error"])
def test_outward_bounds_enclose_negative_objective_values(mode):
    F = np.array([[-5.0, -2.0], [-3.0, 4.0], [1.0, 2.0]])
    bounds = generate_bounds(F, 10, mode, np.random.default_rng(7))
    for ideal, nadir in bounds:
        assert np.all(ideal <= F.min(axis=0))
        assert np.all(nadir >= F.max(axis=0))
