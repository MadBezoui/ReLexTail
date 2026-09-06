"""Exact rational ReLexTail profiles.

The profile is the object the decision rule compares:

    Psi(D) = ( C_M, C_25, C_50, C_100, T_25, T_50, T_100, M, sort_desc(D) )

with ``M = max_q D_q``, ``T_alpha`` the upper-tail mean at level ``alpha`` and
``C_z = ceil(z / delta_z)`` the fixed-resolution category of ``z``.  Every
coordinate is computed here in exact rational arithmetic from
:class:`fractions.Fraction` inputs, so the certified path never depends on a
floating-point tie tolerance.  This module is the reference semantics; the
binary64 selector in ``Experimental/code/lexpr/orders/relex_tail.py`` must agree
with it on exactly representable inputs, which ``tests/test_oracle.py`` checks.

Monotonicity (used by every soundness proof in :mod:`certrelex.certify`).
Each coordinate of ``Psi`` is nondecreasing in ``D`` componentwise: order
statistics, maxima, upper-tail means and ``ceil(./delta)`` all are.  Hence
``D <= D'`` componentwise implies ``Psi(D) <= Psi(D')`` componentwise, which in
turn implies ``Psi(D) <=_lex Psi(D')``.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Iterable, Sequence

DEFAULT_RESOLUTION = Fraction("0.02")
TAIL_LEVELS = (Fraction(1, 4), Fraction(1, 2), Fraction(1))


def tail_mean(sorted_desc: Sequence[Fraction], alpha: Fraction) -> Fraction:
    """Upper-tail mean of the top ``alpha`` fraction of a descending sequence.

    Matches ``lexpr.orders.relex_tail.tail_cvar``: with ``h = alpha * K``,
    ``k = floor(h)`` and ``theta = h - k``, the value is
    ``(sum of the k largest + theta * the (k+1)-st) / h``, and the plain
    maximum when ``h <= 1``.
    """
    K = len(sorted_desc)
    if K == 0:
        return Fraction(0)
    h = alpha * K
    if h <= 1:
        return sorted_desc[0]
    k = h.numerator // h.denominator
    theta = h - k
    total = sum(sorted_desc[:k], Fraction(0))
    if theta:
        total += theta * sorted_desc[k]
    return total / h


def category(z: Fraction, delta: Fraction) -> int:
    """Fixed-resolution category ``ceil(z / delta)``, exact."""
    q = z / delta
    n, d = q.numerator, q.denominator
    return -((-n) // d)


def profile(row: Iterable[Fraction], resolutions=None):
    """Exact ReLexTail profile of one candidate's disappointment row."""
    values = sorted((Fraction(v) for v in row), reverse=True)
    if not values:
        raise ValueError("empty retained probe multiset")
    res = _resolution_vector(resolutions)
    M = values[0]
    tails = [tail_mean(values, a) for a in TAIL_LEVELS]
    cats = (
        category(M, res["maximum"]),
        category(tails[0], res["tail_025"]),
        category(tails[1], res["tail_050"]),
        category(tails[2], res["tail_100"]),
    )
    return cats + tuple(tails) + (M,) + tuple(values)


def _resolution_vector(resolutions):
    keys = ("maximum", "tail_025", "tail_050", "tail_100")
    if resolutions is None:
        return {k: DEFAULT_RESOLUTION for k in keys}
    if isinstance(resolutions, (str, Fraction, int)):
        return {k: Fraction(str(resolutions)) for k in keys}
    return {k: Fraction(str(resolutions.get(k, DEFAULT_RESOLUTION))) for k in keys}


def lex_less(p, q) -> bool:
    """Strict lexicographic order on profiles."""
    return p < q


def first_difference(p, q):
    """Index and values of the first coordinate where two profiles differ.

    Returns ``(index, p_value, q_value)`` or ``None`` when the profiles are
    equal.  Used for the contrastive certificate record.
    """
    for i, (a, b) in enumerate(zip(p, q)):
        if a != b:
            return i, a, b
    return None


COORDINATE_NAMES = ("C_M", "C_25", "C_50", "C_100", "T_25", "T_50", "T_100", "M")


def coordinate_name(index: int) -> str:
    """Human-readable name of profile coordinate ``index``."""
    if index < len(COORDINATE_NAMES):
        return COORDINATE_NAMES[index]
    return f"D_({index - len(COORDINATE_NAMES) + 1})"
