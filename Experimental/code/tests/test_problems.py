"""Tests for lexpr.problems — candidate-set generation and Pareto-front geometries.

Covers: sample_front (all 8 geometries), non_dominated, make_candidate_set,
make_redundant_set, and edge cases (m=2, m=1-like, n=1).
"""
import numpy as np
import pytest
import numpy.testing as npt

from lexpr.problems import (
    sample_front, non_dominated, make_candidate_set, make_redundant_set,
)


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture
def rng():
    return np.random.default_rng(42)


ALL_GEOMETRIES = [
    "linear", "concave", "convex", "disconnected",
    "asymmetric", "manyknee", "degenerate", "irregular",
]


# --------------------------------------------------------------------------- #
# sample_front
# --------------------------------------------------------------------------- #
class TestSampleFront:
    """Tests for sample_front() across all supported geometries."""

    @pytest.mark.parametrize("geometry", ALL_GEOMETRIES)
    def test_output_shape(self, geometry, rng):
        """Output should have m columns; rows <= n (non-dominated filtering)."""
        n, m = 50, 3
        F = sample_front(geometry, n, m, rng)
        assert F.ndim == 2
        assert F.shape[1] == m
        assert F.shape[0] >= 1   # at least one point survives

    @pytest.mark.parametrize("geometry", ALL_GEOMETRIES)
    def test_non_negativity(self, geometry, rng):
        """All objective values should be non-negative (after clipping in some geometries)."""
        F = sample_front(geometry, 80, 3, rng)
        assert F.min() >= -1e-6

    @pytest.mark.parametrize("geometry", ALL_GEOMETRIES)
    def test_output_is_non_dominated(self, geometry, rng):
        """The returned set should be non-dominated (idempotent filtering)."""
        F = sample_front(geometry, 60, 3, rng)
        F_nd = non_dominated(F)
        # All rows in F should survive non-dominated filtering
        assert F_nd.shape[0] == F.shape[0]

    @pytest.mark.parametrize("geometry", ALL_GEOMETRIES)
    def test_bi_objective(self, geometry, rng):
        """Should work with m=2."""
        F = sample_front(geometry, 30, 2, rng)
        assert F.shape[1] == 2
        assert F.shape[0] >= 1

    @pytest.mark.parametrize("geometry", ALL_GEOMETRIES)
    def test_many_objective(self, geometry, rng):
        """Should work with m=5."""
        F = sample_front(geometry, 40, 5, rng)
        assert F.shape[1] == 5

    def test_single_point(self, rng):
        """Requesting n=1 should return exactly 1 point."""
        F = sample_front("linear", 1, 3, rng)
        assert F.shape[0] == 1

    def test_unknown_geometry_raises(self, rng):
        """Unknown geometry string should raise ValueError."""
        with pytest.raises(ValueError, match="unknown geometry"):
            sample_front("nonexistent", 10, 3, rng)

    def test_linear_sum_constraint(self, rng):
        """Linear geometry: points should satisfy sum(f_i) ≈ 0.5."""
        F = sample_front("linear", 100, 3, rng)
        sums = F.sum(axis=1)
        npt.assert_allclose(sums, 0.5, atol=1e-10)

    def test_concave_unit_sphere(self, rng):
        """Concave geometry: points on the unit sphere (sum f_i^2 ≈ 1)."""
        # After non_dominated filtering some points may be removed, but
        # the geometry should still roughly satisfy the sphere constraint.
        F = sample_front("concave", 100, 3, rng)
        norms = np.linalg.norm(F, axis=1)
        npt.assert_allclose(norms, 1.0, atol=0.05)

    def test_deterministic(self, rng):
        """Same seed should produce identical results."""
        rng1 = np.random.default_rng(99)
        rng2 = np.random.default_rng(99)
        F1 = sample_front("concave", 30, 3, rng1)
        F2 = sample_front("concave", 30, 3, rng2)
        npt.assert_array_equal(F1, F2)


