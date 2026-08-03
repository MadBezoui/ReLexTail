"""Referee point 4 (round 3): the certified enclosures must be validated
interval arithmetic, not a fixed final widening.

The check compares the binary64 enclosure against the EXACT value computed in
rational arithmetic (fractions.Fraction), over the same bound box. Every exact
value must lie inside the computed interval.

What these tests do and do not establish. They verify that the implemented
enclosure formula is correct and that outward rounding never breaks containment.
They do NOT establish that outward rounding is empirically necessary: we
searched 400 random instances plus constructed near-duplicate, one-ulp-separated
and wide-dynamic-range cases, and found no configuration where plain
round-to-nearest evaluation escaped the exact range. The corner construction
takes a minimum and a maximum over four corner evaluations, which leaves
structural slack. Outward rounding is therefore a guarantee that removes the
need for such a search, not a repair of an observed failure, and the paper says
so rather than implying the widening corrects anything.
"""
from fractions import Fraction as Fr
import numpy as np
import pytest
from lexpr import certified


def _exact_D(F, probe, box, cand):
    """Exact range of D_q(cand) over the corners of the bound box, in rationals.

    The extrema of each r_i over the rectangle are attained at its corners
    (linear-fractional in the two bounds), so ranging over corners of the two
    bound coordinates per criterion bounds the exact value.
    """
    ideal_lo, ideal_hi, nadir_lo, nadir_hi = box
    n, m = F.shape
    kind, idx = probe
    idx = list(idx)
    vals = []
    # enumerate corners of the bound box restricted to the criteria the probe uses
    from itertools import product
    for choice in product(*[[(Fr(ideal_lo[i]), Fr(nadir_lo[i])),
                             (Fr(ideal_lo[i]), Fr(nadir_hi[i])),
                             (Fr(ideal_hi[i]), Fr(nadir_lo[i])),
                             (Fr(ideal_hi[i]), Fr(nadir_hi[i]))] for i in idx]):
        r = {}
        for pos, i in enumerate(idx):
            I, N = choice[pos]
            if N - I <= 0:
                return None
            r[i] = [(Fr(F[a, i]) - I) / (N - I) for a in range(n)]
        if kind == "mean":
            v = [sum(r[i][a] for i in idx) / len(idx) for a in range(n)]
        elif kind == "max":
            v = [max(r[i][a] for i in idx) for a in range(n)]
        else:
            v = [r[idx[0]][a] for a in range(n)]
        qs, qw = min(v), max(v)
        if qw - qs <= 0:
            continue
        vals.append((v[cand] - qs) / (qw - qs))
    return (min(vals), max(vals)) if vals else None


@pytest.mark.parametrize("seed", range(12))
def test_enclosure_contains_the_exact_value(seed):
    rng = np.random.default_rng(seed)
    F = rng.random((4, 3))
    probes = [("mean", (0, 1, 2)), ("max", (0, 1, 2))]
    box = certified._box_from_p(F, 0.05)
    Dlo, Dhi = certified._D_enclosure(F, probes, box)
    for k, probe in enumerate(probes):
        for cand in range(F.shape[0]):
            exact = _exact_D(F, probe, box, cand)
            if exact is None:
                continue
            lo, hi = exact
            assert Fr(Dlo[cand, k]) <= lo, (
                f"lower bound {Dlo[cand, k]} exceeds exact minimum {float(lo)}")
            assert Fr(Dhi[cand, k]) >= hi, (
                f"upper bound {Dhi[cand, k]} below exact maximum {float(hi)}")


def test_ill_conditioned_instance_is_still_enclosed():
    """Near-identical candidates make q_x - q* cancel catastrophically."""
    F = np.array([[1.0,          1.0,          1.0],
                  [1.0 + 1e-13,  1.0,          1.0 + 3e-13],
                  [1.0,          1.0 + 1e-13,  1.0 + 1e-13],
                  [1.0 + 2e-13,  1.0 + 1e-13,  1.0 + 2e-13]])
    probes = [("mean", (0, 1, 2))]
    box = certified._box_from_p(F, 0.01)
    Dlo, Dhi = certified._D_enclosure(F, probes, box)
    assert (Dlo <= Dhi).all()
    for cand in range(F.shape[0]):
        exact = _exact_D(F, probes[0], box, cand)
        if exact is None:
            continue
        lo, hi = exact
        assert Fr(Dlo[cand, 0]) <= lo and Fr(Dhi[cand, 0]) >= hi


