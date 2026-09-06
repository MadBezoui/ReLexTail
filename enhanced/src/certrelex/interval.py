"""Outward-rounded binary64 interval arithmetic.

Numerical contract (see ``enhanced/protocol/numerical_contract.md``).

Every elementary operation is evaluated in IEEE-754 binary64 under
round-to-nearest and then pushed outward by exactly one
:func:`numpy.nextafter` step.  Round-to-nearest commits an error strictly
smaller than half the local spacing, and one ``nextafter`` step moves by the
full local spacing, so the directed result always encloses the exact value.
The property is maintained inductively along a whole evaluation.

Subnormal intermediates are accepted: the argument above uses only the
absolute round-to-nearest bound and the local spacing, both of which remain
valid at ``2**-1074``.  Overflow to infinity and NaN are refused, because they
break the enclosure rather than widen it.

Accumulation order is fixed and explicit; ``numpy.sum`` is never used inside a
certified path because its pairwise association order depends on array length
and build.
"""
from __future__ import annotations

import numpy as np

_INF = np.inf


def dn(x):
    """Next representable value strictly below ``x``."""
    return np.nextafter(x, -_INF)


def up(x):
    """Next representable value strictly above ``x``."""
    return np.nextafter(x, _INF)


def check_finite(*arrays) -> None:
    """Refuse to certify past an overflow or a NaN."""
    for a in arrays:
        if not np.isfinite(np.asarray(a)).all():
            raise FloatingPointError("non-finite intermediate in interval evaluation")


def isub(alo, ahi, blo, bhi):
    """``[alo, ahi] - [blo, bhi]``, outward rounded."""
    return dn(alo - bhi), up(ahi - blo)


def idiv_pos(alo, ahi, blo, bhi):
    """``[alo, ahi] / [blo, bhi]`` for a denominator bounded away from zero.

    Division is refused rather than approximated when ``blo <= 0``.
    """
    if np.any(np.asarray(blo) <= 0.0):
        raise ValueError("interval division requires a strictly positive denominator")
    lo = np.minimum(dn(alo / bhi), dn(alo / blo))
    hi = np.maximum(up(ahi / blo), up(ahi / bhi))
    return lo, hi


def imean(vlo, vhi, axis=1):
    """Interval mean along ``axis`` with a fixed ascending accumulation order."""
    assert axis == 1, "accumulation order is defined for axis=1"
    k = vlo.shape[1]
    slo = vlo[:, 0].copy()
    shi = vhi[:, 0].copy()
    for j in range(1, k):
        slo = dn(slo + vlo[:, j])
        shi = up(shi + vhi[:, j])
    return dn(slo / k), up(shi / k)


def quotient_range(vlo, vhi, alo, ahi, clo, chi):
    """Range of ``g(v, a, c) = (v - a) / (c - a)`` over the product box.

    This is the dependency-preserving primitive of the enhanced engine.  For a
    single retained probe, ``a = q^*(b)`` and ``c = q^w(b)`` are *shared*
    anchors: the same two numbers enter the numerator and the denominator of
    every candidate's disappointment at the same ``b``.  Replacing the pair
    ``(numerator, denominator)`` by two independently widened intervals throws
    that link away and lets the numerator take its extreme value against a
    denominator that the same ``a`` could never produce.

    Soundness.  On the rectangle ``[alo, ahi] x [clo, chi]`` with ``clo > ahi``
    the denominator is positive everywhere and, for fixed ``v``,

        d/dc g = -(v - a) / (c - a)^2   (sign constant in c),
        d/da g =  (v - c) / (c - a)^2   (sign constant in a),

    so ``g`` is coordinatewise monotone in ``(a, c)``: minimising first over
    ``c`` at an endpoint and then over ``a`` at an endpoint shows that the
    extrema over the rectangle are attained at its four corners.  ``g`` is
    strictly increasing in ``v``, so the minimum uses ``v = vlo`` and the
    maximum uses ``v = vhi``.  Each corner is a point/point division evaluated
    with directed rounding, so the returned interval encloses the exact range
    of the relaxation in which ``v``, ``a`` and ``c`` vary independently.

    Tightness.  When ``vlo >= ahi`` -- the case for every candidate that is not
    the probe's own minimiser -- the corner minimum is ``(vlo - ahi)/(chi - ahi)``
    and the corner maximum is ``(vhi - alo)/(clo - alo)``, each holding ``a``
    at a *single* value inside the expression.  The independent quotient
    returns ``(vlo - ahi)/(chi - alo)`` and ``(vhi - alo)/(clo - ahi)``, which
    are strictly wider whenever ``ahi > alo``.  That gap is the shared-anchor
    cancellation.

    Parameters are broadcast: ``alo, ahi, clo, chi`` are scalars for a probe,
    ``vlo, vhi`` are per-candidate arrays.

    Raises
    ------
    ValueError
        If ``clo - ahi <= 0``, i.e. the active range of the probe is not
        certifiably positive over the box.  The baseline routine refuses on
        exactly the same condition, so the two are compared on equal terms.
    """
    if not np.all(dn(clo - ahi) > 0.0):
        raise ValueError("probe active range is not certifiably positive")
    lo = None
    hi = None
    for a in (alo, ahi):
        for c in (clo, chi):
            # The corner is a pair of stored binary64 numbers, so the only
            # rounding left is in the subtraction and the division; both are
            # pushed outward.
            den_lo, den_hi = dn(c - a), up(c - a)
            if not np.all(den_lo > 0.0):
                raise ValueError("probe active range is not certifiably positive")
            num_lo, num_hi = dn(vlo - a), up(vhi - a)
            cand_lo, cand_hi = idiv_pos(num_lo, num_hi, den_lo, den_hi)
            lo = cand_lo if lo is None else np.minimum(lo, cand_lo)
            hi = cand_hi if hi is None else np.maximum(hi, cand_hi)
    check_finite(lo, hi)
    return lo, hi


def quotient_range_independent(vlo, vhi, alo, ahi, clo, chi):
    """Baseline enclosure that drops the shared-anchor link.

    Reproduces the arithmetic of the current submission engine: the numerator
    and the denominator are widened separately and then divided as independent
    intervals.  Kept as the ablation control for the dependency-preserving
    primitive, not as a recommended routine.
    """
    num_lo, num_hi = isub(vlo, vhi, alo, ahi)
    den_lo, den_hi = isub(clo, chi, alo, ahi)
    if np.any(np.asarray(den_lo) <= 0.0):
        raise ValueError("probe active range is not certifiably positive")
    lo, hi = idiv_pos(num_lo, num_hi, den_lo, den_hi)
    check_finite(lo, hi)
    return lo, hi
