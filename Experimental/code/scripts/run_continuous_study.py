"""Computational study of the front-free continuous formulation (Theorem 9).

Two things are measured, over random linear multiobjective programs
X = {x : A x <= b, 0 <= x <= 1} with affine criteria f = C x and the canonical
probe family Q_can:

  (1) CORRECTNESS.  The sequential scheme of lexpr.continuous is validated
      against dense enumerate-then-select using the SAME anchors (computed over
      X, per Remark 6 of the main text).  The continuous solution's sorted
      disappointment profile must be lexicographically no worse than the best
      profile found by enumerating many weighted-sum optima.

  (2) COST.  LP solver calls and wall-clock time for the direct formulation
      versus enumerate-then-select, with the call count checked against the
      O(Km) accounting of Theorem 9: 2m bound LPs, two per weighted-sum probe
      and |S|+1 per maximum probe for the anchors, and K stage LPs.

Seeded by MASTER_SEED. Outputs scripts/real_results/continuous.json and the
LaTeX table manuscript/generated/continuous_study.tex.
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lexpr import directopt
from lexpr.continuous import continuous_lexpr, make_probes, _disappointments_at

MASTER_SEED = 20260628
OUT = os.path.join(os.path.dirname(__file__), "real_results")
TEX = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "manuscript", "generated")
)
os.makedirs(OUT, exist_ok=True)
os.makedirs(TEX, exist_ok=True)

SIZES = [(3, 6), (4, 8), (5, 10), (6, 12), (8, 16)]  # (m criteria, n variables)
REPS = 10
N_ENUM = 400  # weight draws for the enumerate-then-select baseline


def lex_leq(a, b, tol=1e-7):
    """a <=_lex b on descending-sorted vectors, with numerical tolerance."""
    for u, v in zip(a, b):
        if u < v - tol:
            return True
        if u > v + tol:
            return False
    return True


def enumerate_then_select(C, A, b, rows, qstar, R, n_weights, rng):
    """Generate a weighted-sum front over X, then pick the leximax-best point.

    Uses the anchors already computed over X so that the two procedures are
    compared on the same objective, isolating the cost of avoiding enumeration.
    """
    m, n = C.shape
    bounds = [(0.0, 1.0)] * n
    W = rng.dirichlet(np.ones(m), size=n_weights)
    best_prof, calls = None, 0
    for w in W:
        res = directopt._solve_lp(w @ C, A, b, bounds)
        calls += 1
        d = _disappointments_at(res.x, rows, qstar, R)
        prof = np.sort(d)[::-1]
        if best_prof is None or lex_leq(prof, best_prof):
            best_prof = prof
    return best_prof, calls


def main():
    master = np.random.default_rng(MASTER_SEED)
    records = []

    for m, n in SIZES:
        agree = 0
        direct_calls, enum_calls = [], []
        direct_t, enum_t = [], []
        gaps = []
        expected_calls = None

        for _ in range(REPS):
            rng = np.random.default_rng(int(master.integers(1 << 31)))
            C, A, b = directopt.random_linear_mop(m, n=n, n_constr=max(4, n // 2), rng=rng)

            t0 = time.perf_counter()
            x, info = continuous_lexpr(C, A, b)
            direct_t.append(time.perf_counter() - t0)
            direct_calls.append(info["solver_calls"])

            # Theoretical count: 2m bounds + (2 per sum probe) + (|S|+1 for the
            # single max probe) + K stage LPs.  Q_can has m+1 sum probes and one
            # max probe over all m criteria.
            K_full = m + 2
            expected_calls = 2 * m + 2 * (m + 1) + (m + 1) + K_full

            # rebuild the retained-probe representation for the baseline
            probes = make_probes(m)
            bounds = [(0.0, 1.0)] * n
            ctr = directopt  # only for _solve_lp
            from lexpr.continuous import (
                SolverCounter,
                _anchors,
                _criterion_bounds,
                _probe_rows,
            )

            c2 = SolverCounter()
            f_lo, f_hi = _criterion_bounds(C, A, b, bounds, c2)
            rng_obj = np.maximum(f_hi - f_lo, 1e-9)
            rows = _probe_rows(probes, C, f_lo, rng_obj)
            qs, qw = _anchors(rows, A, b, bounds, c2)
            Rr = qw - qs
            keep = [k for k in range(len(rows)) if Rr[k] > 1e-9]
            rows = [rows[k] for k in keep]
            qs, Rr = qs[keep], Rr[keep]

            t0 = time.perf_counter()
            prof_enum, calls_e = enumerate_then_select(
                C, A, b, rows, qs, Rr, N_ENUM, np.random.default_rng(0)
            )
            enum_t.append(time.perf_counter() - t0)
            enum_calls.append(calls_e + c2.calls)

            prof_dir = info["profile_sorted"]
            L = min(len(prof_dir), len(prof_enum))
            if lex_leq(prof_dir[:L], prof_enum[:L]):
                agree += 1
            gaps.append(float(prof_enum[0] - prof_dir[0]))

        records.append(
            {
                "m": m,
                "n": n,
                "K": m + 2,
                "reps": REPS,
                "direct_lp_calls": int(np.median(direct_calls)),
                "direct_lp_calls_predicted": int(expected_calls),
                "enum_lp_calls": int(np.median(enum_calls)),
                "direct_ms": round(float(np.median(direct_t)) * 1e3, 1),
                "enum_ms": round(float(np.median(enum_t)) * 1e3, 1),
                "direct_no_worse_frac": agree / REPS,
                "worst_coord_gap_mean": round(float(np.mean(gaps)), 5),
            }
        )
        r = records[-1]
        print(
            f"m={m:2d} n={n:2d} K={r['K']:2d} | direct {r['direct_lp_calls']:3d} LPs "
            f"(predicted {r['direct_lp_calls_predicted']:3d}), {r['direct_ms']:7.1f} ms"
            f" | enumerate {r['enum_lp_calls']:4d} LPs, {r['enum_ms']:8.1f} ms"
            f" | direct no worse in {r['direct_no_worse_frac']*100:.0f}% of reps"
        )

    with open(os.path.join(OUT, "continuous.json"), "w") as f:
        json.dump({"seed": MASTER_SEED, "n_enum_weights": N_ENUM, "rows": records}, f, indent=2)

    lines = [
        "% Auto-generated by scripts/run_continuous_study.py. Do not edit.",
        "\\begin{tabular}{rrrrrrrr}",
        "\\toprule",
        "$m$ & $n$ & $K$ & \\multicolumn{2}{c}{Direct (Thm.~9)} & "
        "\\multicolumn{2}{c}{Enumerate-then-select} & Direct no\\\\",
        "  &   &   & LPs & ms & LPs & ms & worse\\\\",
        "\\midrule",
    ]
    for r in records:
        lines.append(
            f"{r['m']} & {r['n']} & {r['K']} & {r['direct_lp_calls']} & {r['direct_ms']:.1f} & "
            f"{r['enum_lp_calls']} & {r['enum_ms']:.1f} & "
            f"{r['direct_no_worse_frac']*100:.0f}\\%\\\\"
        )
    lines += ["\\bottomrule", "\\end{tabular}", ""]
    with open(os.path.join(TEX, "continuous_study.tex"), "w") as f:
        f.write("\n".join(lines))
    print("wrote", os.path.join(TEX, "continuous_study.tex"))


if __name__ == "__main__":
    main()
