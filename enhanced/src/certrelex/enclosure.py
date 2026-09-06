"""Sound enclosures of the disappointment matrix over a box of bounds.

The uncertainty set is a box of admissible ideal/nadir vectors

    beta = prod_i [I_i^lo, I_i^hi] x [N_i^lo, N_i^hi],

and the object to enclose is the retained disappointment matrix ``D(x; b)``.

Two enclosure modes are provided and are otherwise identical, so that the
effect of dependency preservation can be measured in isolation:

``"joint"``
    the enhanced mode.  The shared probe anchors ``q^*(b)`` and ``q^w(b)`` are
    kept inside a single quotient (see :func:`certrelex.interval.quotient_range`).

``"independent"``
    the baseline mode.  The numerator and the denominator are widened
    separately and divided as independent intervals, reproducing the
    arithmetic of the current submission engine.

Both modes refuse a box outright -- returning ``None`` -- when a normalising
denominator or a probe active range is not certifiably positive on it.  Refusal
never weakens soundness; it only leaves the box unresolved.
"""
from __future__ import annotations

from fractions import Fraction

import numpy as np

from .interval import (
    check_finite,
    dn,
    idiv_pos,
    imean,
    isub,
    quotient_range,
    quotient_range_independent,
    up,
)

#: Degenerate-probe guard.  A probe whose active range is not provably above
#: this relative threshold is not retained, and the box is refused.  It is a
#: retention test, never a term added to a denominator.
RETENTION_EPS = 1e-9


def canonical_probes(m: int):
    """The canonical family: ``m`` singletons plus the grand mean and maximum."""
    probes = [("single", (i,)) for i in range(m)]
    if m > 1:
        probes.append(("mean", tuple(range(m))))
        probes.append(("max", tuple(range(m))))
    return probes


def box_from_level(F: np.ndarray, p: float):
    """Range-relative uncertainty box ``B(p)`` of the manuscript, Eq. (box).

    ``I_i - p s_i <= ideal_i <= I_i + p s_i`` and likewise for the nadir, with
    ``s_i`` the nominal criterion range.  Denominators stay positive for
    ``p < 1/2``.
    """
    lo = F.min(axis=0)
    hi = F.max(axis=0)
    span = hi - lo
    return (lo - p * span, lo + p * span, hi - p * span, hi + p * span)


def r_enclosure(F, box):
    """Sound (and corner-exact) enclosure of the normalised criterion matrix.

    ``r_i(x; b) = (f_i(x) - I_i) / (N_i - I_i)`` is monotone in ``I_i`` and in
    ``N_i`` separately while the denominator stays positive, so its range over
    the two-dimensional rectangle is attained at the rectangle's corners; each
    corner is evaluated with directed rounding.
    """
    ideal_lo, ideal_hi, nadir_lo, nadir_hi = box
    los, his = [], []
    for I in (ideal_lo, ideal_hi):
        for N in (nadir_lo, nadir_hi):
            den_lo, den_hi = dn(N - I), up(N - I)
            if np.any(den_lo <= 0.0):
                raise ValueError("non-positive normalising denominator")
            num_lo, num_hi = dn(F - I), up(F - I)
            lo, hi = idiv_pos(num_lo, num_hi, den_lo, den_hi)
            check_finite(lo, hi)
            los.append(lo)
            his.append(hi)
    return np.stack(los, axis=0).min(axis=0), np.stack(his, axis=0).max(axis=0)


def probe_enclosure(probe, r_lo, r_hi):
    """Enclosure of ``q(r(x; b))`` for one probe, coordinatewise and exact."""
    kind, idx = probe
    idx = list(idx)
    if kind == "single":
        i = idx[0]
        return r_lo[:, i].copy(), r_hi[:, i].copy()
    if kind == "mean":
        return imean(r_lo[:, idx], r_hi[:, idx], axis=1)
    if kind == "max":
        # the maximum of interval endpoints selects an existing value
        return r_lo[:, idx].max(axis=1), r_hi[:, idx].max(axis=1)
    raise ValueError(f"unknown probe kind {kind!r}")


def _singleton_column(F, i, box):
    """Bound-invariant disappointment of the singleton probe ``q_i(r) = r_i``.

    The ideal and the nadir cancel exactly in
    ``D_i(x) = (f_i(x) - min_A f_i) / (max_A f_i - min_A f_i)``.  This is
    identity 1 of the dependency programme -- singleton cancellation -- and it
    is what makes ``m`` of the ``K = m + 2`` canonical coordinates carry zero
    width no matter how large the bound box is.  The interval returned here is
    only as wide as the two roundings of the subtraction and the division.
    """
    col = F[:, i]
    lo, hi = col.min(), col.max()
    span_box = box[3][i] - box[0][i]
    if span_box <= 0.0 or (hi - lo) / span_box <= RETENTION_EPS:
        raise ValueError("singleton probe is not uniformly retained on the box")
    num_lo, num_hi = isub(col, col, lo, lo)
    den_lo, den_hi = isub(hi, hi, lo, lo)
    if den_lo <= 0.0:
        raise ValueError("degenerate singleton active range")
    return idiv_pos(num_lo, num_hi, den_lo, den_hi)


def d_enclosure(F, probes, box, mode="joint"):
    """Return ``(D_lo, D_hi)``, each ``(n, K)``, sound for every ``b`` in ``box``.

    ``mode="joint"`` preserves the shared anchors; ``mode="independent"``
    reproduces the baseline arithmetic.  Returns ``None`` if the box cannot be
    certified at all (collapsed range, unretained probe, or overflow).
    """
    if mode not in ("joint", "independent"):
        raise ValueError(f"unknown enclosure mode {mode!r}")
    quotient = quotient_range if mode == "joint" else quotient_range_independent
    try:
        r_lo, r_hi = r_enclosure(F, box)
    except (ValueError, FloatingPointError):
        return None
    los, his = [], []
    for q in probes:
        try:
            if q[0] == "single":
                lo, hi = _singleton_column(F, q[1][0], box)
            else:
                v_lo, v_hi = probe_enclosure(q, r_lo, r_hi)
                a_lo, a_hi = v_lo.min(), v_hi.min()  # enclosure of q^*(b)
                c_lo, c_hi = v_lo.max(), v_hi.max()  # enclosure of q^w(b)
                if dn(c_lo - a_hi) <= RETENTION_EPS:
                    return None
                lo, hi = quotient(v_lo, v_hi, a_lo, a_hi, c_lo, c_hi)
        except (ValueError, FloatingPointError):
            return None
        # clipping applies to an already rigorous enclosure and selects
        # existing values, so it adds no error: 0 <= D <= 1 always holds
        los.append(np.clip(lo, 0.0, 1.0))
        his.append(np.clip(hi, 0.0, 1.0))
    return np.column_stack(los), np.column_stack(his)


def to_rational(matrix):
    """Exact rational view of stored binary64 endpoints.

    Every entry of an outward-rounded enclosure is a binary64 number and
    therefore an exact rational; converting it loses nothing and lets the
    profile comparison run without any floating-point tie tolerance.
    """
    return [[Fraction(float(v)) for v in row] for row in matrix]
