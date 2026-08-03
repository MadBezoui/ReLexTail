r"""Regression test for referee point 3 (round 2): the certified outer possible
set must be the UNION of surviving candidates over terminal leaves, never a
running global subtraction.

The test is written so that it FAILS if certified_sets is changed to the
erroneous `Out <- Out \ E_beta` aggregation, which would return a set that is
too small and can even be empty.
"""
import numpy as np
import pytest
from lexpr.certified import certified_sets, canonical_supplier_probes, _classify_box, _box_from_p, _split


# Discriminating instance. At p = 0.25 the terminal leaves of the subdivision
# have genuinely different survivor sets: their union is all five candidates
# while their intersection is the single candidate 4. Union and subtraction
# therefore give different answers here, which is what makes the test bite.
SEED, N, M, P = 1, 5, 3, 0.25


def _instance():
    F = np.random.default_rng(SEED).random((N, M))
    return F, [("single", (i,)) for i in range(M)] + [("mean", tuple(range(M))),
                                                      ("max", tuple(range(M)))]


def test_outer_is_the_union_over_terminal_leaves():
    """The headline invariant. Under the erroneous global subtraction the outer
    set collapses towards the intersection of the leaf survivor sets."""
    F, probes = _instance()
    r = certified_sets(F, probes, P, max_boxes=400, max_depth=10)
    outer = set(r["outer_possible"])
    # Rebuild the same subdivision by hand and aggregate both ways.
    leaves, stack, nb = [], [(_box_from_p(F, P), 0, frozenset(range(N)))], 0
    while stack and nb < 400:
        box, d, inherited = stack.pop()
        nb += 1
        sole, not_elim = _classify_box(F, probes, box)
        survivors = frozenset(not_elim) & inherited
        if sole is not None or d >= 10:
            leaves.append(survivors)
        else:
            b1, b2 = _split(box)
            stack += [(b1, d + 1, survivors), (b2, d + 1, survivors)]
    leaves += [inh for _, _, inh in stack]
    union = set().union(*leaves)
    intersection = set(leaves[0]).intersection(*leaves)
    assert union != intersection, "instance no longer discriminates; pick another"
    assert outer == union, f"outer {sorted(outer)} is not the union {sorted(union)}"
    assert outer != intersection, "outer collapsed to the intersection: subtraction bug"


def test_outer_is_superset_of_inner_and_never_empty():
    F, probes = _instance()
    for p in (0.002, 0.02, P):
        r = certified_sets(F, probes, p, max_boxes=400, max_depth=12)
        inner, outer = set(r["inner_possible"]), set(r["outer_possible"])
        assert outer, f"outer set empty at p={p}: subtraction bug"
        assert inner <= outer, f"inner not contained in outer at p={p}"


def test_outer_contains_every_locally_certified_sole_winner():
    """Any candidate that is the certified sole winner on SOME sub-box is a
    genuine possible winner, so it must appear in the outer set. Global
    subtraction can drop it; terminal-leaf union cannot."""
    F, probes = _instance()
    p = P
    r = certified_sets(F, probes, p, max_boxes=800, max_depth=14)
    outer = set(r["outer_possible"])
    # independently re-derive sole winners on a hand-built subdivision
    boxes, stack = [], [(_box_from_p(F, p), 0)]
    while stack and len(boxes) < 200:
        box, d = stack.pop()
        sole, _ = _classify_box(F, probes, box)
        if sole is not None:
            boxes.append(sole)
        elif d < 8:
            b1, b2 = _split(box)
            stack += [(b1, d + 1), (b2, d + 1)]
    for w in set(boxes):
        assert w in outer, f"candidate {w} wins on a sub-box but is absent from outer"


def test_budget_exhaustion_keeps_queued_boxes_sound():
    """With a deliberately tiny budget the queue cannot drain; the leftover
    boxes must still contribute survivors and unresolved volume."""
    F, probes = _instance()
    tight = certified_sets(F, probes, P, max_boxes=3, max_depth=40)
    assert tight["outer_possible"], "queued boxes dropped at budget exhaustion"
    assert tight["unresolved_vol_frac"] > 0, "queued volume not counted as unresolved"
    generous = certified_sets(F, probes, P, max_boxes=4000, max_depth=40)
    assert set(generous["outer_possible"]) <= set(tight["outer_possible"]), \
        "outer approximation must weakly tighten under a larger budget"
