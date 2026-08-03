"""Known-truth validation of the certified branch-and-bound (MC3).

The certified procedure of `lexpr.certified` returns sound sets

    In  subset  S_pos  subset  Out

but soundness alone is not evidence that the enclosures are *tight* enough to
say anything.  This script supplies the missing controlled test: on
low-dimensional instances, where the bound box has 2m coordinates and can be
swept exhaustively, we compute a reference possible-winner set S_grid by
evaluating the EXACT finite LexPR rule at every point of a dense product grid
over the box, and check

    In  subset  S_grid  subset  Out

on every instance and level.  S_grid is a high-confidence inner approximation
of S_pos (every grid point is a genuine admissible bound vector, so every
winner it produces really is a possible winner), which makes the left
inclusion a consistency check on the certified inner set and the right
inclusion a genuine test of outer-set validity: an alternative that wins
somewhere on the grid but is missing from Out would be a soundness violation.

Alongside the inclusion test the script measures the five behaviours the
referee asked to see illustrated:

  1. exact recovery, In == Out and zero unresolved volume;
  2. persistent ties, grid points at which the top two sorted profiles are
     exactly equal, so no sole winner can ever be certified there;
  3. denominator-positivity failures, counted over (sub-box, aggregate-probe)
     pairs on which the enclosed active range is non-positive and the trivial
     enclosure [0,1] is substituted;
  4. unresolved volume caused by dependency overestimation, the gap between
     what the grid shows and what the enclosures can prove;
  5. monotone tightening of the terminal-leaf outer set under refinement,
     |Out| and the unresolved fraction both non-increasing in the box budget.

Outputs
    scripts/real_results/certified_truth.json
    manuscript/generated/certified_truth.tex

Resumable: finished rows are appended to real_results/certified_truth_rows.jsonl
and skipped on a later invocation, so the battery can be completed across
several bounded runs.

Usage
    python scripts/run_certified_truth.py [--quick] [--budget-s SECONDS]
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from lexpr import certified as C  # noqa: E402
from lexpr import problems  # noqa: E402

OUTDIR = os.path.join(HERE, "real_results")
TEXDIR = os.path.abspath(os.path.join(ROOT, "..", "manuscript", "generated"))

SEED = 20260628
LEVELS = [0.02, 0.05, 0.10]
BUDGETS = [250, 1000, 4000, 16000]          # refinement ladder, for behaviour 5
BIG_BUDGET = 120_000                        # extra rung, tried only when the
PROMISING = 0.5                             # 16k run already resolved most of
                                            # the box; a run still at u ~ 1 will
                                            # not terminate at any budget and
                                            # spending 120k boxes on it only
                                            # burns time.
CACHE = "certified_truth_rows.jsonl"        # resumable: one finished row per line
MAX_GRID = 300_000                       # exhaustive sweep size cap
CHUNK = 20_000


# --------------------------------------------------------------------------- #
# canonical probe family in the (kind, index-tuple) encoding of lexpr.certified
# --------------------------------------------------------------------------- #
def canonical_probes(m):
    probes = [("single", (i,)) for i in range(m)]
    if m > 1:
        probes.append(("mean", tuple(range(m))))
        probes.append(("max", tuple(range(m))))
    return probes


# --------------------------------------------------------------------------- #
# exact finite LexPR, vectorised over a batch of bound vectors
# --------------------------------------------------------------------------- #
def _winners_batch(F, probes, ideal, nadir):
    """Exact LexPR winner and tie flag at each of B bound vectors.

    F        (N, m)
    ideal    (B, m)      nadir (B, m)
    returns  winners (B,) int, tied (B,) bool
    """
    N, m = F.shape
    r = (F[None, :, :] - ideal[:, None, :]) / (nadir - ideal)[:, None, :]   # (B,N,m)
    cols = []
    for kind, idx in probes:
        if kind == "single":
            v = r[:, :, idx[0]]
        elif kind == "mean":
            v = r[:, :, list(idx)].mean(axis=2)
        elif kind == "max":
            v = r[:, :, list(idx)].max(axis=2)
        else:                                    # pragma: no cover
            raise ValueError(kind)
        lo = v.min(axis=1, keepdims=True)
        hi = v.max(axis=1, keepdims=True)
        cols.append((v - lo) / np.where(hi - lo > 0, hi - lo, 1.0))
    D = np.stack(cols, axis=2)                   # (B,N,K)
    S = -np.sort(-D, axis=2)                     # descending sorted profiles

    # lexicographic argmin over the N candidates, vectorised across the batch:
    # keep a live mask, and at each coordinate retain only the rows attaining
    # the coordinate minimum among the still-live rows.
    B = S.shape[0]
    live = np.ones((B, N), dtype=bool)
    for k in range(S.shape[2]):
        col = np.where(live, S[:, :, k], np.inf)
        best = col.min(axis=1, keepdims=True)
        live &= (col == best)
    # a persistent tie is a batch element with more than one surviving row
    tied = live.sum(axis=1) > 1
    winners = np.argmax(live, axis=1)
    return winners.astype(int), tied


def grid_reference(F, probes, p, max_points=MAX_GRID):
    """Exhaustive sweep of box(p): winners seen, tie fraction, grid resolution."""
    N, m = F.shape
    ideal0, nadir0 = F.min(axis=0), F.max(axis=0)
    # box(p) of Definition 'Bound perturbation model':
    #   ideal_i in [ideal_i (1-p), ideal_i],  nadir_i in [nadir_i (1-p), nadir_i (1+p)]
    axes = []
    dims = 2 * m
    g = 2
    while (g + 1) ** dims <= max_points:
        g += 1
    for i in range(m):
        axes.append(np.linspace(ideal0[i] * (1 - p), ideal0[i], g))
    for i in range(m):
        axes.append(np.linspace(nadir0[i] * (1 - p), nadir0[i] * (1 + p), g))

    seen, n_tied, n_pts = set(), 0, 0
    for start in range(0, g ** dims, CHUNK):
        block = list(itertools.islice(itertools.product(*axes), start, start + CHUNK))
        if not block:
            break
        arr = np.asarray(block, dtype=float)
        ideal, nadir = arr[:, :m], arr[:, m:]
        ok = np.all(nadir - ideal > 1e-12, axis=1)
        if not ok.any():
            continue
        w, t = _winners_batch(F, probes, ideal[ok], nadir[ok])
        seen.update(int(x) for x in np.unique(w))
        n_tied += int(t.sum())
        n_pts += int(ok.sum())
    return sorted(seen), n_tied, n_pts, g


# --------------------------------------------------------------------------- #
# denominator-positivity diagnostics
# --------------------------------------------------------------------------- #
def denominator_failures(F, probes, p, n_probe_boxes=64, rng=None):
    """Count (sub-box, aggregate-probe) pairs that fall back to the trivial [0,1].

    NOTE the unit.  The loop visits `n_probe_boxes` sub-boxes and, inside each,
    every AGGREGATE probe, so the returned count is over PAIRS and can exceed
    the number of boxes.  Reporting it as a count of boxes would be wrong.

    Detected structurally: the fallback is the only way an aggregate column can
    come back with lower bound exactly 0 on every candidate and upper bound
    exactly 1 on every candidate.
    """
    rng = np.random.default_rng(0) if rng is None else rng
    root = C._box_from_p(F, p)
    boxes = [root]
    while len(boxes) < n_probe_boxes:
        b = boxes.pop(0)
        boxes.extend(C._split(b))
    fails = 0
    for b in boxes[:n_probe_boxes]:
        Dlo, Dhi = C._D_enclosure(F, probes, b)
        for k, (kind, _idx) in enumerate(probes):
            if kind == "single":
                continue
            if np.all(Dlo[:, k] == 0.0) and np.all(Dhi[:, k] == 1.0):
                fails += 1
    return fails, len(boxes[:n_probe_boxes])


# --------------------------------------------------------------------------- #
# instance battery
# --------------------------------------------------------------------------- #
def build_instances(rng, quick=False):
    """(name, F) pairs.  Low dimension throughout, so the sweep stays exhaustive."""
    inst = []
    geoms = ["concave"] if quick else ["concave", "knapsack"]
    for geom in geoms:
        for m in (2, 3):
            for N in ((4,) if quick else (4, 6)):
                F = problems.make_candidate_set(geom, 8, m, rng)[:N]
                inst.append((f"{geom}-m{m}-N{F.shape[0]}", F))

    # A constructed persistent tie: two candidates with identical criterion
    # vectors have identical profiles at EVERY bound vector, so no sole winner
    # is certifiable anywhere and the unresolved volume can never reach zero.
    Ftie = np.array([[1.0, 4.0],
                     [2.0, 2.0],
                     [2.0, 2.0],
                     [4.0, 1.0]])
    inst.append(("constructed-tie", Ftie))

    # A near-degenerate criterion: criterion 2 has a very small active range, so
    # a wide bound box drives the enclosed aggregate ranges towards zero and
    # exercises the denominator-positivity fallback.
    Fdeg = np.array([[1.0, 1.000],
                     [2.0, 0.999],
                     [3.0, 0.998],
                     [4.0, 0.997]])
    inst.append(("near-degenerate", Fdeg))

    # A boundary-only winner: c4 attains the leximax-optimal profile only on a
    # measure-zero surface INSIDE the box (not on a face of it), so it appears
    # in the grid sweep while never being a sole winner on a positive-volume
    # sub-box.  This is the case the inner set is documented not to catch.
    Fbnd = np.array([[0.0, 3.0],
                     [3.0, 0.0],
                     [1.5, 1.5],
                     [1.4, 1.6]])
    inst.append(("boundary-winner", Fbnd))
    return inst


def run(quick=False, budget_s=None):
    """Resumable.  Finished rows are appended to real_results/CACHE, one JSON
    object per line, and are skipped on a later invocation, so the battery can
    be completed across several bounded runs."""
    rng = np.random.default_rng(SEED)
    os.makedirs(OUTDIR, exist_ok=True)
    cache_path = os.path.join(OUTDIR, CACHE)
    done = {}
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    r = json.loads(line)
                    done[(r["instance"], r["p"])] = r

    rows, t0 = [], time.time()
    for name, F in build_instances(rng, quick):
        m = F.shape[1]
        probes = canonical_probes(m)
        for p in (LEVELS[:2] if quick else LEVELS):
            if (name, p) in done:
                rows.append(done[(name, p)])
                continue
            if budget_s is not None and time.time() - t0 > budget_s:
                print(f"-- wall-clock budget reached, {len(done)} rows cached; rerun to continue")
                return None
            budgets = BUDGETS[:2] if quick else BUDGETS
            ladder = []
            for B in budgets:
                cs = C.certified_sets(F, probes, p, max_boxes=B)
                ladder.append({
                    "budget": B,
                    "n_boxes": int(cs["n_boxes"]),
                    "inner": list(cs["inner_possible"]),
                    "outer": list(cs["outer_possible"]),
                    "unresolved": float(cs["unresolved_vol_frac"]),
                })
            # One extra rung, but only where the ladder is already close to
            # terminating: exact recovery is what we want to exhibit, and a box
            # still at u ~ 1 after 16k sub-boxes will not reach it.
            if 0.0 < ladder[-1]["unresolved"] <= PROMISING and not quick:
                cs = C.certified_sets(F, probes, p, max_boxes=BIG_BUDGET)
                ladder.append({
                    "budget": BIG_BUDGET,
                    "n_boxes": int(cs["n_boxes"]),
                    "inner": list(cs["inner_possible"]),
                    "outer": list(cs["outer_possible"]),
                    "unresolved": float(cs["unresolved_vol_frac"]),
                })
            final = ladder[-1]
            first_exact = next(
                (L["budget"] for L in ladder
                 if L["unresolved"] == 0.0 and set(L["inner"]) == set(L["outer"])),
                None,
            )
            grid, n_tied, n_pts, g = grid_reference(F, probes, p)
            fails, n_probe = denominator_failures(F, probes, p)

            inner_ok = set(final["inner"]) <= set(grid)
            outer_ok = set(grid) <= set(final["outer"])
            # behaviour 5: |Out| and unresolved fraction non-increasing
            monotone = all(
                len(ladder[i + 1]["outer"]) <= len(ladder[i]["outer"])
                and ladder[i + 1]["unresolved"] <= ladder[i]["unresolved"] + 1e-15
                for i in range(len(ladder) - 1)
            )
            row = {
                "instance": name,
                "N": int(F.shape[0]),
                "m": int(m),
                "p": p,
                "grid_res": g,
                "grid_points": n_pts,
                "grid_winners": grid,
                "tie_points": n_tied,
                "tie_frac": n_tied / max(n_pts, 1),
                "inner": final["inner"],
                "outer": final["outer"],
                "unresolved": final["unresolved"],
                "den_fail_pairs": fails,
                "den_probed_boxes": n_probe,
                "inner_subset_grid": bool(inner_ok),
                "grid_subset_outer": bool(outer_ok),
                "exact_recovery": bool(
                    final["unresolved"] == 0.0
                    and set(final["inner"]) == set(final["outer"])
                ),
                "monotone_tightening": bool(monotone),
                "first_exact_budget": first_exact,
                "ladder": ladder,
            }
            rows.append(row)
            done[(name, p)] = row
            with open(cache_path, "a") as f:
                f.write(json.dumps(row) + "\n")
            status = "ok" if (inner_ok and outer_ok and monotone) else "FAIL"
            print(f"{status:4s} {name:22s} p={p:.2f}  In={final['inner']} "
                  f"grid={grid} Out={final['outer']} u={final['unresolved']:.3f} "
                  f"ties={n_tied} denfail={fails}pairs Bex={first_exact}", flush=True)

    violations = [r for r in rows
                  if not (r["inner_subset_grid"] and r["grid_subset_outer"])]
    summary = {
        "seed": SEED,
        "levels": LEVELS,
        "budgets": BUDGETS,
        "n_rows": len(rows),
        "n_violations": len(violations),
        "n_exact_recovery": sum(r["exact_recovery"] for r in rows),
        "n_monotone": sum(r["monotone_tightening"] for r in rows),
        "seconds": round(time.time() - t0, 1),
        "rows": rows,
    }
    os.makedirs(OUTDIR, exist_ok=True)
    with open(os.path.join(OUTDIR, "certified_truth.json"), "w") as f:
        json.dump(summary, f, indent=2)
    write_table(summary)
    print(f"\n{len(rows)} instance-level pairs, {len(violations)} inclusion violations, "
          f"{summary['n_exact_recovery']} exact recoveries, "
          f"{summary['n_monotone']}/{len(rows)} monotone ladders, "
          f"{summary['seconds']}s")
    return summary


def write_table(summary):
    """Compact LaTeX table for Online Resource 1."""
    def fmt(s):
        return "\\{" + ",".join(str(x + 1) for x in s) + "\\}" if s else "$\\varnothing$"

    lines = [
        "% Auto-generated by scripts/run_certified_truth.py. Do not edit.",
        "\\footnotesize",
        "\\setlength{\\tabcolsep}{3.4pt}",
        "\\begin{tabular}{@{}lrrrlllrrrc@{}}",
        "\\toprule",
        "Instance & $N$ & $m$ & $p$ & In & $S_{\\mathrm{grid}}$ & Out & $u$ & ties & "
        "$B^{\\mathrm{ex}}$ & "
        "$\\mathrm{In}\\subseteq S_{\\mathrm{grid}}\\subseteq\\mathrm{Out}$\\\\",
        "\\midrule",
    ]
    for r in summary["rows"]:
        ok = r["inner_subset_grid"] and r["grid_subset_outer"]
        verdict = "yes" if ok else "\\textbf{NO}"
        name = r["instance"].replace("_", "-")
        bex = (f"${r['first_exact_budget']:,}$".replace(",", "{,}")
               if r["first_exact_budget"] else "---")
        lines.append(
            f"\\texttt{{{name}}} & {r['N']} & {r['m']} & "
            f"${r['p']*100:.0f}\\%$ & {fmt(r['inner'])} & {fmt(r['grid_winners'])} & "
            f"{fmt(r['outer'])} & ${r['unresolved']:.3f}$ & "
            f"${r['tie_frac']*100:.1f}\\%$ & {bex} & {verdict}" + r"\\"
        )
    lines += ["\\bottomrule", "\\end{tabular}"]
    os.makedirs(TEXDIR, exist_ok=True)
    with open(os.path.join(TEXDIR, "certified_truth.tex"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("wrote generated/certified_truth.tex")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--budget-s", type=float, default=None,
                    help="stop after this many seconds; rerun to resume")
    a = ap.parse_args()
    run(a.quick, a.budget_s)
