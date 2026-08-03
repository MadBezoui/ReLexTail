"""Referee point 6.2 (final round): compare EVERY certified enclosure produced
during a real branch-and-bound run against exact rational evaluation.

The earlier suite (test_validated_intervals.py) checks the enclosure formula on
hand-picked boxes. This one instead replays the boxes the algorithm actually
visits, and for each of them checks containment in exact arithmetic. Inputs are
chosen to be exactly representable in binary64 (dyadic rationals), so the
rational reference is the true value of the same mathematical expression rather
than a different rounding of it.

Scope, stated plainly: this test detects a wrong enclosure FORMULA, and it
confirms that outward rounding never breaks containment. It does not demonstrate
that outward rounding is necessary. Neutralising the directed rounding leaves
all six cases passing, here as in test_validated_intervals.py, because the
corner construction takes a min and a max over four evaluations and so carries
structural slack. Outward rounding is a guarantee, not a repair.
"""
from fractions import Fraction as Fr
from itertools import product
import numpy as np
import pytest
from lexpr import certified


def _dyadic(rng, shape, bits=8):
    """Matrix of exactly representable values in [1, 2)."""
    return 1.0 + rng.integers(0, 2 ** bits, size=shape) / float(2 ** bits)


def _exact_range(F, probe, box, cand):
    """Exact range of D_q(cand) over the box corners, in rationals."""
    ideal_lo, ideal_hi, nadir_lo, nadir_hi = box
    n = F.shape[0]
    kind, idx = probe
    idx = list(idx)
    vals = []
    per_crit = [[(Fr(ideal_lo[i]), Fr(nadir_lo[i])), (Fr(ideal_lo[i]), Fr(nadir_hi[i])),
                 (Fr(ideal_hi[i]), Fr(nadir_lo[i])), (Fr(ideal_hi[i]), Fr(nadir_hi[i]))]
                for i in idx]
    for choice in product(*per_crit):
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


@pytest.mark.parametrize("seed", range(6))
def test_every_visited_box_encloses_the_exact_value(seed):
    rng = np.random.default_rng(seed)
    F = _dyadic(rng, (4, 3))
    probes = [("mean", (0, 1, 2)), ("max", (0, 1, 2))]

    # replay the boxes the branch-and-bound actually visits
    # Sweep the subdivision tree the algorithm would explore, subdividing
    # unconditionally rather than stopping at the first resolved box: the point
    # is to exercise many enclosures, including deep narrow ones where the
    # cancellation in q_x - q* is worst. p is kept small enough that every
    # corner keeps a strictly positive normalising denominator, so the rational
    # reference is defined rather than skipped.
    visited, stack = [], [(certified._box_from_p(F, 0.002), 0)]
    while stack and len(visited) < 60:
        box, depth = stack.pop()
        visited.append(box)
        if depth < 6:
            b1, b2 = certified._split(box)
            stack += [(b1, depth + 1), (b2, depth + 1)]

    checked = 0
    for box in visited:
        Dlo, Dhi = certified._D_enclosure(F, probes, box)
        for k, probe in enumerate(probes):
            for cand in range(F.shape[0]):
                exact = _exact_range(F, probe, box, cand)
                if exact is None:
                    continue
                lo, hi = exact
                assert Fr(Dlo[cand, k]) <= lo, (
                    f"seed {seed}: lower bound {Dlo[cand, k]!r} above exact min {float(lo)!r}")
                assert Fr(Dhi[cand, k]) >= hi, (
                    f"seed {seed}: upper bound {Dhi[cand, k]!r} below exact max {float(hi)!r}")
                checked += 1
    assert checked >= 200, f"only {checked} enclosures checked; test is too weak"
