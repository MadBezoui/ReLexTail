"""Tests for lexpr.methods — selection methods and LexPR core algorithm.

Covers: normalize, correlation_clusters, build_probes, disappointment_matrix,
leximax_argmin, lexpr, lexpr_variant, and all 12 METHODS registry entries.
"""
import warnings

import numpy as np
import pytest
import numpy.testing as npt

from lexpr.methods import (
    normalize, correlation_clusters, build_probes, disappointment_matrix,
    leximax_argmin, lexpr, lexpr_variant, EPS,
    topsis, compromise_programming, knee_point, random_weights, asf,
    smaa, minimax_regret, chebyshev_mmr, hypervolume_pick, dist_to_ideal,
    vikor, METHODS,
)


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture
def rng():
    return np.random.default_rng(42)


@pytest.fixture
def simple_front():
    """A small 5x3 non-dominated front for quick tests."""
    return np.array([
        [0.0, 1.0, 0.5],
        [1.0, 0.0, 0.5],
        [0.5, 0.5, 0.0],
        [0.3, 0.3, 0.6],
        [0.7, 0.2, 0.3],
    ])


@pytest.fixture
def dominated_front():
    """Front with one clearly dominated point (index 3)."""
    return np.array([
        [0.0, 1.0],
        [1.0, 0.0],
        [0.5, 0.5],
        [0.8, 0.9],   # dominated by [0.5, 0.5]
    ])


# --------------------------------------------------------------------------- #
# normalize
# --------------------------------------------------------------------------- #
class TestNormalize:
    """Tests for the normalize() function."""

    def test_output_in_unit_interval(self, simple_front):
        """Normalised values should lie in [0, 1]."""
        r = normalize(simple_front)
        assert r.min() >= -1e-12
        assert r.max() <= 1.0 + 1e-12

    def test_ideal_maps_to_zero(self, simple_front):
        """The column-wise minimum should map to 0."""
        r = normalize(simple_front)
        npt.assert_allclose(r.min(axis=0), 0.0, atol=1e-12)

    def test_nadir_maps_to_one(self, simple_front):
        """The column-wise maximum should map to 1."""
        r = normalize(simple_front)
        npt.assert_allclose(r.max(axis=0), 1.0, atol=1e-12)

    def test_custom_ideal_nadir(self):
        """Custom ideal/nadir should shift and scale accordingly."""
        F = np.array([[2.0, 4.0], [4.0, 6.0]])
        ideal = np.array([0.0, 0.0])
        nadir = np.array([10.0, 10.0])
        r = normalize(F, ideal=ideal, nadir=nadir)
        npt.assert_allclose(r, [[0.2, 0.4], [0.4, 0.6]])

    def test_identical_columns_eps_handling(self):
        """When a column is constant the denominator should use EPS, not zero."""
        F = np.array([[3.0, 1.0], [3.0, 2.0]])
        r = normalize(F)
        # First column constant → (F-ideal)/EPS, should not be NaN/Inf
        assert np.all(np.isfinite(r))

    def test_single_row(self):
        """A single candidate should normalise to all zeros (ideal == nadir)."""
        F = np.array([[5.0, 3.0]])
        r = normalize(F)
        assert np.all(np.isfinite(r))

    def test_shape_preserved(self, simple_front):
        """Output shape should match input shape."""
        r = normalize(simple_front)
        assert r.shape == simple_front.shape


# --------------------------------------------------------------------------- #
# correlation_clusters
# --------------------------------------------------------------------------- #
class TestCorrelationClusters:
    """Tests for correlation_clusters()."""

    def test_perfectly_correlated_grouped(self):
        """Two perfectly correlated columns should be in the same cluster."""
        rng = np.random.default_rng(42)
        base = rng.random((50, 1))
        F = np.column_stack([base, base * 2 + 1, rng.random((50, 1))])
        clusters = correlation_clusters(F, theta=0.6)
        # objectives 0 and 1 are perfectly correlated
        cluster_of_0 = [c for c in clusters if 0 in c][0]
        assert 1 in cluster_of_0

    def test_uncorrelated_separate(self):
        """Independent columns should end up in different clusters."""
        rng = np.random.default_rng(42)
        F = rng.random((100, 3))
        clusters = correlation_clusters(F, theta=0.9)
        # With high threshold and independent columns, each should be separate
        assert len(clusters) == 3

    def test_all_objectives_covered(self, simple_front):
        """Every objective index should appear in exactly one cluster."""
        clusters = correlation_clusters(simple_front)
        all_indices = sorted(idx for c in clusters for idx in c)
        assert all_indices == list(range(simple_front.shape[1]))

    def test_two_objectives(self):
        """Bi-objective case: either 1 or 2 clusters."""
        F = np.array([[0.0, 1.0], [1.0, 0.0], [0.5, 0.5]])
        clusters = correlation_clusters(F)
        assert 1 <= len(clusters) <= 2

    def test_constant_column_nan_safe(self):
        """Constant columns are separated without relying on NaN correlations."""
        F = np.array([[1.0, 0.0], [1.0, 1.0], [1.0, 0.5]])
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            clusters = correlation_clusters(F)
        all_indices = sorted(idx for c in clusters for idx in c)
        assert all_indices == [0, 1]

    def test_single_candidate_has_singleton_clusters_without_warning(self):
        F = np.array([[1.0, 2.0, 3.0]])
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            clusters = correlation_clusters(F)
        assert clusters == [[0], [1], [2]]


