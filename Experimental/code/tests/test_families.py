"""Tests for lexpr.families — extended utility families for held-out evaluation.

Covers: build_families (all 10 families), loss_cache, losses_from.
"""
import numpy as np
import pytest
import numpy.testing as npt

from lexpr.families import build_families, loss_cache, losses_from, ALL_FAMILIES
from lexpr.methods import normalize


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture
def rng():
    return np.random.default_rng(42)


@pytest.fixture
def normalised_front(rng):
    """A 15x3 normalised front in [0, 1]."""
    from lexpr.problems import make_candidate_set
    F = make_candidate_set("concave", 15, 3, rng)
    return normalize(F)


@pytest.fixture
def raw_front(rng):
    """A 15x3 raw (un-normalised) front."""
    from lexpr.problems import make_candidate_set
    return make_candidate_set("concave", 15, 3, rng)


# --------------------------------------------------------------------------- #
# build_families — individual family tests
# --------------------------------------------------------------------------- #
class TestBuildFamilies:
    """Tests for build_families() and each utility family."""

    def test_returns_all_families(self, rng):
        """Should return all 10 families by default."""
        fams = build_families(3, 20, rng)
        assert len(fams) == 10
        assert set(fams.keys()) == set(ALL_FAMILIES)

    def test_subset_selection(self, rng):
        """Should return only requested families."""
        fams = build_families(3, 20, rng, family_list=["linear", "ces"])
        assert set(fams.keys()) == {"linear", "ces"}

    @pytest.mark.parametrize("family_name", ALL_FAMILIES)
    def test_family_output_shape(self, family_name, rng, normalised_front):
        """Each family should return (N x T) for N candidates and T parameterisations."""
        N = normalised_front.shape[0]
        T = 25
        m = normalised_front.shape[1]
        fams = build_families(m, T, rng, family_list=[family_name])
        fn = fams[family_name]
        U = fn(normalised_front)
        assert U.shape == (N, T), f"{family_name}: expected ({N}, {T}), got {U.shape}"

    @pytest.mark.parametrize("family_name", ALL_FAMILIES)
    def test_family_output_finite(self, family_name, rng, normalised_front):
        """Each family's output should be finite (no NaN/Inf)."""
        m = normalised_front.shape[1]
        fams = build_families(m, 20, rng, family_list=[family_name])
        U = fams[family_name](normalised_front)
        assert np.all(np.isfinite(U)), f"{family_name} produced non-finite values"

    @pytest.mark.parametrize("family_name", ALL_FAMILIES)
    def test_family_higher_is_better(self, family_name, rng):
        """Utilities should prefer the ideal point (r=0) over nadir (r=1)."""
        m = 3
        r = np.array([[0.0]*m, [1.0]*m])  # ideal vs nadir
        fams = build_families(m, 50, rng, family_list=[family_name])
        U = fams[family_name](r)
        # Ideal should have higher utility on average
        assert U[0].mean() >= U[1].mean(), \
            f"{family_name}: ideal not preferred over nadir"

    def test_alpha_affects_weights(self, rng):
        """Different alpha should change the weight distribution shape."""
        fams_sparse = build_families(3, 50, np.random.default_rng(42),
                                     alpha=0.2, family_list=["linear"])
        fams_balanced = build_families(3, 50, np.random.default_rng(42),
                                       alpha=5.0, family_list=["linear"])
        r = rng.random((10, 3))
        U_sparse = fams_sparse["linear"](r)
        U_balanced = fams_balanced["linear"](r)
        # They should produce different results
        assert not np.allclose(U_sparse, U_balanced)

    def test_bi_objective(self, rng):
        """Should work with m=2."""
        fams = build_families(2, 20, rng)
        r = rng.random((10, 2))
        for name, fn in fams.items():
            U = fn(r)
            assert U.shape == (10, 20), f"{name} failed for m=2"

    def test_many_objective(self, rng):
        """Should work with m=6."""
        fams = build_families(6, 20, rng)
        r = rng.random((10, 6))
        for name, fn in fams.items():
            U = fn(r)
            assert U.shape == (10, 20), f"{name} failed for m=6"


# --------------------------------------------------------------------------- #
# loss_cache
# --------------------------------------------------------------------------- #
class TestLossCache:
    """Tests for loss_cache()."""

    def test_cache_structure(self, raw_front, rng):
        """Cache should contain per-family entries, _families, and _pooled."""
        cache = loss_cache(raw_front, normalize, rng, n_per_family=30)
        assert "_families" in cache
        assert "_pooled" in cache
        assert len(cache["_families"]) == 10
        for name in cache["_families"]:
            assert name in cache

    def test_pooled_shape(self, raw_front, rng):
        """_pooled should have shape (N, 10*T)."""
        T = 30
        cache = loss_cache(raw_front, normalize, rng, n_per_family=T)
        L = cache["_pooled"]
        assert L.shape[0] == raw_front.shape[0]
        assert L.shape[1] == 10 * T

    def test_pooled_non_negative(self, raw_front, rng):
        """Pooled losses should be non-negative."""
        cache = loss_cache(raw_front, normalize, rng, n_per_family=30)
        assert cache["_pooled"].min() >= -1e-6


# --------------------------------------------------------------------------- #
# losses_from
# --------------------------------------------------------------------------- #
class TestLossesFrom:
    """Tests for losses_from()."""

    def test_returns_four_values(self, raw_front, rng):
        """Should return (mean, tail, worst_family, per_dict)."""
        cache = loss_cache(raw_front, normalize, rng, n_per_family=30)
        result = losses_from(cache, 0)
        assert len(result) == 4
        mean_loss, tail_loss, worst_family, per = result
        assert isinstance(per, dict)

    def test_losses_non_negative(self, raw_front, rng):
        """All loss components should be non-negative."""
        cache = loss_cache(raw_front, normalize, rng, n_per_family=30)
        for idx in range(min(5, raw_front.shape[0])):
            mean_l, tail_l, worst_l, per = losses_from(cache, idx)
            assert mean_l >= -1e-6
            assert tail_l >= -1e-6
            assert worst_l >= -1e-6

    def test_worst_ge_mean(self, raw_front, rng):
        """Worst-family loss should be >= mean-family loss."""
        cache = loss_cache(raw_front, normalize, rng, n_per_family=30)
        for idx in range(min(5, raw_front.shape[0])):
            mean_l, _, worst_l, _ = losses_from(cache, idx)
            assert worst_l >= mean_l - 1e-6
