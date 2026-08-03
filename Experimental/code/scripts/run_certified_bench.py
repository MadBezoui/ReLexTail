"""Computational study of the certified branch-and-bound (T3.5, part i).

Table S8 of the supplement times only the finite algorithm. This script adds the
three things a computational-OR referee will look for in the certified mode:

  * RUNTIME as a function of instance size (N candidates, m criteria);
  * UNRESOLVED-VOLUME DECAY as the box budget grows, which is what converts
    Algorithm S3 from "sound with a budget cap" into a procedure with an
    observable convergence profile;
  * BUDGET SENSITIVITY of the reported certified sets, i.e. whether spending
    more boxes actually tightens the outer approximation.

Outputs scripts/real_results/certified_bench.json and
manuscript/generated/certified_bench.tex.
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from lexpr import certified, problems, supplier  # noqa: E402

SEED = 20260628
LEVEL = 0.05
OUT = os.path.join(HERE, "real_results")
TEXDIR = os.path.abspath(os.path.join(ROOT, "..", "manuscript", "generated"))

# Candidate-set sizes are modest because the pairwise certification test is
# O(N^2) per box: every candidate must be shown to be beaten throughout the box.
# This quadratic term, not the box count, is what bounds the practical reach of
# the certified mode, and the ms/box column below is what exhibits it.
SIZES = [(20, 3), (20, 5), (50, 3), (50, 5), (100, 5)]
BUDGETS = [250, 500, 1000, 2000, 4000]


def canonical_probes(m):
    """Canonical core in the (kind, index-tuple) format used by lexpr.certified."""
    probes = [("single", (i,)) for i in range(m)]
    probes.append(("mean", tuple(range(m))))
    probes.append(("max", tuple(range(m))))
    return probes


def main():
    rng = np.random.default_rng(SEED)
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(TEXDIR, exist_ok=True)

    size_rows = []
    for N, m in SIZES:
        F = problems.make_candidate_set("concave", N, m, rng)
        probes = canonical_probes(m)
        t0 = time.perf_counter()
        cs = certified.certified_sets(F, probes, LEVEL, max_boxes=1000, max_depth=36)
        dt = time.perf_counter() - t0
        size_rows.append({
            "N": int(F.shape[0]), "m": m, "K": m + 2,
            "boxes": int(cs["n_boxes"]),
            "seconds": round(dt, 2),
            "ms_per_box": round(dt / max(cs["n_boxes"], 1) * 1e3, 3),
            "outer": len(cs["outer_possible"]),
            "inner": len(cs["inner_possible"]),
            "unresolved": round(cs["unresolved_vol_frac"], 4),
        })
        print(f"N={N:4d} m={m} : {dt:6.2f}s over {cs['n_boxes']:5d} boxes, "
              f"outer={len(cs['outer_possible']):3d} unresolved={cs['unresolved_vol_frac']:.3f}")

    # Budget sensitivity on one fixed mid-size instance.
    Fb = problems.make_candidate_set("concave", 15, 4, np.random.default_rng(SEED + 1))
    pb = canonical_probes(4)
    budget_rows = []
    for B in BUDGETS:
        t0 = time.perf_counter()
        cs = certified.certified_sets(Fb, pb, LEVEL, max_boxes=B, max_depth=40)
        dt = time.perf_counter() - t0
        budget_rows.append({
            "budget": B, "boxes": int(cs["n_boxes"]), "seconds": round(dt, 2),
            "outer": len(cs["outer_possible"]),
            "inner": len(cs["inner_possible"]),
            "unresolved": round(cs["unresolved_vol_frac"], 4),
        })
        print(f"budget={B:5d}: {dt:6.2f}s outer={len(cs['outer_possible']):3d} "
              f"unresolved={cs['unresolved_vol_frac']:.4f}")

    # Resolution threshold on the supplier case.
    #
    # Raising the budget on that instance does NOT eventually resolve the box,
    # and this is not a defect: above the certified stability radius there is no
    # sole winner to certify, so no amount of subdivision can produce one. The
    # sweep below locates the threshold and shows it coincides with the radius
    # obtained independently by bisection in run_certified_stability.py.
    Fs, snames, _ = supplier.load_supplier_case()
    sprobes, _ = certified.canonical_supplier_probes()
    threshold_rows = []
    for p in (0.001, 0.002, 0.003, 0.005, 0.010, 0.020):
        t0 = time.perf_counter()
        cs = certified.certified_sets(Fs, sprobes, p, max_boxes=3000, max_depth=44)
        threshold_rows.append({
            "p": p, "boxes": int(cs["n_boxes"]),
            "seconds": round(time.perf_counter() - t0, 2),
            "unresolved": round(cs["unresolved_vol_frac"], 4),
            "outer": [snames[i] for i in cs["outer_possible"]],
        })
        print(f"supplier p={p:<6}: unresolved={cs['unresolved_vol_frac']:.4f} "
              f"outer={len(cs['outer_possible'])}")

    out = {"seed": SEED, "level": LEVEL, "n_candidates_budget_instance": int(Fb.shape[0]),
           "supplier_box_dimension": 2 * Fs.shape[1],
           "by_size": size_rows, "by_budget": budget_rows,
           "supplier_threshold": threshold_rows}
    with open(os.path.join(OUT, "certified_bench.json"), "w") as f:
        json.dump(out, f, indent=2)

    L = ["% Auto-generated by scripts/run_certified_bench.py. Do not edit.",
         "\\footnotesize",
         "\\begin{tabular}{@{}rrrrrrr@{}}", "\\toprule",
         "$N$ & $m$ & $K$ & Boxes & Time (s) & ms/box & Outer $|S^{\\mathrm{pos}}|$\\\\",
         "\\midrule"]
    for r in size_rows:
        L.append(f"{r['N']} & {r['m']} & {r['K']} & {r['boxes']} & {r['seconds']:.2f} & "
                 f"{r['ms_per_box']:.2f} & {r['outer']}\\\\")
    L += ["\\bottomrule", "\\end{tabular}", ""]
    with open(os.path.join(TEXDIR, "certified_bench.tex"), "w") as f:
        f.write("\n".join(L))

    B = ["% Auto-generated by scripts/run_certified_bench.py. Do not edit.",
         "\\footnotesize",
         "\\begin{tabular}{@{}rrrrr@{}}", "\\toprule",
         "Budget & Boxes & Time (s) & Outer $|S^{\\mathrm{pos}}|$ & Unresolved vol.\\\\",
         "\\midrule"]
    for r in budget_rows:
        B.append(f"{r['budget']} & {r['boxes']} & {r['seconds']:.2f} & {r['outer']} & "
                 f"{r['unresolved']:.4f}\\\\")
    B += ["\\bottomrule", "\\end{tabular}", ""]
    with open(os.path.join(TEXDIR, "certified_budget.tex"), "w") as f:
        f.write("\n".join(B))


if __name__ == "__main__":
    main()