# --------------------------------------------------------------------------- #
# build_probes
# --------------------------------------------------------------------------- #
class TestBuildProbes:
    """Tests for build_probes()."""

    def test_probe_count_lower_bound(self, simple_front):
        """Should have at least m singletons + 2 anchor probes for m > 1."""
        m = simple_front.shape[1]
        probes, labels = build_probes(simple_front)
        assert len(probes) >= m + 2   # singletons + mean(all) + max(all)
        assert len(probes) == len(labels)

    def test_probes_are_monotone(self, simple_front):
        """Each probe should be monotone non-decreasing: increasing any r_i
        should not decrease the probe value."""
        r = normalize(simple_front)
        probes, _ = build_probes(simple_front)
        for q in probes:
            v = q(r)
            # Adding a positive perturbation to r should not decrease probe
            r_plus = r + 0.01
            v_plus = q(r_plus)
            assert np.all(v_plus >= v - 1e-10)

    def test_singleton_only_mode(self, simple_front):
        """With only singletons enabled, probe count should equal m."""
        m = simple_front.shape[1]
        probes, labels = build_probes(
            simple_front, use_mean=False, use_max=False, use_clusters=False
        )
        assert len(probes) == m

    def test_bi_objective_probes(self):
        """Bi-objective case should still produce singletons + anchors."""
        F = np.array([[0.0, 1.0], [1.0, 0.0], [0.5, 0.5]])
        probes, labels = build_probes(F)
        assert len(probes) >= 4  # 2 singletons + mean + max


# --------------------------------------------------------------------------- #
# disappointment_matrix
# --------------------------------------------------------------------------- #
class TestDisappointmentMatrix:
    """Tests for disappointment_matrix()."""

    def test_shape(self, simple_front):
        """D should be (N x K) where K is the number of probes."""
        probes, _ = build_probes(simple_front)
        D = disappointment_matrix(simple_front, probes)
        assert D.shape == (simple_front.shape[0], len(probes))

    def test_values_in_unit_interval(self, simple_front):
        """Disappointment values should be in [0, 1]."""
        probes, _ = build_probes(simple_front)
        D = disappointment_matrix(simple_front, probes)
        assert D.min() >= -1e-10
        assert D.max() <= 1.0 + 1e-10

    def test_best_candidate_has_zero(self, simple_front):
        """For each probe, the best candidate should have 0 disappointment."""
        probes, _ = build_probes(simple_front)
        D = disappointment_matrix(simple_front, probes)
        npt.assert_allclose(D.min(axis=0), 0.0, atol=1e-8)

    def test_with_custom_ideal_nadir(self, simple_front):
        """Custom ideal/nadir should not crash and should still produce valid D."""
        probes, _ = build_probes(simple_front)
        ideal = np.zeros(3)
        nadir = np.ones(3) * 2.0
        D = disappointment_matrix(simple_front, probes, ideal=ideal, nadir=nadir)
        assert D.shape[0] == simple_front.shape[0]
        assert np.all(np.isfinite(D))


# --------------------------------------------------------------------------- #
# leximax_argmin
# --------------------------------------------------------------------------- #
class TestLeximaxArgmin:
    """Tests for leximax_argmin()."""

    def test_returns_minimax(self):
        """Should pick the row whose worst column is smallest."""
        D = np.array([
            [0.8, 0.2],   # max = 0.8
            [0.5, 0.5],   # max = 0.5  ← best minimax
            [0.9, 0.1],   # max = 0.9
        ])
        assert leximax_argmin(D) == 1

    def test_tiebreaker_second_worst(self):
        """When worst columns tie, should break by second-worst."""
        D = np.array([
            [0.6, 0.4, 0.1],   # sorted desc: [0.6, 0.4, 0.1]
            [0.6, 0.3, 0.2],   # sorted desc: [0.6, 0.3, 0.2]
        ])
        # Both have max = 0.6; row 1 has second-worst 0.3 < 0.4
        assert leximax_argmin(D) == 1

    def test_single_row(self):
        """Single candidate should return index 0."""
        D = np.array([[0.5, 0.3]])
        assert leximax_argmin(D) == 0

    def test_single_column(self):
        """Single probe: should return argmin."""
        D = np.array([[0.7], [0.3], [0.5]])
        assert leximax_argmin(D) == 1

    def test_identical_rows(self):
        """Identical rows: should return a valid index (first by convention)."""
        D = np.array([[0.5, 0.3], [0.5, 0.3]])
        idx = leximax_argmin(D)
        assert idx in (0, 1)


