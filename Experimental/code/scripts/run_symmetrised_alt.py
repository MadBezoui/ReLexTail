"""Symmetrised baselines: decomposing LexPR's advantage (T3.3).

The comparisons of `run_real_experiments.py` pit LexPR, which consumes a K-probe
declared family, against baselines that consume a single equal-weight criterion
vector. That is not a calibrated contest, and any fragility gap it shows
confounds two distinct causes:

  (a) FAMILY RICHNESS  -- LexPR is told about K probes, ASF about m criteria;
  (b) LEXICOGRAPHIC REFINEMENT -- LexPR breaks ties beyond the worst coordinate,
      whereas a scalarisation collapses the whole profile into one number.

This script separates them by running four rules on the SAME instances:

  ASF_raw  the manuscript's baseline: augmented Chebyshev on the RAW normalised
           matrix r(x;b), which is bound-sensitive
  ASF_1    the same scalarisation on the re-anchored SINGLETON disappointments
  ASF_K    the same scalarisation on the full re-anchored K-probe profile,
           i.e. ASF given LexPR's declared family
  MMR_K    pure minimax over the K-probe profile (LexPR's stage 1 alone)
  LexPR_1  leximax over the singleton disappointments only
  LexPR    the full leximax over the K-probe profile

ASF_raw -> ASF_1 isolates the effect of RE-ANCHORING (dividing each probe by its
own active range); ASF_1 -> ASF_K isolates (a); ASF_K/MMR_K -> LexPR isolates
(b).  Whichever step carries the fragility difference is the one that deserves
the credit, and we report it wherever it falls.

Outputs scripts/real_results/symmetrised.json and
manuscript/generated/symmetrised_table.tex.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from lexpr import metrics, problems  # noqa: E402
from lexpr.methods import singleton_disappointments, winner_class  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "rre", os.path.join(HERE, "run_real_experiments.py")
)
rre = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rre)

SEEDS = [20260628, 20260629, 20260630, 20260701, 20260702, 20260703, 20260704, 20260705, 20260706, 20260707]
LEVELS = [0.05, 0.10, 0.20]
M_DRAWS = 60  # draws per level, matching the main battery. This decomposition
              # compares rules against each other on identical draws, so the
              # paired differences are what carry the conclusion.
RHO = 1e-4

OUT = os.path.join(HERE, "real_results")
ALT_DIR = os.path.join(OUT, "symmetrised_alt")
TEXDIR = os.path.abspath(os.path.join(ROOT, "..", "manuscript", "generated"))


def asf_on_profile(D, rho=RHO):
    """Augmented Chebyshev applied to a disappointment matrix D (n x K).

    With K = 1 this is the classic ASF; with K = m singletons it reduces to the
    equal-weight criterion ASF, so ASF_1 and ASF_K differ only in the family.
    """
    return int(np.argmin(D.max(axis=1) + rho * D.sum(axis=1)))


def mmr_on_profile(D):
    """Pure minimax over the probe profile: LexPR's first stage with no refinement.

    Ties on the worst coordinate are broken by lowest index, matching the model
    contract's deterministic tie policy (C7); the point is precisely that no
    later coordinate is consulted.
    """
    return int(np.argmin(D.max(axis=1)))


def run_seed(seed, sdir=None, budget_s=None):
    """One master seed.  Checkpoints after each generator family when `sdir`
    is given, so a run killed by a wall-clock budget resumes where it stopped
    instead of discarding the seed."""
    import time
    t0 = time.time()
    rng = np.random.default_rng(seed)
    rows = []
    for fam_i, (label, geom, n_inst, (mlo, mhi), cap) in enumerate(rre.FAMILIES):
        part = (None if sdir is None
                else os.path.join(sdir, f"part_{seed}_{fam_i}.csv"))
        if part is not None and os.path.exists(part):
            prev = pd.read_csv(part)
            rows.extend(prev.to_dict("records"))
            # replay the RNG stream this family would have consumed
            for _ in range(n_inst):
                m = int(rng.integers(mlo, mhi + 1))
                N = int(rng.integers(60, cap + 1))
                F = problems.make_candidate_set(geom, N, m, rng)
                if F.shape[0] < 3:
                    continue
                rng.integers(1 << 31)
                for p in LEVELS:
                    for _d in range(M_DRAWS):
                        rre.perturb_bounds_range_proportional(F, p, rng)
            continue
        if budget_s is not None and time.time() - t0 > budget_s:
            return None
        fam_rows = []
        for _ in range(n_inst):
            m = int(rng.integers(mlo, mhi + 1))
            N = int(rng.integers(60, cap + 1))
            F = problems.make_candidate_set(geom, N, m, rng)
            if F.shape[0] < 3:
                continue

            probes = rre.build_probes(F, theta=rre.THETA)[0]
            D = rre.D_matrix(F, probes)
            # Proposition 1: singleton disappointments do not depend on the
            # bounds, so they are computed ONCE from the bound-free closed form
            # and reused at every draw.  Recomputing them under each perturbed
            # bound vector used to introduce a ~1e-9 numerical wobble, which is
            # far larger than the ~1e-16 gaps separating genuinely tied
            # alternatives, and produced spurious "flips" of a rule that is
            # provably invariant.
            singles = singleton_disappointments(F)

            w_lex, _ = rre.fast_leximax_argmin(D)
            w_lex1, _ = rre.fast_leximax_argmin(singles)
            w_asf1 = asf_on_profile(singles)
            w_asfk = asf_on_profile(D)
            w_mmrk = mmr_on_profile(D)
            w_raw = rre.asf_winner(F)

            cache = metrics.precompute_utilities(
                F, np.random.default_rng(int(rng.integers(1 << 31))), n_per_family=200
            )
            rec = {"seed": seed, "family": label, "m": m, "N": F.shape[0]}
            for tag, w in (("lexpr", w_lex), ("lexpr1", w_lex1), ("asf1", w_asf1),
                           ("asfk", w_asfk), ("mmrk", w_mmrk), ("raw", w_raw)):
                _, rec[f"tail_{tag}"] = metrics.loss_from_cache(cache, w)
            rec["agree_lexpr_asfk"] = int(w_lex == w_asfk)
            rec["agree_lexpr_mmrk"] = int(w_lex == w_mmrk)
            # The contract reports ties as a class, so the class is what a flip
            # rate should really be measured on.  Both are recorded: the class
            # flip is the property of the rule, the point flip is the property
            # of the rule plus its tie-break.
            cls_lex = winner_class(D)
            cls_lex1 = winner_class(singles)
            rec["tied_lexpr"] = int(len(cls_lex) > 1)
            rec["tied_lexpr1"] = int(len(cls_lex1) > 1)

            tags = ("lexpr", "lexpr1", "asf1", "asfk", "mmrk", "raw")
            flips = {t: {p: 0 for p in LEVELS} for t in tags}
            cflips = {t: {p: 0 for p in LEVELS} for t in ("lexpr", "lexpr1")}
            base = {"lexpr": w_lex, "lexpr1": w_lex1, "asf1": w_asf1,
                    "asfk": w_asfk, "mmrk": w_mmrk, "raw": w_raw}
            for p in LEVELS:
                for _d in range(M_DRAWS):
                    idl, ndr = rre.perturb_bounds_range_proportional(F, p, rng)
                    Dp = rre.D_matrix(F, probes, idl, ndr)
                    Sp = singles          # invariant, by Proposition 1
                    wl, _ = rre.fast_leximax_argmin(Dp)
                    wl1, _ = rre.fast_leximax_argmin(Sp)
                    flips["lexpr"][p] += int(wl != base["lexpr"])
                    flips["lexpr1"][p] += int(wl1 != base["lexpr1"])
                    cflips["lexpr"][p] += int(winner_class(Dp) != cls_lex)
                    cflips["lexpr1"][p] += int(winner_class(Sp) != cls_lex1)
                    flips["asf1"][p] += int(asf_on_profile(Sp) != base["asf1"])
                    flips["asfk"][p] += int(asf_on_profile(Dp) != base["asfk"])
                    flips["mmrk"][p] += int(mmr_on_profile(Dp) != base["mmrk"])
                    flips["raw"][p] += int(rre.asf_winner(F, idl, ndr) != base["raw"])
            for t in flips:
                for p in LEVELS:
                    rec[f"flip_{t}_{p:.2f}"] = flips[t][p] / M_DRAWS
            for t in cflips:
                for p in LEVELS:
                    rec[f"classflip_{t}_{p:.2f}"] = cflips[t][p] / M_DRAWS
            fam_rows.append(rec)
        if part is not None:
            pd.DataFrame(fam_rows).to_csv(part, index=False)
        rows.extend(fam_rows)
    return pd.DataFrame(rows)


def paired_ci(d, n_boot=10000, seed=0):
    d = np.asarray(d, dtype=float)
    d = d[~np.isnan(d)]
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, d.size, size=(n_boot, d.size))
    mm = d[idx].mean(axis=1)
    return float(np.quantile(mm, 0.025)), float(np.quantile(mm, 0.975))


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(TEXDIR, exist_ok=True)
    # Resumable: one file per seed, so a long battery can be run in chunks.
    sdir = ALT_DIR
    os.makedirs(sdir, exist_ok=True)
    budget = None
    if "--budget-s" in sys.argv:
        budget = float(sys.argv[sys.argv.index("--budget-s") + 1])
    for s in SEEDS:
        fp = os.path.join(sdir, f"per_instance_{s}.csv")
        if not os.path.exists(fp):
            df_s = run_seed(s, sdir=sdir, budget_s=budget)
            if df_s is None:
                print(f"seed {s}: wall-clock budget reached, partials kept; rerun")
                return
            df_s.to_csv(fp, index=False)
            for f in os.listdir(sdir):
                if f.startswith(f"part_{s}_"):
                    os.remove(os.path.join(sdir, f))
            print(f"seed {s} done", flush=True)
    missing = [s for s in SEEDS
               if not os.path.exists(os.path.join(sdir, f"per_instance_{s}.csv"))]
    if missing:
        print("pending seeds:", missing)
        return
    df = pd.concat([pd.read_csv(os.path.join(sdir, f"per_instance_{s}.csv"))
                    for s in SEEDS], ignore_index=True)

    rules = ["raw", "lexpr", "asfk", "mmrk", "lexpr1", "asf1"]
    out = {"seeds": SEEDS, "n_instances": int(len(df)), "flip": {}, "tail": {},
           "agreement": {}, "paired_vs_lexpr": {}}

    for t in rules:
        out["flip"][t] = {f"{p:.2f}": round(float(df[f"flip_{t}_{p:.2f}"].mean()), 4)
                          for p in LEVELS}
        out["tail"][t] = round(float(df[f"tail_{t}"].mean()), 4)

    out["agreement"]["lexpr_vs_asfk"] = round(float(df["agree_lexpr_asfk"].mean()), 4)
    out["agreement"]["lexpr_vs_mmrk"] = round(float(df["agree_lexpr_mmrk"].mean()), 4)

    for t in ["asfk", "mmrk", "lexpr1", "asf1", "raw"]:
        d = df["flip_" + t + "_0.20"] - df["flip_lexpr_0.20"]
        lo, hi = paired_ci(d, seed=3)
        out["paired_vs_lexpr"][f"flip_0.20_{t}_minus_lexpr"] = {
            "mean": round(float(d.mean()), 4), "ci95": [round(lo, 4), round(hi, 4)],
            "supported": bool(lo > 0 or hi < 0)}
        dt = df["tail_" + t] - df["tail_lexpr"]
        lo, hi = paired_ci(dt, seed=4)
        out["paired_vs_lexpr"][f"tail_{t}_minus_lexpr"] = {
            "mean": round(float(dt.mean()), 4), "ci95": [round(lo, 4), round(hi, 4)],
            "supported": bool(lo > 0 or hi < 0)}

    with open(os.path.join(OUT, "symmetrised_alt.json"), "w") as f:
        json.dump(out, f, indent=2)

    # Short row labels: in the journal's two-column layout even a full-width
    # table* cannot carry a long first column. What each rule means belongs in
    # the caption, not in the stub.
    nice = {"raw": "ASF$_{\\mathrm{raw}}$",
            "lexpr": "\\textbf{LexPR}",
            "asfk": "ASF$_K$",
            "mmrk": "MMR$_K$",
            "lexpr1": "LexPR$_1$",
            "asf1": "ASF$_1$"}
    L = ["% Auto-generated by scripts/run_symmetrised.py. Do not edit.",
         "\\footnotesize",
         "\\begin{tabular}{@{}lrrrrr@{}}", "\\toprule",
         "Rule & \\multicolumn{3}{c}{Class flip rate} & Tail & Agrees\\\\",
         "\\cmidrule(lr){2-4}",
         " & $5\\%$ & $10\\%$ & $20\\%$ & loss & w/ LexPR\\\\", "\\midrule"]
    for t in rules:
        ag = (f"{out['agreement']['lexpr_vs_asfk']*100:.1f}\\%" if t == "asfk" else
              f"{out['agreement']['lexpr_vs_mmrk']*100:.1f}\\%" if t == "mmrk" else "---")
        L.append(f"{nice[t]} & " +
                 " & ".join(f"{out['flip'][t][f'{p:.2f}']*100:.1f}\\%" for p in LEVELS) +
                 f" & {out['tail'][t]:.3f} & {ag}\\\\")
    L += ["\\bottomrule", "\\end{tabular}", ""]
    with open(os.path.join(TEXDIR, "symmetrised_table.tex"), "w") as f:
        f.write("\n".join(L))

    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
