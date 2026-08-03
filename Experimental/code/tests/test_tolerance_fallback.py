"""Referee archive check 5f: the tolerance-cycle fallback of (S4).

The paper's Theorems 1 and 5 were corrected so that R_tau = {x*} follows from
the margin conditions only when the tolerance comparison graph is acyclic; under
the fallback branch it additionally requires x* to be the unique exact winner of
the PERTURBED profiles. This test implements (S4) directly from the supplement
and shows the caveat is not vacuous: it exhibits the configuration of Remark 1,
in which the margin conditions hold, U_tau = {x*}, a cycle exists elsewhere, and
the fallback class does NOT contain x*.
"""
import numpy as np
import pytest

TAU = 0.05


def _sorted_desc(p):
    return sorted((float(v) for v in p), reverse=True)


def _prec_tau(a, b, tau=TAU):
    """True if a strictly tau-precedes b: decide at the first coordinate whose
    gap exceeds tau."""
    for u, v in zip(a, b):
        if abs(u - v) > tau:
            return u < v
    return False


def _prec_exact(a, b):
    for u, v in zip(a, b):
        if u != v:
            return u < v
    return False


def _U_tau(profiles, tau=TAU):
    names = list(profiles)
    return {x for x in names
            if not any(_prec_tau(profiles[y], profiles[x], tau) for y in names if y != x)}


def _has_cycle(profiles, tau=TAU):
    names = list(profiles)
    edges = {x: [y for y in names if y != x and _prec_tau(profiles[x], profiles[y], tau)]
             for x in names}
    colour = {x: 0 for x in names}

    def visit(x):
        colour[x] = 1
        for y in edges[x]:
            if colour[y] == 1 or (colour[y] == 0 and visit(y)):
                return True
        colour[x] = 2
        return False

    return any(colour[x] == 0 and visit(x) for x in names)


def _W0(profiles):
    names = list(profiles)
    return {x for x in names
            if not any(_prec_exact(profiles[y], profiles[x]) for y in names if y != x)}


def _R_tau(profiles, tau=TAU):
    """(S4): report U_tau when it is nonempty and the tau-relation is acyclic,
    otherwise fall back to the exact class W_0 of the same profiles."""
    U = _U_tau(profiles, tau)
    if U and not _has_cycle(profiles, tau):
        return U, "U_tau"
    return _W0(profiles), "fallback"


def test_acyclic_branch_reports_the_tolerance_undominated_set():
    prof = {"x": _sorted_desc([0.10, 0.00]), "y": _sorted_desc([0.40, 0.00]),
            "z": _sorted_desc([0.80, 0.00])}
    R, branch = _R_tau(prof)
    assert branch == "U_tau" and R == {"x"}


def test_fallback_branch_can_exclude_the_tolerance_winner():
    """Remark 1 of the main text, made executable."""
    # perturbed profiles: x* tau-beats y, but y beats x* exactly
    prof = {"xstar": [0.51, 0.00], "y": [0.49, 0.20]}
    assert _prec_tau(prof["xstar"], prof["y"]), "x* should tau-beat y"
    assert _prec_exact(prof["y"], prof["xstar"]), "y should beat x* exactly"

    # Three inferior alternatives that cycle among themselves under tau while
    # x* tau-beats all of them. The cycle works because consecutive first
    # coordinates are within tau of each other, so those comparisons fall
    # through to the second coordinate, while the extreme pair is separated by
    # more than tau and decides the other way: c1 -> c2 -> c3 -> c1.
    prof.update({"c1": [0.90, 0.00], "c2": [0.86, 0.30], "c3": [0.82, 0.60]})
    assert _has_cycle(prof), "the added alternatives should create a tau-cycle"
    assert _U_tau(prof) == {"xstar"}, "margin conditions should give U_tau = {x*}"

    R, branch = _R_tau(prof)
    assert branch == "fallback"
    assert "xstar" not in R, (
        "if x* were always in the fallback class the theorem's caveat would be vacuous")
    assert "y" in R


def test_at_tau_zero_the_two_branches_coincide():
    """tau = 0 is the recommended deployment: the relation is the exact order,
    which is transitive, so no cycle can arise and the fallback never fires."""
    rng = np.random.default_rng(0)
    for _ in range(200):
        prof = {f"a{i}": _sorted_desc(rng.random(4)) for i in range(5)}
        assert not _has_cycle(prof, tau=0.0)
        R, branch = _R_tau(prof, tau=0.0)
        assert branch == "U_tau" and R == _W0(prof)
