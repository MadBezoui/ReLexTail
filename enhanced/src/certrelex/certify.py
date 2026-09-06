"""Decision-focused certification of a ReLexTail recommendation.

What is certified
-----------------
For a candidate set ``A``, a retained probe multiset ``Q``, a resolution vector
``delta`` and a box ``beta`` of admissible normalisation bounds, the decision
region of a nominal winner ``x0`` is

    R(x0) = { b in beta : Psi(x0; b) <_lex Psi(y; b) for every y != x0 }.

The engine returns a certified *inner* region for ``R(x0)``: a set of sub-boxes
on which ``x0`` provably beats every rival, together with the explicitly
recorded leaves it could not resolve.  Nothing else about the profile has to
stay put.  Categories of irrelevant alternatives may change, boundary
coordinates may move, and coordinates occurring after an already decisive
comparison are never examined.

Two gates
---------
``gate="global"``
    The condition used by the current submission engine: refuse the box unless
    *every* candidate keeps *all four* categorical coordinates fixed across the
    enclosure.  It is sufficient but not necessary, and it fails for reasons
    that have nothing to do with the decision -- an irrelevant alternative
    sitting on a cell boundary is enough.

``gate="decision"``
    The enhanced condition: require only ``Psi(D_hi(x0)) <_lex Psi(D_lo(y))``
    for each rival ``y``.  Proposition 1 below shows this is sound on its own,
    so the global gate can only certify a subset of what this gate certifies.

Soundness (Proposition 1).  Suppose ``D_lo <= D(.; b) <= D_hi`` componentwise
for every ``b`` in the box.  Every coordinate of ``Psi`` is nondecreasing in
``D`` componentwise, so ``Psi(D(x0; b)) <= Psi(D_hi(x0))`` and
``Psi(D_lo(y)) <= Psi(D(y; b))`` componentwise, hence also in ``<=_lex``.  If
``Psi(D_hi(x0)) <_lex Psi(D_lo(y))`` then, by transitivity of the total
lexicographic order,

    Psi(x0; b) <=_lex Psi(D_hi(x0)) <_lex Psi(D_lo(y)) <=_lex Psi(y; b)

for every ``b`` in the box.  No retention of categories is used anywhere in
this chain.  The comparison itself is carried out in exact rational arithmetic
on the outward-rounded binary64 endpoints, so no tie tolerance enters.

Anytime validity.  Certified leaves are never revisited and unresolved leaves
are always retained with their volume, so an interrupted run returns a valid
certified region and a valid uncertified-volume bound; continuing the run can
only move volume from the second set into the first.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from .enclosure import d_enclosure, box_from_level, to_rational
from .profile import first_difference, profile

MAX_DEPTH = 60


@dataclass
class DecisiveRecord:
    """Contrastive record of one certified pairwise comparison."""

    rival: int
    depth: int
    coordinate: int
    winner_value: str
    rival_value: str


@dataclass
class WinnerCertificate:
    """Result of a decision-focused certification run."""

    winner: int
    gate: str
    mode: str
    split: str
    certified: bool
    certified_volume: float
    unresolved_volume: float
    n_boxes: int
    max_depth_reached: int
    seconds: float
    budget_exhausted: bool
    unresolved_rivals: set = field(default_factory=set)
    records: list = field(default_factory=list)
    certified_leaves: list = field(default_factory=list)
    unresolved_leaves: list = field(default_factory=list)

    def as_row(self) -> dict:
        return {
            "winner": self.winner,
            "gate": self.gate,
            "mode": self.mode,
            "split": self.split,
            "certified": bool(self.certified),
            "certified_volume": self.certified_volume,
            "unresolved_volume": self.unresolved_volume,
            "n_boxes": self.n_boxes,
            "max_depth_reached": self.max_depth_reached,
            "seconds": self.seconds,
            "budget_exhausted": bool(self.budget_exhausted),
            "n_unresolved_rivals": len(self.unresolved_rivals),
        }


# --------------------------------------------------------------------------
# branching
# --------------------------------------------------------------------------
def _split_widest(F, box, active):
    """Baseline rule: bisect the widest bound coordinate of the box."""
    ideal_lo, ideal_hi, nadir_lo, nadir_hi = box
    widths = np.concatenate([ideal_hi - ideal_lo, nadir_hi - nadir_lo])
    return _bisect(box, int(np.argmax(widths)))


def _split_decision(F, box, active):
    """Decision-relevant rule: bisect the bound coordinate that carries the
    most enclosure width for the candidates still involved in an unresolved
    comparison.

    ``r_j`` is the only channel through which ``(I_j, N_j)`` reaches an
    aggregate probe, so the width of ``r_j`` over the active candidates
    measures how much that pair of bound coordinates can still move the
    decisive comparison.  Criteria that only feed singleton probes contribute
    nothing, because those coordinates cancel exactly.  The rule is a heuristic
    and changes only *where* effort goes; soundness is unaffected.
    """
    from .enclosure import r_enclosure

    ideal_lo, ideal_hi, nadir_lo, nadir_hi = box
    m = ideal_lo.size
    try:
        r_lo, r_hi = r_enclosure(F, box)
    except (ValueError, FloatingPointError):
        return _split_widest(F, box, active)
    rows = sorted(active) if active else list(range(F.shape[0]))
    influence = (r_hi[rows] - r_lo[rows]).max(axis=0)
    j = int(np.argmax(influence))
    # split whichever of the two bound coordinates of criterion j is wider
    if (ideal_hi[j] - ideal_lo[j]) >= (nadir_hi[j] - nadir_lo[j]):
        return _bisect(box, j)
    return _bisect(box, m + j)


def _bisect(box, k):
    ideal_lo, ideal_hi, nadir_lo, nadir_hi = box
    m = ideal_lo.size
    b1 = [np.array(a, copy=True) for a in box]
    b2 = [np.array(a, copy=True) for a in box]
    if k < m:
        mid = 0.5 * (ideal_lo[k] + ideal_hi[k])
        b1[1][k] = mid
        b2[0][k] = mid
    else:
        j = k - m
        mid = 0.5 * (nadir_lo[j] + nadir_hi[j])
        b1[3][j] = mid
        b2[2][j] = mid
    return tuple(b1), tuple(b2)


_SPLITTERS = {"widest": _split_widest, "decision": _split_decision}


# --------------------------------------------------------------------------
# gates
# --------------------------------------------------------------------------
def _global_gate_passes(D_lo, D_hi, resolutions) -> bool:
    """All-candidate uniform categorical retention (the conservative gate)."""
    lo_rows = to_rational(D_lo)
    hi_rows = to_rational(D_hi)
    for lo_row, hi_row in zip(lo_rows, hi_rows):
        if profile(lo_row, resolutions)[:4] != profile(hi_row, resolutions)[:4]:
            return False
    return True


# --------------------------------------------------------------------------
# main entry point
# --------------------------------------------------------------------------
def certify_winner(
    F,
    probes,
    box,
    winner: int,
    *,
    mode: str = "joint",
    gate: str = "decision",
    split: str = "decision",
    resolutions=None,
    max_boxes: int = 4096,
    max_depth: int = MAX_DEPTH,
    time_limit: Optional[float] = None,
    collect_records: bool = False,
    record_leaves: int = 0,
) -> WinnerCertificate:
    """Certify that ``winner`` is the unique ReLexTail winner throughout ``box``.

    The run is anytime: it stops at ``max_boxes`` processed boxes or at
    ``time_limit`` seconds and reports the certified and unresolved volume
    fractions it reached.
    """
    F = np.asarray(F, dtype=float)
    n = F.shape[0]
    rivals0 = frozenset(y for y in range(n) if y != winner)
    splitter = _SPLITTERS[split]
    t0 = time.perf_counter()

    stack = [(tuple(np.asarray(a, dtype=float) for a in box), 0, rivals0, 1.0)]
    certified_vol = 0.0
    unresolved_vol = 0.0
    unresolved_rivals: set = set()
    records: list = []
    certified_leaves: list = []
    unresolved_leaves: list = []
    n_boxes = 0
    depth_reached = 0
    exhausted = False

    while stack:
        if n_boxes >= max_boxes or (
            time_limit is not None and time.perf_counter() - t0 > time_limit
        ):
            exhausted = True
            break
        sub, depth, rivals, vol = stack.pop()
        n_boxes += 1
        depth_reached = max(depth_reached, depth)

        enc = d_enclosure(F, probes, sub, mode=mode)
        remaining = rivals
        if enc is not None:
            D_lo, D_hi = enc
            if gate == "global" and not _global_gate_passes(D_lo, D_hi, resolutions):
                remaining = rivals  # refuse the box wholesale
            else:
                psi_win = profile(to_rational(D_hi)[winner], resolutions)
                still = set()
                for y in rivals:
                    psi_riv = profile(to_rational(D_lo)[y], resolutions)
                    if psi_win < psi_riv:
                        if collect_records:
                            diff = first_difference(psi_win, psi_riv)
                            if diff is not None:
                                idx, wv, rv = diff
                                records.append(
                                    DecisiveRecord(y, depth, idx, str(wv), str(rv))
                                )
                    else:
                        still.add(y)
                remaining = frozenset(still)

        if not remaining:
            certified_vol += vol
            if len(certified_leaves) < record_leaves:
                certified_leaves.append(_leaf(sub, depth, vol))
            continue
        if depth < max_depth:
            b1, b2 = splitter(F, sub, remaining | {winner})
            stack.append((b1, depth + 1, remaining, vol / 2))
            stack.append((b2, depth + 1, remaining, vol / 2))
        else:
            unresolved_vol += vol
            unresolved_rivals |= set(remaining)
            if len(unresolved_leaves) < record_leaves:
                unresolved_leaves.append(_leaf(sub, depth, vol))

    for sub, depth, rivals, vol in stack:
        unresolved_vol += vol
        unresolved_rivals |= set(rivals)
        if len(unresolved_leaves) < record_leaves:
            unresolved_leaves.append(_leaf(sub, depth, vol))

    return WinnerCertificate(
        winner=winner,
        gate=gate,
        mode=mode,
        split=split,
        certified=unresolved_vol <= 0.0,
        certified_volume=certified_vol,
        unresolved_volume=unresolved_vol,
        n_boxes=n_boxes,
        max_depth_reached=depth_reached,
        seconds=time.perf_counter() - t0,
        budget_exhausted=exhausted,
        unresolved_rivals=unresolved_rivals,
        records=records,
        certified_leaves=certified_leaves,
        unresolved_leaves=unresolved_leaves,
    )


def _leaf(box, depth, vol):
    """Serialisable leaf record: the four bound vectors, its depth and volume."""
    return {
        "ideal_lo": np.asarray(box[0]).tolist(),
        "ideal_hi": np.asarray(box[1]).tolist(),
        "nadir_lo": np.asarray(box[2]).tolist(),
        "nadir_hi": np.asarray(box[3]).tolist(),
        "depth": int(depth),
        "volume": float(vol),
    }


def certified_sets(
    F,
    probes,
    box,
    *,
    mode: str = "joint",
    resolutions=None,
    max_boxes: int = 4096,
    max_depth: int = MAX_DEPTH,
):
    """Certified inner and outer approximations of the possible-winner set.

    Terminal-leaf aggregation: the outer set is the union of the surviving
    candidates of terminal leaves only, so refinement can only tighten it.
    Elimination is monotone under subdivision, so a parent's survivor set is a
    sound superset for its children and a valid survivor set for any leaf left
    unprocessed when the budget runs out.
    """
    F = np.asarray(F, dtype=float)
    n = F.shape[0]
    stack = [(tuple(np.asarray(a, dtype=float) for a in box), 0, frozenset(range(n)), 1.0)]
    inner, outer = set(), set()
    unresolved_vol = 0.0
    n_boxes = 0
    while stack and n_boxes < max_boxes:
        sub, depth, alive, vol = stack.pop()
        n_boxes += 1
        enc = d_enclosure(F, probes, sub, mode=mode)
        survivors = alive
        if enc is not None:
            D_lo, D_hi = enc
            lo_rows = to_rational(D_lo)
            hi_rows = to_rational(D_hi)
            up_prof = {x: profile(hi_rows[x], resolutions) for x in alive}
            lo_prof = {x: profile(lo_rows[x], resolutions) for x in alive}
            survivors = frozenset(
                y
                for y in alive
                if not any(x != y and up_prof[x] < lo_prof[y] for x in alive)
            )
        if len(survivors) == 1:
            inner |= set(survivors)
            outer |= set(survivors)
        elif depth < max_depth:
            b1, b2 = _split_decision(F, sub, survivors)
            stack.append((b1, depth + 1, survivors, vol / 2))
            stack.append((b2, depth + 1, survivors, vol / 2))
        else:
            outer |= set(survivors)
            unresolved_vol += vol
    for _, _, alive, vol in stack:
        outer |= set(alive)
        unresolved_vol += vol
    return {
        "n_boxes": n_boxes + len(stack),
        "inner_possible": sorted(inner),
        "outer_possible": sorted(outer),
        "unresolved_vol_frac": unresolved_vol,
    }


# --------------------------------------------------------------------------
# radius bracket
# --------------------------------------------------------------------------
def certified_radius(
    F,
    probes,
    winner: int,
    *,
    mode: str = "joint",
    gate: str = "decision",
    split: str = "decision",
    resolutions=None,
    p_hi: float = 0.45,
    tol: float = 1e-3,
    max_boxes: int = 4096,
    max_depth: int = MAX_DEPTH,
) -> float:
    """Certified LOWER bound on ``rho*(winner)`` for the nested boxes ``B(p)``.

    Bisection on ``p``.  Because the engine is anytime and one-sided, a
    negative answer at level ``p`` means only "not certified within this
    budget", so the returned value is a lower bound on the true radius and
    never an upper bound.
    """

    def ok(p: float) -> bool:
        if p <= 0.0:
            return True
        cert = certify_winner(
            F,
            probes,
            box_from_level(F, p),
            winner,
            mode=mode,
            gate=gate,
            split=split,
            resolutions=resolutions,
            max_boxes=max_boxes,
            max_depth=max_depth,
        )
        return cert.certified

    if not ok(tol):
        return 0.0
    if ok(p_hi):
        return p_hi
    lo, hi = tol, p_hi
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        if ok(mid):
            lo = mid
        else:
            hi = mid
    return lo