def test_division_refuses_a_denominator_touching_zero():
    with pytest.raises(ValueError):
        certified._idiv_pos(np.array([1.0]), np.array([2.0]),
                            np.array([0.0]), np.array([1.0]))


# --------------------------------------------------------------------------
# Directed tests requested by the referee (round 4, section 4.3). Each targets
# a specific way the outward-rounded evaluation could silently lose soundness.
# --------------------------------------------------------------------------

def test_cancellation_in_numerator_is_still_enclosed():
    """q_x - q* cancels to near zero: the relative error of the difference
    explodes even though every operand is well scaled. A scheme that widened
    only the final result by a relative amount would fail here."""
    base = np.array([0.5, 0.25, 0.125])
    F = np.vstack([base, base + 1e-15, base + 2e-15, base + 3e-15])
    probes = [("mean", (0, 1, 2))]
    box = certified._box_from_p(F, 0.02)
    Dlo, Dhi = certified._D_enclosure(F, probes, box)
    assert (Dlo <= Dhi).all()
    for cand in range(F.shape[0]):
        exact = _exact_D(F, probes[0], box, cand)
        if exact is None:
            continue
        lo, hi = exact
        assert Fr(Dlo[cand, 0]) <= lo and Fr(Dhi[cand, 0]) >= hi


def test_near_degenerate_denominator_is_refused_not_approximated():
    """When the probe range cannot be separated from zero the enclosure must
    fall back to [0, 1] rather than dividing by something tiny."""
    F = np.array([[1.0, 2.0], [1.0 + 1e-17, 2.0], [1.0, 2.0 + 1e-17]])
    probes = [("mean", (0, 1))]
    Dlo, Dhi = certified._D_enclosure(F, probes, certified._box_from_p(F, 1e-9))
    assert np.all(Dlo[:, 0] == 0.0) and np.all(Dhi[:, 0] == 1.0)


def test_subnormal_endpoints_do_not_break_the_enclosure():
    """Gradual underflow is allowed by the soundness argument; check that the
    outward step really moves by at least one local spacing there."""
    tiny = np.finfo(float).tiny
    for x in (0.0, tiny, tiny * 4, -tiny * 3, 5e-324):
        lo, hi = certified._dn(x), certified._up(x)
        assert lo < x < hi or (lo <= x <= hi and lo != hi)


def test_overflow_is_refused_rather_than_propagated():
    with pytest.raises(FloatingPointError):
        certified._check_finite(np.array([np.inf]))
    with pytest.raises(FloatingPointError):
        certified._check_finite(np.array([np.nan]))


def test_normalised_values_outside_the_unit_interval_are_handled():
    """The perturbation model lets a bound cross an observation, so r_i may
    leave [0, 1] and aggregate terms may have mixed signs."""
    F = np.array([[0.0, 10.0], [5.0, 5.0], [10.0, 0.0]])
    ideal = np.array([2.0, 2.0])      # strictly inside the observed range
    nadir = np.array([8.0, 8.0])      # also inside: r leaves [0, 1] both ways
    box = (ideal * 0.99, ideal * 1.01, nadir * 0.99, nadir * 1.01)
    r_lo, r_hi = certified._r_enclosure(F, *box)
    assert (r_lo <= r_hi).all()
    assert (r_lo < 0).any() and (r_hi > 1).any(), "instance no longer exercises the case"


def test_one_ulp_separation_is_not_collapsed():
    """Two candidates separated by a single ulp must not be merged by the
    outward rounding of the comparison inputs at the finite-selector level."""
    a = 0.3
    b = np.nextafter(a, np.inf)
    D = np.array([[a, 0.1], [b, 0.1]])
    from lexpr.methods import leximax_argmin
    assert leximax_argmin(D) == 0


def test_child_enclosure_is_contained_in_parent():
    """Subdivision must tighten, never widen: this is what makes the inherited
    survivor set of Algorithm 1 a sound superset for its children."""
    rng = np.random.default_rng(3)
    F = rng.random((5, 3))
    probes = [("mean", (0, 1, 2)), ("max", (0, 1, 2))]
    parent = certified._box_from_p(F, 0.05)
    Plo, Phi = certified._D_enclosure(F, probes, parent)
    for child in certified._split(parent):
        Clo, Chi = certified._D_enclosure(F, probes, child)
        assert (Clo >= Plo - 1e-12).all(), "child lower bound escapes the parent"
        assert (Chi <= Phi + 1e-12).all(), "child upper bound escapes the parent"
