"""Tests for lexpr.metrics — evaluation metrics and held-out loss computation.

Covers: sample_test_utilities, precompute_utilities, loss_from_cache,
out_of_class_loss, is_dominated, tail_loss, worst_case_regret.
"""
import numpy as np
import pytest
import numpy.testing as npt

from lexpr.metrics import (
    sample_test_utilities, precompute_utilities, loss_from_cache,
    out_of_class_loss, is_dominated, tail_loss, worst_case_regret,
)


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture
def rng():
    return np.random.default_rng(42)


@pytest.fixture
def front():
    """A 10x3 candidate set for metric tests."""
    from lexpr.problems import make_candidate_set
    return make_candidate_set("concave", 10, 3, np.random.default_rng(42))


@pytest.fixture
def cache(front, rng):
    """Pre-computed utility cache."""
    return precompute_utilities(front, rng, n_per_family=50)


# --------------------------------------------------------------------------- #
# sample_test_utilities
# --------------------------------------------------------------------------- #
class TestSampleTestUtilities:
    """Tests for sample_test_utilities()."""

    def test_returns_six_families(self, rng):
        """Should return exactly 6 utility families."""
        fams = sample_test_utilities(3, 50, rng)
        assert len(fams) == 6
        expected = {"linear", "chebyshev", "aug_asf", "ces", "choquet", "satisfice"}
        assert set(fams.keys()) == expected

    def test_utility_shapes(self, rng):
        """Each family should produce an (N x T) matrix."""
        fams = sample_test_utilities(3, 50, rng)
        r = np.random.default_rng(0).random((10, 3))  # dummy normalised input
        for name, fn in fams.items():
            U = fn(r)
            assert U.shape == (10, 50), f"Family {name} shape mismatch"

    def test_utilities_are_finite(self, rng):
        """All utilities should be finite (no NaN/Inf)."""
        fams = sample_test_utilities(3, 20, rng)
        r = rng.random((5, 3))
        for name, fn in fams.items():
            U = fn(r)
            assert np.all(np.isfinite(U)), f"Family {name} has non-finite values"

    def test_higher_is_better(self, rng):
        """Utilities encode higher-is-better: the ideal point (r=0) should
        generally score higher than a worse point."""
        fams = sample_test_utilities(3, 100, rng)
        r = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]])  # ideal vs nadir
        for name, fn in fams.items():
            U = fn(r)
            # ideal (row 0) should have higher utility than nadir (row 1) on average
            assert U[0].mean() >= U[1].mean(), f"Family {name}: ideal not preferred"


# --------------------------------------------------------------------------- #
# precompute_utilities
# --------------------------------------------------------------------------- #
class TestPrecomputeUtilities:
    """Tests for precompute_utilities()."""

    def test_cache_structure(self, cache):
        """Cache should contain per-family entries plus _all_loss and _families."""
        assert "_all_loss" in cache
        assert "_families" in cache
        assert len(cache["_families"]) == 6
        for name in cache["_families"]:
            assert name in cache
            U, best, worst = cache[name]
            assert U.ndim == 2

    def test_all_loss_shape(self, cache, front):
        """_all_loss should have shape (N, 6*T)."""
        L = cache["_all_loss"]
        assert L.shape[0] == front.shape[0]
        assert L.ndim == 2

    def test_all_loss_non_negative(self, cache):
        """Loss values should be non-negative."""
        L = cache["_all_loss"]
        assert L.min() >= -1e-6


# --------------------------------------------------------------------------- #
# loss_from_cache
# --------------------------------------------------------------------------- #
class TestLossFromCache:
    """Tests for loss_from_cache()."""

    def test_non_negative_losses(self, cache, front):
        """Mean and tail loss should be non-negative for any candidate."""
        for idx in range(front.shape[0]):
            mean_loss, tail_loss_ = loss_from_cache(cache, idx)
            assert mean_loss >= -1e-6
            assert tail_loss_ >= -1e-6

    def test_by_family_returns_dict(self, cache):
        """by_family=True should return a 3-tuple with per-family dict."""
        mean_loss, tail_loss_, per = loss_from_cache(cache, 0, by_family=True)
        assert isinstance(per, dict)
        assert len(per) == 6

    def test_best_candidate_low_loss(self, cache, front):
        """At least one candidate should have mean_loss < 0.5."""
        losses = [loss_from_cache(cache, i)[0] for i in range(front.shape[0])]
        assert min(losses) < 0.5


