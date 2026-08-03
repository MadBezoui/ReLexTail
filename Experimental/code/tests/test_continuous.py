"""Tests for the front-free continuous formulation (Theorem 9).

These pin the two properties the manuscript claims: the solver-call accounting
is exactly 6m+5 for the canonical core, and the sequential stage optima are the
partial sums of the descending-sorted disappointment profile (which is what
makes the scheme lexicographic rather than merely hierarchical).
"""
import numpy as np
import pytest

from lexpr import directopt
from lexpr.continuous import continuous_lexpr, make_probes


def _instance(m, n, seed):
    rng = np.random.default_rng(seed)
    return directopt.random_linear_mop(m, n=n, n_constr=max(4, n // 2), rng=rng)


@pytest.mark.parametrize("m,n", [(3, 6), (4, 8), (5, 10)])
def test_solver_calls_match_theorem_accounting(m, n):
    """2m bound LPs + 2(m+1) sum-probe anchors + (m+1) max-probe anchors + K stages."""
    C, A, b = _instance(m, n, seed=11 + m)
    _, info = continuous_lexpr(C, A, b)
    K = m + 2
    assert info["K"] == K
    assert info["bound_calls"] == 2 * m
    assert info["anchor_calls"] == 2 * (m + 1) + (m + 1)
    assert info["stage_calls"] == K
    assert info["solver_calls"] == 6 * m + 5


def test_continuous_relextail():
    from lexpr.continuous import continuous_relextail
    C = np.array([
        [1.0, 0.0],
        [0.0, 1.0],
        [0.5, 0.5]
    ])
    A = np.array([
        [1.0, 1.0],
        [-1.0, 0.0],
        [0.0, -1.0]
    ])
    b = np.array([1.0, 0.0, 0.0])
    
    resolutions = {
        "maximum": "0.1",
        "tail_025": "0.1",
        "tail_050": "0.1",
        "tail_100": "0.1"
    }
    
    x, info = continuous_relextail(C, A, b, resolutions)
    
    assert x is not None
    assert "stage_optima" in info
    assert "M" in info["stage_optima"]
    assert "z_M" in info["stage_optima"]


@pytest.mark.parametrize("m,n", [(3, 6), (4, 8), (5, 10)])
def test_stage_optima_are_partial_sums_of_profile(m, n):
    """T*_p must equal the sum of the p largest disappointments at the optimum."""
    C, A, b = _instance(m, n, seed=101 + m)
    _, info = continuous_lexpr(C, A, b)
    prof = np.asarray(info["profile_sorted"])
    for p, T in enumerate(info["stage_optima"], start=1):
        assert T == pytest.approx(float(prof[:p].sum()), abs=1e-5)


@pytest.mark.parametrize("m,n", [(3, 6), (4, 8)])
def test_stage_optima_nondecreasing(m, n):
    C, A, b = _instance(m, n, seed=7 + m)
    _, info = continuous_lexpr(C, A, b)
    T = info["stage_optima"]
    assert all(T[i] <= T[i + 1] + 1e-9 for i in range(len(T) - 1))


def test_profile_in_unit_interval_and_probe_count():
    C, A, b = _instance(4, 8, seed=5)
    _, info, d = continuous_lexpr(C, A, b, return_profile=True)
    assert len(d) == info["K"]
    assert np.all(d >= -1e-9) and np.all(d <= 1 + 1e-9)


def test_direct_no_worse_than_weighted_sum_enumeration():
    """The direct optimum cannot be beaten by any weighted-sum point, since the
    enumeration searches a finite subset of the same feasible set."""
    from lexpr.continuous import (
        SolverCounter,
        _anchors,
        _criterion_bounds,
        _disappointments_at,
        _probe_rows,
    )

    m, n = 4, 8
    C, A, b = _instance(m, n, seed=23)
    x, info = continuous_lexpr(C, A, b)

    bounds = [(0.0, 1.0)] * n
    ctr = SolverCounter()
    f_lo, f_hi = _criterion_bounds(C, A, b, bounds, ctr)
    rng_obj = np.maximum(f_hi - f_lo, 1e-9)
    rows = _probe_rows(make_probes(m), C, f_lo, rng_obj)
    qs, qw = _anchors(rows, A, b, bounds, ctr)
    R = qw - qs
    keep = [k for k in range(len(rows)) if R[k] > 1e-9]
    rows, qs, R = [rows[k] for k in keep], qs[keep], R[keep]

    rng = np.random.default_rng(0)
    direct = np.asarray(info["profile_sorted"])
    for w in rng.dirichlet(np.ones(m), size=60):
        res = directopt._solve_lp(w @ C, A, b, bounds)
        prof = np.sort(_disappointments_at(res.x, rows, qs, R))[::-1]
        # direct <=_lex prof, up to solver tolerance
        diff = np.where(np.abs(direct - prof) > 1e-6)[0]
        if diff.size:
            assert direct[diff[0]] < prof[diff[0]]
