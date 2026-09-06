"""The three frozen rational examples behind the theory section.

Each candidate matrix is given as integer numerators over the fixed denominator
64, so every entry is an exact rational *and* an exactly representable binary64
number.  Nothing here depends on a random seed: the matrices are literals, and
each example ships a checker that recomputes its defining property.

Each property is stated at the *root box*.  None of them depends on a branching
budget, so none of them can be explained away as a search that ran out of time.
"""
from __future__ import annotations

import numpy as np

DENOMINATOR = 64
RESOLUTION = "0.02"


def _matrix(numerators) -> np.ndarray:
    return np.asarray(numerators, dtype=float) / DENOMINATOR


# ---------------------------------------------------------------------------
# E-A  invariant boundary coordinate
# ---------------------------------------------------------------------------
#: Five candidates, four criteria.  At p = 0.01 every one of the five candidates
#: changes at least one categorical coordinate between the lower and the upper
#: enclosure, so the all-candidate retention gate refuses the root box outright.
#: The decision-focused test nevertheless certifies candidate 4 against all four
#: rivals on that same box, with no branching at all.  The global margin is zero
#: and the recommendation is certain: the two questions are simply different.
BOUNDARY = {
    "numerators": [
        [52, 29, 33, 46],
        [19, 50, 21, 17],
        [57, 60, 20, 13],
        [22, 30, 44, 56],
        [31, 35, 14, 13],
    ],
    "level": 0.01,
    "winner": 4,
}

# ---------------------------------------------------------------------------
# E-B  cancellation-induced interval slack
# ---------------------------------------------------------------------------
#: Four candidates, three criteria.  At p = 0.05 the dependency-preserving
#: enclosure certifies candidate 0 against every rival on the root box in one
#: box.  The independent-quotient enclosure -- identical in every other respect
#: -- still leaves two thirds of the box volume uncertified after 2,048 boxes.
#: The only difference between the two runs is whether the shared probe anchors
#: q*(b) and q^w(b) stay inside a single quotient.
SLACK = {
    "numerators": [
        [19, 14, 27],
        [22, 2, 23],
        [15, 15, 41],
        [21, 21, 9],
    ],
    "level": 0.05,
    "winner": 0,
}

# ---------------------------------------------------------------------------
# E-C  verified winner switch
# ---------------------------------------------------------------------------
#: Four candidates, three criteria.  Inside B(0.05) there is a bound vector at
#: which the exact rational oracle names candidate 2, not the nominal winner 1,
#: as the unique winner.  That witness is an upper bound on the decision radius;
#: the engine certifies a strictly smaller radius from below.  Together they
#: bracket rho*, which is what an honest anytime certificate should return.
SWITCH = {
    "numerators": [
        [61, 14, 9],
        [23, 27, 47],
        [2, 15, 58],
        [14, 52, 9],
    ],
    "witness_level": 0.05,
    "witness_ideal": [0.07734375, 0.2484375, 0.17890625],
    "witness_nadir": [0.90703125, 0.7828125, 0.94453125],
    "nominal_winner": 1,
    "witness_winner": 2,
}

EXAMPLES = {"boundary": BOUNDARY, "slack": SLACK, "switch": SWITCH}


def matrix(name: str) -> np.ndarray:
    """Candidate matrix of one frozen example."""
    return _matrix(EXAMPLES[name]["numerators"])


# ---------------------------------------------------------------------------
# checkers
# ---------------------------------------------------------------------------
def check_boundary() -> dict:
    """Recompute E-A: retention gate blocked, decision test already certified."""
    from .enclosure import box_from_level, canonical_probes, d_enclosure, to_rational
    from .profile import profile

    F = matrix("boundary")
    m = F.shape[1]
    probes = canonical_probes(m)
    box = box_from_level(F, BOUNDARY["level"])
    D_lo, D_hi = d_enclosure(F, probes, box, mode="joint")
    lo_rows, hi_rows = to_rational(D_lo), to_rational(D_hi)
    leaving = [
        y
        for y in range(F.shape[0])
        if profile(lo_rows[y], RESOLUTION)[:4] != profile(hi_rows[y], RESOLUTION)[:4]
    ]
    w = BOUNDARY["winner"]
    psi_win = profile(hi_rows[w], RESOLUTION)
    certified = all(
        psi_win < profile(lo_rows[y], RESOLUTION)
        for y in range(F.shape[0])
        if y != w
    )
    return {
        "candidates_leaving_cells": leaving,
        "global_gate_passes": not leaving,
        "decision_gate_certifies_root": certified,
    }


def check_slack(budget: int = 2048) -> dict:
    """Recompute E-B: joint certifies the root box, independent does not."""
    from .certify import certify_winner
    from .enclosure import box_from_level, canonical_probes

    F = matrix("slack")
    probes = canonical_probes(F.shape[1])
    box = box_from_level(F, SLACK["level"])
    w = SLACK["winner"]
    out = {}
    for mode in ("joint", "independent"):
        c = certify_winner(
            F, probes, box, w, mode=mode, resolutions=RESOLUTION, max_boxes=budget
        )
        out[mode] = {
            "certified": bool(c.certified),
            "boxes": c.n_boxes,
            "certified_volume": c.certified_volume,
        }
    return out


def check_switch(budget: int = 512) -> dict:
    """Recompute E-C: the witness is real and the certified radius sits below it."""
    from . import oracle
    from .certify import certified_radius

    F = matrix("switch")
    probes = canonical_probes_for(F)
    nominal = oracle.winner(F, probes, F.min(axis=0), F.max(axis=0), RESOLUTION)
    witness_class = oracle.winner_class(
        F,
        probes,
        np.array(SWITCH["witness_ideal"]),
        np.array(SWITCH["witness_nadir"]),
        RESOLUTION,
    )
    rho = certified_radius(
        F, probes, nominal, resolutions=RESOLUTION, max_boxes=budget, p_hi=0.40
    )
    return {
        "nominal_winner": nominal,
        "witness_winner_class": witness_class,
        "witness_level": SWITCH["witness_level"],
        "certified_radius_lower": rho,
        "bracket_is_valid": rho <= SWITCH["witness_level"],
    }


def canonical_probes_for(F) -> list:
    from .enclosure import canonical_probes

    return canonical_probes(np.asarray(F).shape[1])