# --------------------------------------------------------------------------- #
# non_dominated
# --------------------------------------------------------------------------- #
class TestNonDominated:
    """Tests for the non_dominated() filter."""

    def test_removes_dominated(self):
        """Known dominated point should be removed."""
        F = np.array([
            [1.0, 3.0],
            [2.0, 2.0],
            [3.0, 1.0],
            [2.5, 2.5],   # dominated by [2.0, 2.0]
        ])
        nd = non_dominated(F)
        assert nd.shape[0] == 3
        # The dominated point [2.5, 2.5] should not be in the result
        for row in nd:
            assert not (row[0] == 2.5 and row[1] == 2.5)

    def test_keeps_non_dominated(self):
        """All points on the Pareto front should be kept."""
        F = np.array([[0.0, 1.0], [0.5, 0.5], [1.0, 0.0]])
        nd = non_dominated(F)
        assert nd.shape[0] == 3

    def test_single_point(self):
        """A single point is trivially non-dominated."""
        F = np.array([[1.0, 2.0]])
        nd = non_dominated(F)
        assert nd.shape[0] == 1

    def test_all_identical(self):
        """When all points are identical, none dominates another."""
        F = np.full((5, 3), 1.0)
        nd = non_dominated(F)
        assert nd.shape[0] == 5

    def test_strongly_dominated_chain(self):
        """Only the first point survives when each dominates the next."""
        F = np.array([[1.0, 1.0], [2.0, 2.0], [3.0, 3.0]])
        nd = non_dominated(F)
        assert nd.shape[0] == 1
        npt.assert_array_equal(nd[0], [1.0, 1.0])

    def test_idempotent(self, rng):
        """Applying non_dominated twice should give the same result."""
        F = rng.random((30, 3))
        nd1 = non_dominated(F)
        nd2 = non_dominated(nd1)
        npt.assert_array_equal(nd1, nd2)


# --------------------------------------------------------------------------- #
# make_candidate_set
# --------------------------------------------------------------------------- #
class TestMakeCandidateSet:
    """Tests for make_candidate_set()."""

    def test_output_shape(self, rng):
        """Should return an (N x m) matrix."""
        F = make_candidate_set("concave", 30, 3, rng)
        assert F.ndim == 2
        assert F.shape[1] == 3

    def test_enough_candidates(self, rng):
        """Should return a reasonable number of candidates."""
        F = make_candidate_set("concave", 30, 3, rng)
        assert F.shape[0] >= 8  # at least the safety floor

    def test_with_dominated_points(self, rng):
        """Adding dominated points should increase the count."""
        F_nd = make_candidate_set("linear", 20, 3, rng, n_dominated=0)
        rng2 = np.random.default_rng(42)
        F_dom = make_candidate_set("linear", 20, 3, rng2, n_dominated=10)
        assert F_dom.shape[0] >= F_nd.shape[0]

    @pytest.mark.parametrize("geometry", ALL_GEOMETRIES)
    def test_all_geometries(self, geometry, rng):
        """make_candidate_set should work for all geometries."""
        F = make_candidate_set(geometry, 20, 3, rng)
        assert F.shape[0] >= 1
        assert F.shape[1] == 3


# --------------------------------------------------------------------------- #
# make_redundant_set
# --------------------------------------------------------------------------- #
class TestMakeRedundantSet:
    """Tests for make_redundant_set()."""

    def test_output_shape(self, rng):
        """Output should have sum(group_sizes) columns and n rows."""
        group_sizes = [2, 3, 2]  # 3 groups → 7 columns total
        F, groups, base = make_redundant_set("concave", 30, group_sizes, rng)
        assert F.shape == (30, 7)
        assert groups.shape == (7,)
        assert base.shape == (30, 3)

    def test_group_labels(self, rng):
        """Group labels should correctly map objectives to underlying criteria."""
        group_sizes = [2, 3]
        F, groups, base = make_redundant_set("linear", 20, group_sizes, rng)
        assert list(groups[:2]) == [0, 0]
        assert list(groups[2:5]) == [1, 1, 1]

    def test_within_group_correlation(self, rng):
        """Objectives within the same group should be positively correlated."""
        group_sizes = [3, 3]
        F, groups, base = make_redundant_set("concave", 100, group_sizes, rng)
        # Columns 0, 1, 2 are group 0 → should correlate positively
        corr = np.corrcoef(F.T)
        assert corr[0, 1] > 0.5
        assert corr[0, 2] > 0.5

    def test_positive_values(self, rng):
        """All objective values should be positive."""
        F, groups, base = make_redundant_set("concave", 30, [2, 2], rng)
        assert F.min() > 0
