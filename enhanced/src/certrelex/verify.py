"""Independent replay verification of emitted certificates.

Design constraint from the plan: *the verifier must be simpler than the search
code and independent of its heuristic decisions*.  This module therefore

* never calls :mod:`certrelex.enclosure` or :mod:`certrelex.interval`;
* uses exact :class:`fractions.Fraction` arithmetic throughout, so it does not
  reuse -- and cannot inherit a bug from -- the outward-rounded binary64 path;
* knows nothing about branching, budgets or gates.  It is handed a leaf box and
  a claimed winner, and it recomputes the enclosure and the comparison.

A leaf that the verifier accepts is certified by two independent numerical
routes.  A leaf it rejects is reported as a failure, never silently widened.
"""
from __future__ import annotations

from fractions import Fraction

import numpy as np

from .profile import profile

RETENTION_EPS = Fraction(1, 10**9)


def _fr(x):
    return Fraction(float(x))


def _r_box(F, box):
    """Exact enclosure of ``r`` over the leaf, by corner evaluation."""
    ideal_lo, ideal_hi, nadir_lo, nadir_hi = (list(map(_fr, v)) for v in box)
    n, m = F.shape
    F_q = [[_fr(v) for v in row] for row in F]
    lo = [[None] * m for _ in range(n)]
    hi = [[None] * m for _ in range(n)]
    for I in (ideal_lo, ideal_hi):
        for N in (nadir_lo, nadir_hi):
            for j in range(m):
                den = N[j] - I[j]
                if den <= 0:
                    raise ValueError("non-positive normalising denominator")
                for i in range(n):
                    val = (F_q[i][j] - I[j]) / den
                    lo[i][j] = val if lo[i][j] is None else min(lo[i][j], val)
                    hi[i][j] = val if hi[i][j] is None else max(hi[i][j], val)
    return lo, hi


def _probe_box(probe, r_lo, r_hi):
    kind, idx = probe
    idx = list(idx)
    if kind == "single":
        i = idx[0]
        return [row[i] for row in r_lo], [row[i] for row in r_hi]
    if kind == "mean":
        k = Fraction(len(idx))
        return (
            [sum((row[i] for i in idx), Fraction(0)) / k for row in r_lo],
            [sum((row[i] for i in idx), Fraction(0)) / k for row in r_hi],
        )
    if kind == "max":
        return (
            [max(row[i] for i in idx) for row in r_lo],
            [max(row[i] for i in idx) for row in r_hi],
        )
    raise ValueError(f"unknown probe kind {kind!r}")


def enclose(F, probes, box):
    """Exact rational enclosure ``(D_lo, D_hi)`` of the disappointment matrix.

    The quotient ``(v - a) / (c - a)`` is evaluated at the four corners of the
    shared-anchor rectangle and the extremes are taken.  ``g`` is coordinatewise
    monotone in ``(a, c)`` for fixed ``v`` and increasing in ``v``, so this is
    the exact range of the independent-variable relaxation; it is written out
    the obvious way here rather than reusing the search-side primitive.
    """
    F = np.asarray(F, dtype=float)
    r_lo, r_hi = _r_box(F, box)
    n = F.shape[0]
    D_lo = [[] for _ in range(n)]
    D_hi = [[] for _ in range(n)]
    for q in probes:
        if q[0] == "single":
            # Singleton cancellation, checked rather than assumed.  r_i is an
            # increasing affine image of f_i, so the candidates attaining the
            # anchors do not move with b and the affine map cancels in
            # D_i = (f_i - min f_i) / (max f_i - min f_i).  The value is
            # recomputed here from the raw bounds at all four corners of the
            # box and refused unless every corner agrees with the closed form.
            col = _singleton_column(F, q[1][0], box)
            for i in range(n):
                D_lo[i].append(col[i])
                D_hi[i].append(col[i])
            continue
        v_lo, v_hi = _probe_box(q, r_lo, r_hi)
        a_lo, a_hi = min(v_lo), min(v_hi)
        c_lo, c_hi = max(v_lo), max(v_hi)
        if c_lo - a_hi <= RETENTION_EPS:
            raise ValueError("probe active range is not certifiably positive")
        for i in range(n):
            vals_lo, vals_hi = [], []
            for a in (a_lo, a_hi):
                for c in (c_lo, c_hi):
                    vals_lo.append((v_lo[i] - a) / (c - a))
                    vals_hi.append((v_hi[i] - a) / (c - a))
            D_lo[i].append(max(Fraction(0), min(min(vals_lo), min(vals_hi))))
            D_hi[i].append(min(Fraction(1), max(max(vals_lo), max(vals_hi))))
    return D_lo, D_hi


def verify_leaf(F, probes, box, winner: int, resolutions=None) -> dict:
    """Recheck one certified leaf.  Returns a dict with ``ok`` and a reason."""
    try:
        D_lo, D_hi = enclose(F, probes, box)
    except ValueError as exc:
        return {"ok": False, "reason": f"enclosure refused: {exc}"}
    psi_win = profile(D_hi[winner], resolutions)
    for y in range(len(D_lo)):
        if y == winner:
            continue
        if not (psi_win < profile(D_lo[y], resolutions)):
            return {"ok": False, "reason": f"rival {y} not dominated on this leaf"}
    return {"ok": True, "reason": "all rivals dominated"}


def replay(F, probes, leaves, winner: int, resolutions=None) -> dict:
    """Replay a list of leaf records (as emitted by :func:`certify_winner`)."""
    failures = []
    for k, leaf in enumerate(leaves):
        box = (
            np.array(leaf["ideal_lo"], dtype=float),
            np.array(leaf["ideal_hi"], dtype=float),
            np.array(leaf["nadir_lo"], dtype=float),
            np.array(leaf["nadir_hi"], dtype=float),
        )
        out = verify_leaf(F, probes, box, winner, resolutions)
        if not out["ok"]:
            failures.append({"leaf": k, **out})
    return {
        "n_leaves": len(leaves),
        "n_failures": len(failures),
        "failures": failures,
        "ok": not failures,
    }


def _singleton_column(F, i: int, box) -> list:
    """Exact, bound-invariant disappointment of the singleton probe ``q_i``.

    The closed form is ``(f_i - min f_i) / (max f_i - min f_i)``.  It is then
    cross-checked against a direct evaluation at the four corners of the box:
    normalise with that corner's bounds, take the probe anchors, divide.  A
    corner that disagrees means the invariance claim is false on this box and
    the leaf is refused.
    """
    col = [_fr(v) for v in F[:, i]]
    lo, hi = min(col), max(col)
    if hi - lo <= RETENTION_EPS:
        raise ValueError("singleton probe is not retained on this box")
    closed = [(v - lo) / (hi - lo) for v in col]
    ideal_lo, ideal_hi, nadir_lo, nadir_hi = (list(map(_fr, v)) for v in box)
    for I in (ideal_lo, ideal_hi):
        for N in (nadir_lo, nadir_hi):
            den = N[i] - I[i]
            if den <= 0:
                raise ValueError("non-positive normalising denominator")
            r = [(v - I[i]) / den for v in col]
            a, c = min(r), max(r)
            if c - a <= 0:
                raise ValueError("degenerate singleton active range at a corner")
            if [(x - a) / (c - a) for x in r] != closed:
                raise ValueError("singleton invariance violated at a box corner")
    return closed
