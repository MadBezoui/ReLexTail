"""Search for the three rational examples the theory section relies on.

Each phenomenon is characterised *at the root box*, with no branch-and-bound
budget anywhere in the statement.  A budget-dependent example would only show
that a search ran out of time; a root-box example shows a property of the
certification condition itself.

E-A  invariant boundary coordinate
     At the root box, some candidate's categorical coordinates differ between
     the lower and the upper enclosure, so the all-candidate retention gate
     refuses the box outright -- while the decision-focused test already
     certifies the winner against every rival on that same box.  The global
     margin is zero and the decision is nevertheless certain.

E-B  cancellation-induced interval slack
     At the root box, the dependency-preserving enclosure certifies the winner
     against every rival and the independent-quotient enclosure does not.  The
     two differ only in whether the shared probe anchors are kept inside a
     single quotient, so the gap is attributable to that alone.

E-C  verified winner switch
     A bound vector inside B(p) at which the exact rational oracle names a
     different unique winner, together with a certified lower radius strictly
     below p: a genuine two-sided bracket on the decision radius.

Run once.  The instances found are frozen as integer literals in
``enhanced/src/certrelex/examples.py``.
"""
from __future__ import annotations

import json
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from certrelex import oracle  # noqa: E402
from certrelex.certify import certify_winner  # noqa: E402
from certrelex.enclosure import (  # noqa: E402
    box_from_level,
    canonical_probes,
    d_enclosure,
    to_rational,
)
from certrelex.profile import profile  # noqa: E402

RES = "0.02"
DEN = 64  # criterion values are k/64: exactly representable and rational


def rational_matrix(rng, n, m):
    return rng.integers(1, DEN, size=(n, m)).astype(float) / DEN


def _root_report(F, probes, p, winner):
    """Root-box status of both gates and both enclosure modes."""
    box = box_from_level(F, p)
    out = {}
    for mode in ("independent", "joint"):
        enc = d_enclosure(F, probes, box, mode=mode)
        if enc is None:
            out[mode] = None
            continue
        D_lo, D_hi = enc
        lo_rows, hi_rows = to_rational(D_lo), to_rational(D_hi)
        psi_win = profile(hi_rows[winner], RES)
        beats_all = all(
            psi_win < profile(lo_rows[y], RES)
            for y in range(len(lo_rows))
            if y != winner
        )
        moving = [
            y
            for y in range(len(lo_rows))
            if profile(lo_rows[y], RES)[:4] != profile(hi_rows[y], RES)[:4]
        ]
        out[mode] = {"certifies_root": beats_all, "candidates_leaving_cells": moving}
    return box, out


def search_boundary_case(rng, tries=20000):
    """E-A: retention gate blocked at the root, decision test already certified."""
    for _ in range(tries):
        n, m = int(rng.choice([4, 5, 6])), int(rng.choice([3, 4]))
        F = rational_matrix(rng, n, m)
        probes = canonical_probes(m)
        try:
            cls = oracle.winner_class(F, probes, F.min(0), F.max(0), RES)
        except ValueError:
            continue
        if len(cls) != 1:
            continue
        w = cls[0]
        for p in (0.01, 0.02, 0.05):
            _, rep = _root_report(F, probes, p, w)
            j = rep["joint"]
            if j is None or not j["certifies_root"]:
                continue
            if not j["candidates_leaving_cells"]:
                continue
            # the retention gate refuses this root box; confirm the engine
            # cannot recover it quickly either
            glob = certify_winner(F, probes, box_from_level(F, p), w, gate="global",
                                  resolutions=RES, max_boxes=64)
            return dict(
                F=F, p=p, winner=w,
                candidates_leaving_cells=j["candidates_leaving_cells"],
                global_certified_volume_at_64_boxes=glob.certified_volume,
            )
    return None


def search_slack_case(rng, tries=20000):
    """E-B: joint quotient certifies the root box, independent quotient does not."""
    for _ in range(tries):
        n, m = int(rng.choice([4, 5, 6])), int(rng.choice([3, 4]))
        F = rational_matrix(rng, n, m)
        probes = canonical_probes(m)
        try:
            cls = oracle.winner_class(F, probes, F.min(0), F.max(0), RES)
        except ValueError:
            continue
        if len(cls) != 1:
            continue
        w = cls[0]
        for p in (0.02, 0.05, 0.10):
            _, rep = _root_report(F, probes, p, w)
            j, i = rep["joint"], rep["independent"]
            if j is None or i is None:
                continue
            if j["certifies_root"] and not i["certifies_root"]:
                indep = certify_winner(F, probes, box_from_level(F, p), w,
                                       mode="independent", resolutions=RES,
                                       max_boxes=512)
                return dict(
                    F=F, p=p, winner=w,
                    independent_boxes_to_certify=indep.n_boxes,
                    independent_certified_at_512=bool(indep.certified),
                )
    return None


def search_switch_case(rng, tries=20000, draws=256):
    """E-C: a verified unique switch above a certified lower radius."""
    for _ in range(tries):
        n, m = int(rng.choice([4, 5])), 3
        F = rational_matrix(rng, n, m)
        probes = canonical_probes(m)
        try:
            cls = oracle.winner_class(F, probes, F.min(0), F.max(0), RES)
        except ValueError:
            continue
        if len(cls) != 1:
            continue
        w = cls[0]
        level, wit = oracle.witness_radius(
            F, probes, w, resolutions=RES, grid=(0.02, 0.05, 0.10),
            draws=draws, seed=7,
        )
        if wit is None or not wit["unique"]:
            continue
        lower = certify_winner(F, probes, box_from_level(F, level / 4), w,
                               resolutions=RES, max_boxes=512)
        if lower.certified:
            return dict(F=F, winner=w, witness_level=level, witness=wit,
                        certified_level=level / 4)
    return None


def _freeze(F):
    num = np.rint(np.asarray(F) * DEN).astype(int)
    assert np.all(np.asarray(num, dtype=float) / DEN == np.asarray(F))
    assert all(
        Fraction(int(a), DEN) == Fraction(float(b))
        for a, b in zip(num.ravel(), np.asarray(F).ravel())
    )
    return num.tolist()


def main() -> int:
    rng = np.random.default_rng(20260906)
    out = {"denominator": DEN, "resolution": RES}
    for key, fn in (
        ("boundary", search_boundary_case),
        ("slack", search_slack_case),
        ("switch", search_switch_case),
    ):
        found = fn(rng)
        if found is None:
            print(f"{key}: NOT FOUND", flush=True)
            out[key] = None
            continue
        rec = {k: v for k, v in found.items() if k != "F"}
        rec["numerators"] = _freeze(found["F"])
        out[key] = rec
        print(f"{key}: {json.dumps(rec, default=str)}", flush=True)
    dest = ROOT / "data" / "processed" / "examples_search.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2, default=str))
    print("written", dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