# --------------------------------------------------------------------------- #
# out_of_class_loss
# --------------------------------------------------------------------------- #
class TestOutOfClassLoss:
    """Tests for out_of_class_loss()."""

    def test_returns_non_negative(self, front, rng):
        """Overall loss should be non-negative."""
        loss = out_of_class_loss(front, 0, rng, n_per_family=30)
        assert loss >= -1e-6

    def test_by_family(self, front, rng):
        """by_family=True should return (float, dict)."""
        overall, per = out_of_class_loss(front, 0, rng, n_per_family=30,
                                          by_family=True)
        assert isinstance(per, dict)
        assert len(per) == 6
        for v in per.values():
            assert v >= -1e-6

    def test_ideal_candidate_low_loss(self, rng):
        """A candidate at the ideal point should have very low loss."""
        F = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [0.5, 0.5]])
        loss = out_of_class_loss(F, 0, rng, n_per_family=50)
        assert loss < 0.3  # ideal point should be favoured


# --------------------------------------------------------------------------- #
# is_dominated
# --------------------------------------------------------------------------- #
class TestIsDominated:
    """Tests for is_dominated()."""

    def test_dominated_point(self):
        """A point dominated by another should return True."""
        F = np.array([
            [1.0, 1.0],
            [2.0, 2.0],   # dominated by [1, 1]
        ])
        assert is_dominated(F, 1) is True

    def test_non_dominated_point(self):
        """A Pareto-optimal point should return False."""
        F = np.array([
            [0.0, 1.0],
            [1.0, 0.0],
        ])
        assert is_dominated(F, 0) is False
        assert is_dominated(F, 1) is False

    def test_identical_points_not_dominated(self):
        """Identical points do not dominate each other (need strict <)."""
        F = np.array([[1.0, 1.0], [1.0, 1.0]])
        assert is_dominated(F, 0) is False

    def test_weakly_dominated(self):
        """Weakly dominated (equal in one, worse in another) should be dominated."""
        F = np.array([
            [1.0, 2.0],
            [1.0, 3.0],   # same in f1, worse in f2 → dominated
        ])
        assert is_dominated(F, 1) is True


# --------------------------------------------------------------------------- #
# tail_loss and worst_case_regret
# --------------------------------------------------------------------------- #
class TestTailLoss:
    """Tests for tail_loss()."""

    def test_non_negative(self, front, rng):
        """Tail loss should be non-negative."""
        tl = tail_loss(front, 0, rng, n_per_family=30)
        assert tl >= -1e-6

    def test_tail_ge_mean(self, front, rng):
        """Tail loss (upper quantile) should be >= mean loss."""
        from lexpr.metrics import out_of_class_loss as ocl
        rng1 = np.random.default_rng(99)
        rng2 = np.random.default_rng(99)
        mean_loss = ocl(front, 0, rng1, n_per_family=50)
        tl = tail_loss(front, 0, rng2, n_per_family=50)
        # Tail should usually be >= mean, but with sampling noise allow small slack
        assert tl >= mean_loss - 0.15


class TestWorstCaseRegret:
    """Tests for worst_case_regret()."""

    def test_non_negative(self, front):
        """Worst-case regret should be non-negative."""
        wcr = worst_case_regret(front, 0)
        assert wcr >= -1e-6

    def test_at_most_one(self, front):
        """Worst-case regret (normalised) should be at most 1."""
        for idx in range(front.shape[0]):
            wcr = worst_case_regret(front, idx)
            assert wcr <= 1.0 + 1e-6