# --------------------------------------------------------------------------- #
# lexpr
# --------------------------------------------------------------------------- #
class TestLexPR:
    """Tests for the main lexpr() selection function."""

    def test_returns_valid_index(self, simple_front):
        """LexPR should return an integer index in [0, N)."""
        idx = lexpr(simple_front)
        assert isinstance(idx, int)
        assert 0 <= idx < simple_front.shape[0]

    def test_deterministic(self, simple_front):
        """Same input should always give same output."""
        assert lexpr(simple_front) == lexpr(simple_front)

    def test_never_picks_dominated(self, dominated_front):
        """LexPR should never select a dominated candidate (Pareto compatibility)."""
        idx = lexpr(dominated_front)
        # Index 3 is dominated by index 2
        assert idx != 3

    def test_return_detail(self, simple_front):
        """return_detail=True should give (idx, D, labels, probes)."""
        result = lexpr(simple_front, return_detail=True)
        assert len(result) == 4
        idx, D, labels, probes = result
        assert isinstance(idx, int)
        assert D.shape[0] == simple_front.shape[0]
        assert len(labels) == len(probes)

    def test_single_candidate(self):
        """A single candidate should return index 0."""
        F = np.array([[1.0, 2.0, 3.0]])
        assert lexpr(F) == 0

    def test_bi_objective(self):
        """Should work correctly on a 2-objective problem."""
        F = np.array([[0.0, 1.0], [1.0, 0.0], [0.5, 0.5]])
        idx = lexpr(F)
        assert 0 <= idx < 3

    def test_custom_ideal_nadir(self, simple_front):
        """Custom ideal/nadir should not crash."""
        ideal = np.zeros(3)
        nadir = np.ones(3) * 2.0
        idx = lexpr(simple_front, ideal=ideal, nadir=nadir)
        assert 0 <= idx < simple_front.shape[0]


# --------------------------------------------------------------------------- #
# lexpr_variant
# --------------------------------------------------------------------------- #
class TestLexPRVariant:
    """Tests for lexpr_variant() with different probe strategies."""

    @pytest.mark.parametrize("variant", [
        "adaptive", "full", "singletons", "no_singletons",
        "max_only", "cluster_only", "random",
    ])
    def test_all_variants_return_valid_index(self, simple_front, variant, rng):
        """Each variant should return a valid candidate index."""
        idx = lexpr_variant(simple_front, variant=variant, rng=rng)
        assert 0 <= idx < simple_front.shape[0]

    def test_invalid_variant_raises(self, simple_front):
        """Unknown variant name should raise ValueError."""
        with pytest.raises(ValueError):
            lexpr_variant(simple_front, variant="nonexistent")

    def test_variant_with_custom_ideal_nadir(self, simple_front, rng):
        """Custom ideal/nadir should work in variant mode."""
        ideal = np.zeros(3)
        nadir = np.ones(3) * 2.0
        idx = lexpr_variant(simple_front, variant="adaptive", rng=rng,
                          ideal=ideal, nadir=nadir)
        assert 0 <= idx < simple_front.shape[0]

    def test_return_detail(self, simple_front, rng):
        """return_detail should give 4-tuple for variants."""
        result = lexpr_variant(simple_front, variant="full", rng=rng,
                             return_detail=True)
        assert len(result) == 4


# --------------------------------------------------------------------------- #
# All 12 selection methods in the METHODS registry
# --------------------------------------------------------------------------- #
class TestAllMethods:
    """Each of the 12 selection methods should return a valid index."""

    @pytest.fixture
    def front_for_methods(self, rng):
        """A 20x3 front with enough spread for all methods."""
        from lexpr.problems import make_candidate_set
        return make_candidate_set("concave", 20, 3, rng)

    @pytest.mark.parametrize("name", list(METHODS.keys()))
    def test_method_returns_valid_index(self, front_for_methods, name):
        """Method '{name}' should return an int in [0, N)."""
        F = front_for_methods
        method = METHODS[name]
        rng = np.random.default_rng(42)
        idx = method(F, rng=rng)
        assert isinstance(idx, (int, np.integer))
        assert 0 <= idx < F.shape[0]

    @pytest.mark.parametrize("name", list(METHODS.keys()))
    def test_method_on_bi_objective(self, name):
        """Method '{name}' should work on a minimal 2-objective front."""
        F = np.array([[0.0, 1.0], [1.0, 0.0], [0.4, 0.4]])
        method = METHODS[name]
        rng = np.random.default_rng(42)
        idx = method(F, rng=rng)
        assert 0 <= idx < 3

    @pytest.mark.parametrize("name", list(METHODS.keys()))
    def test_method_on_single_candidate(self, name):
        """With a single candidate, every method should return 0."""
        F = np.array([[1.0, 2.0]])
        method = METHODS[name]
        rng = np.random.default_rng(42)
        idx = method(F, rng=rng)
        assert idx == 0
