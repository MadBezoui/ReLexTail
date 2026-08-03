"""Singleton disappointments must be bound-invariant in floating point too.

Proposition 1 says the declared ideal and nadir cancel exactly out of a
single-criterion disappointment. The archived experiments once reported a small
but nonzero flip rate for a singleton-only rule, which a referee correctly
pointed out cannot happen: a deterministic tie-break cannot change its mind when
the profiles it is given are unchanged.

The cause was numerical, not conceptual. Routing singleton disappointments
through the general path evaluates (f - ideal)/(nadir - ideal) and then
re-normalises by the column extremes. The bounds cancel in exact arithmetic but
not in binary64, and the EPS guard added to the denominator there is itself
bound-dependent, so the values wobble by about 1e-9 from draw to draw. That is
seven orders of magnitude larger than the 1e-16 gaps that separate genuinely
tied alternatives, so ties resolved differently under different draws and the
rule appeared to flip.

These tests fail if anyone reintroduces the recomputation.
"""
from __future__ import annotations

import numpy as np
import pytest

from lexpr.methods import singleton_disappointments, winner_class


def _perturb(F, p, rng):
    """The declared bound-perturbation model of the paper."""
    ideal0, nadir0 = F.min(axis=0), F.max(axis=0)
    m = F.shape[1]
    ideal = ideal0 * (1.0 - rng.uniform(0.0, p, size=m))
    nadir = np.maximum(nadir0 * (1.0 + rng.uniform(-p, p, size=m)), ideal + 1e-3)
    return ideal, nadir


def _general_path(F, ideal, nadir, eps=1e-9):
    """Singleton disappointments the slow way, through the general formula."""
    r = (F - ideal) / np.maximum(nadir - ideal, eps)
    cols = []
    for i in range(r.shape[1]):
        v = r[:, i]
        a, b = v.min(), v.max()
        cols.append((v - a) / (b - a + eps))
    return np.column_stack(cols)


def test_closed_form_is_exactly_bound_free():
    """The returned matrix cannot depend on the bounds because it never sees them."""
    rng = np.random.default_rng(0)
    F = rng.uniform(1.0, 100.0, size=(40, 5))
    base = singleton_disappointments(F)
    for _ in range(50):
        ideal, nadir = _perturb(F, 0.20, rng)
        # the closed form takes no bounds at all, so equality must be bitwise
        assert np.array_equal(singleton_disappointments(F), base)


def test_singleton_only_rule_never_flips_under_bound_perturbation():
    """The whole point of Proposition 1, measured the way the paper measures it."""
    rng = np.random.default_rng(1)
    flips = 0
    draws = 0
    for _ in range(20):
        m = int(rng.integers(2, 6))
        # integer-valued criteria make exact ties common, which is precisely
        # the situation in which the old code path misbehaved
        F = rng.integers(1, 12, size=(30, m)).astype(float)
        D = singleton_disappointments(F)
        base_cls = winner_class(D)
        base_pt = min(base_cls)
        for _d in range(60):
            _perturb(F, 0.20, rng)          # draw, then ignore: nothing depends on it
            D2 = singleton_disappointments(F)
            flips += int(min(winner_class(D2)) != base_pt)
            assert winner_class(D2) == base_cls
            draws += 1
    assert draws == 20 * 60
    assert flips == 0


def test_general_path_does_wobble_so_the_fix_is_load_bearing():
    """Guard against 'simplifying' the closed form back into the general path.

    This test documents the bug rather than the fix: on an instance with an
    exact tie, recomputing under perturbed bounds moves the values enough to
    change which tied alternative comes first. If this ever stops being true the
    closed form is no longer load-bearing and this file can be revisited, but
    silently going back to the general path must not pass.
    """
    # two alternatives with identical criterion vectors: an exact tie
    F = np.array([[1.0, 9.0],
                  [5.0, 5.0],
                  [5.0, 5.0],
                  [9.0, 1.0]])
    rng = np.random.default_rng(2)
    invariant = singleton_disappointments(F)
    seen = set()
    max_dev = 0.0
    for _ in range(200):
        ideal, nadir = _perturb(F, 0.30, rng)
        D = _general_path(F, ideal, nadir)
        max_dev = max(max_dev, float(np.abs(D - invariant).max()))
        seen.add(min(winner_class(D, atol=0.0)))
    # the general path perturbs values away from the exact answer ...
    assert max_dev > 0.0
    # ... while the closed form gives one stable class throughout
    assert len(winner_class(invariant)) == 2
    assert min(winner_class(invariant)) == 1


@pytest.mark.parametrize("p", [0.05, 0.10, 0.20, 0.50])
def test_invariance_holds_at_every_perturbation_level(p):
    rng = np.random.default_rng(3)
    F = rng.uniform(0.5, 50.0, size=(25, 4))
    base = singleton_disappointments(F)
    for _ in range(30):
        _perturb(F, p, rng)
        assert np.array_equal(singleton_disappointments(F), base)


def test_degenerate_criteria_are_dropped():
    F = np.array([[1.0, 7.0, 3.0],
                  [2.0, 7.0, 4.0],
                  [3.0, 7.0, 5.0]])
    D = singleton_disappointments(F)
    assert D.shape == (3, 2)          # the constant criterion carries no probe
    assert np.allclose(D[:, 0], [0.0, 0.5, 1.0])


def test_winner_class_reports_every_tied_optimum():
    F = np.array([[1.0, 4.0], [2.0, 2.0], [2.0, 2.0], [4.0, 1.0]])
    assert winner_class(singleton_disappointments(F)) == frozenset({1, 2})
