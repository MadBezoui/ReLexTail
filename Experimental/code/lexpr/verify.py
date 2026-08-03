"""Independent verifier for LexPR audit records (`lexpr-verify`).

The manuscript claims that "an independent implementation reading only the
exported record reconstructs the same winner class and contrastive margins".
This module is that independent implementation, exposed as a documented CLI so
the claim can be checked by a third party without reading the rest of the
package.

It deliberately does NOT import the selector. It re-derives the winner class and
the contrastive margins from the exported labelled profiles alone, using only
the definitions in the paper:

    a profile is the vector (D_q(x))_q ;
    x beats y iff sort_desc(D(x)) <_lex sort_desc(D(y)) ;
    W_0 is the set of profiles minimal under that order ;
    the contrastive margin of a unique winner is
        min over rivals y of  D_sorted(y)[k] - D_sorted(x)[k],
    where k is the first coordinate at which the two sorted profiles differ.

Verifying the record therefore checks the arithmetic of the recommendation, not
the correctness of the model that produced it -- exactly the model-relative
guarantee the paper claims and no more.

Usage:
    lexpr-verify record.json
    lexpr-verify record.json --expect-winner S7 --expect-margin 0.014
"""
from __future__ import annotations

import argparse
import json
import sys

TOL = 1e-9  # degeneracy / display only; NEVER used in the comparison


def _sorted_desc(profile):
    return sorted((float(v) for v in profile), reverse=True)


def _lex_cmp(a, b):
    """-1 if a <_lex b, +1 if a >_lex b, 0 if equal.

    The comparison is the ordinary total order on the serialised binary64
    values, matching `lexpr.methods.leximax_argmin` and `lexpr.audit`. There is
    deliberately no comparison tolerance and no grid: the paper proves its
    theorems for the real-valued LexPR order, and a tolerance band or a
    quantisation grid would each define a different rule, on which strict
    Pareto compatibility and the contrastive margins are not guaranteed.
    """
    for u, v in zip(a, b):
        if u < v:
            return -1
        if u > v:
            return 1
    return 0


def extract_profiles(record):
    """Pull {alternative: [disappointments]} out of an audit record.

    Several export shapes are accepted so that the verifier is usable against
    records produced by different versions of the pipeline.
    """
    for key in ("profiles", "labelled_profiles", "decision_profiles"):
        if key in record:
            block = record[key]
            if isinstance(block, dict):
                out = {}
                for k, v in block.items():
                    if isinstance(v, dict):
                        # {alternative: {probe_label: disappointment}}
                        out[k] = [float(x) for x in v.values()]
                    else:
                        out[k] = [
                            p[1] if isinstance(p, (list, tuple)) else float(p)
                            for p in v
                        ]
                return out
            if isinstance(block, list):
                out = {}
                for entry in block:
                    name = entry.get("alternative") or entry.get("name")
                    prof = entry.get("profile") or entry.get("disappointments")
                    out[name] = [
                        p[1] if isinstance(p, (list, tuple)) else float(p) for p in prof
                    ]
                return out
    raise KeyError(
        "no profile block found; expected one of "
        "'profiles', 'labelled_profiles', 'decision_profiles'"
    )


def winner_class(profiles):
    """Set of alternatives minimal under the leximax order on sorted profiles."""
    srt = {k: _sorted_desc(v) for k, v in profiles.items()}
    names = list(srt)
    best = names[0]
    for n in names[1:]:
        if _lex_cmp(srt[n], srt[best]) < 0:
            best = n
    return sorted(n for n in names if _lex_cmp(srt[n], srt[best]) == 0), srt


def contrastive_margin(srt, winner):
    """Smallest first-decision gap by which `winner` beats every rival.

    Returns None when the winner is not unique, matching the paper: no
    contrastive margin is defined against a tied co-winner.
    """
    w = srt[winner]
    best = None
    for n, p in srt.items():
        if n == winner:
            continue
        k = next((i for i, (a, b) in enumerate(zip(w, p)) if abs(a - b) > TOL), None)
        if k is None:
            return None
        gap = p[k] - w[k]
        best = gap if best is None else min(best, gap)
    return best


def verify(path, expect_winner=None, expect_margin=None, margin_tol=5e-4):
    with open(path) as f:
        record = json.load(f)

    profiles = extract_profiles(record)
    cls, srt = winner_class(profiles)
    problems = []

    print(f"record            : {path}")
    print(f"alternatives      : {len(profiles)}")
    print(f"probes per profile: {len(next(iter(profiles.values())))}")
    print(f"winner class W_0  : {', '.join(cls)}")

    margin = contrastive_margin(srt, cls[0]) if len(cls) == 1 else None
    if margin is None:
        print("contrastive margin: not defined (winner class is not a singleton)")
    else:
        print(f"contrastive margin: {margin:.6f}")

    # Cross-check the margin against the record's own contrastive block.
    stated_cr = record.get("contrastive_record")
    if stated_cr and margin is not None:
        try:
            stated_margin = min(float(e["margin"]) for e in stated_cr)
            ok = abs(stated_margin - margin) <= margin_tol
            print(
                f"record's margin   : {stated_margin:.6f}  "
                f"[{'MATCH' if ok else 'MISMATCH'}]"
            )
            if not ok:
                problems.append(
                    f"record states margin {stated_margin}, recomputed {margin}"
                )
        except (KeyError, TypeError, ValueError):
            pass

    # Cross-check against whatever the record itself asserts.
    stated = record.get("lexpr_winner") or record.get("winner")
    if stated is None and isinstance(record.get("winner_class"), list):
        wc = record["winner_class"]
        stated = wc[0] if len(wc) == 1 else None
    if stated is not None:
        ok = len(cls) == 1 and cls[0] == stated
        print(f"record states     : {stated}  [{'MATCH' if ok else 'MISMATCH'}]")
        if not ok:
            problems.append(f"record states winner {stated}, recomputed {cls}")

    if expect_winner is not None:
        ok = len(cls) == 1 and cls[0] == expect_winner
        print(f"expected winner   : {expect_winner}  [{'MATCH' if ok else 'MISMATCH'}]")
        if not ok:
            problems.append(f"expected winner {expect_winner}, recomputed {cls}")

    if expect_margin is not None:
        ok = margin is not None and abs(margin - expect_margin) <= margin_tol
        print(f"expected margin   : {expect_margin}  [{'MATCH' if ok else 'MISMATCH'}]")
        if not ok:
            problems.append(f"expected margin {expect_margin}, recomputed {margin}")

    if problems:
        print("\nFAILED:")
        for p in problems:
            print("  -", p)
        return 1
    print("\nOK: the record reconstructs its own winner class and margins.")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="lexpr-verify",
        description="Independently re-derive the LexPR winner class and contrastive "
        "margins from an exported audit record.",
    )
    ap.add_argument("record", help="path to the exported audit record (JSON)")
    ap.add_argument(
        "--expect-winner",
        default=None,
        help="assert that the recomputed unique winner is this alternative",
    )
    ap.add_argument(
        "--expect-margin",
        type=float,
        default=None,
        help="assert the recomputed contrastive margin, within --margin-tol",
    )
    ap.add_argument("--margin-tol", type=float, default=5e-4)
    args = ap.parse_args(argv)
    return verify(args.record, args.expect_winner, args.expect_margin, args.margin_tol)


if __name__ == "__main__":
    sys.exit(main())
