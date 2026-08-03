"""Tests for lexpr.directopt — direct LexPR computation via LP formulation.

Covers: random_linear_mop, direct_lexpr_linear, enumerate_then_select,
and consistency between direct and enumerated approaches.
"""
import numpy as np
import pytest
import numpy.testing as npt

from lexpr.directopt import (
    _solve_lp, random_linear_mop, direct_lexpr_linear, enumerate_then_select,
)


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture
def rng():
    return np.random.default_rng(42)


@pytest.fixture
def small_mop(rng):
    """A small linear MOP instance for testing."""
    return random_linear_mop(m=3, n=6, n_constr=4, rng=rng)


# --------------------------------------------------------------------------- #
# random_linear_mop
# --------------------------------------------------------------------------- #
class TestRandomLinearMOP:
    """Tests for random_linear_mop()."""

    def test_output_shapes(self, rng):
        """C, A, b should have correct shapes."""
        C, A, b = random_linear_mop(m=3, n=8, n_constr=5, rng=rng)
        assert C.shape == (3, 8)
        assert A.shape == (5, 8)
        assert b.shape == (5,)

    def test_deterministic(self):
        """Same seed should produce identical MOP."""
        C1, A1, b1 = random_linear_mop(m=3, n=6, rng=np.random.default_rng(99))
        C2, A2, b2 = random_linear_mop(m=3, n=6, rng=np.random.default_rng(99))
        npt.assert_array_equal(C1, C2)
        npt.assert_array_equal(A1, A2)
        npt.assert_array_equal(b1, b2)

    def test_objectives_conflict(self, rng):
        """Each objective should be cheapest on a different variable block."""
        C, _, _ = random_linear_mop(m=3, n=8, rng=rng)
        # Objective i has C[i, i%n] *= 0.1, so it should be cheaper there
        for i in range(3):
            assert C[i, i % 8] < C[i].mean()


def test_failed_lp_raises_instead_of_returning_invalid_result():
    with pytest.raises(RuntimeError, match="LP solve failed"):
        _solve_lp(
            np.array([1.0]),
            np.array([[1.0], [-1.0]]),
            np.array([0.0, -1.0]),
            [(0.0, 1.0)],
        )


# --------------------------------------------------------------------------- #
# direct_lexpr_linear
# --------------------------------------------------------------------------- #
class TestDirectLurLinear:
    """Tests for direct_lexpr_linear() LP formulation."""

    def test_returns_valid_solution(self, small_mop):
        """Should return a feasible x in [0, 1]^n."""
        C, A, b = small_mop
        m, n = C.shape
        pw = np.vstack([np.eye(m), np.ones(m) / m])
        x, info = direct_lexpr_linear(C, A, b, pw)
        assert x.shape == (n,)
        # x should be in [0, 1]
        assert np.all(x >= -1e-6)
        assert np.all(x <= 1.0 + 1e-6)

    def test_satisfies_constraints(self, small_mop):
        """Solution x should satisfy A x <= b."""
        C, A, b = small_mop
        m = C.shape[0]
        pw = np.vstack([np.eye(m), np.ones(m) / m])
        x, info = direct_lexpr_linear(C, A, b, pw)
        violations = A @ x - b
        assert np.all(violations <= 1e-6)

    def test_info_dict(self, small_mop):
        """info should contain solver_calls, rho1, f_ideal, f_nadir."""
        C, A, b = small_mop
        m = C.shape[0]
        pw = np.vstack([np.eye(m), np.ones(m) / m])
        _, info = direct_lexpr_linear(C, A, b, pw)
        assert "solver_calls" in info
        assert "rho1" in info
        assert "f_ideal" in info
        assert "f_nadir" in info
        assert info["solver_calls"] > 0

    def test_ideal_le_nadir(self, small_mop):
        """f_ideal should be <= f_nadir for each objective."""
        C, A, b = small_mop
        m = C.shape[0]
        pw = np.vstack([np.eye(m), np.ones(m) / m])
        _, info = direct_lexpr_linear(C, A, b, pw)
        assert np.all(info["f_ideal"] <= info["f_nadir"] + 1e-6)

    def test_rho1_non_negative(self, small_mop):
        """The minimax regret value rho1 should be non-negative."""
        C, A, b = small_mop
        m = C.shape[0]
        pw = np.vstack([np.eye(m), np.ones(m) / m])
        _, info = direct_lexpr_linear(C, A, b, pw)
        assert info["rho1"] >= -1e-6


# --------------------------------------------------------------------------- #
# enumerate_then_select
# --------------------------------------------------------------------------- #
class TestEnumerateThenSelect:
    """Tests for enumerate_then_select()."""

    def test_returns_objective_matrix(self, small_mop, rng):
        """Should return a non-empty (K x m) objective matrix."""
        C, A, b = small_mop
        m = C.shape[0]
        F, info = enumerate_then_select(C, A, b, n_weights=50, rng=rng)
        assert F.ndim == 2
        assert F.shape[1] == m
        assert F.shape[0] >= 1

    def test_info_dict(self, small_mop, rng):
        """info should contain solver_calls and points_generated."""
        C, A, b = small_mop
        F, info = enumerate_then_select(C, A, b, n_weights=50, rng=rng)
        assert info["solver_calls"] == 50
        assert info["points_generated"] >= 1


# --------------------------------------------------------------------------- #
# Consistency: direct vs enumerated
# --------------------------------------------------------------------------- #
class TestDirectVsEnumerated:
    """The direct solution should be comparable to enumerated+post-processed."""

    def test_direct_objective_quality(self, rng):
        """Direct LexPR objective values should not be much worse than enumerated
        LexPR selection on a small problem."""
        C, A, b = random_linear_mop(m=3, n=6, n_constr=4, rng=rng)
        m, n = C.shape
        pw = np.vstack([np.eye(m), np.ones(m) / m])

        # Direct
        x_dir, _ = direct_lexpr_linear(C, A, b, pw)
        f_dir = C @ x_dir

        # Enumerated + LexPR post-processing
        from lexpr.methods import lexpr as lexpr_select, normalize
        F, _ = enumerate_then_select(C, A, b, n_weights=100,
                                     rng=np.random.default_rng(42))
        i_sel = lexpr_select(F)
        f_enum = F[i_sel]

        # Both should be feasible (finite)
        assert np.all(np.isfinite(f_dir))
        assert np.all(np.isfinite(f_enum))

        # Direct should not be catastrophically worse (within 2x of enum range)
        enum_range = F.max(axis=0) - F.min(axis=0) + 1e-9
        gap = (f_dir - f_enum) / enum_range
        # Allow each objective to be at most 3x the range worse
        assert np.all(gap < 3.0), f"Direct much worse than enum: gap={gap}"

    def test_singleton_probes_only(self, rng):
        """With singleton-only probes the direct LP should still be feasible."""
        C, A, b = random_linear_mop(m=2, n=5, n_constr=3, rng=rng)
        pw = np.eye(C.shape[0])  # singleton probes only
        x, info = direct_lexpr_linear(C, A, b, pw)
        assert np.all(x >= -1e-6)
        assert np.all(x <= 1.0 + 1e-6)
