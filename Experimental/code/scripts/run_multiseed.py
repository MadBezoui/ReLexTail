"""Multi-seed benchmark battery with an inferential layer (T3.1, T3.2).

Reruns the 500-instance battery of `run_real_experiments.py` under several
master seeds and writes ONE ROW PER INSTANCE, so that every headline rate can
afterwards be reported with

  * seed-pooled point estimates and BETWEEN-SEED standard deviations (T3.1), and
  * paired per-instance differences with bootstrap 95% confidence intervals,
    disaggregated by generator family (T3.2).

The per-instance computation is imported from `run_real_experiments` rather than
duplicated, so the single-seed run at seed 20260628 reproduces the archived
`summary.json` exactly and the multi-seed study is a strict generalisation of it.

Usage (resumable -- rerunning skips seeds already on disk):

    python scripts/run_multiseed.py            # run all seeds, then aggregate
    python scripts/run_multiseed.py --seeds 3  # run at most 3 pending seeds
    python scripts/run_multiseed.py --aggregate-only

Outputs:
    scripts/real_results/multiseed/per_instance_<seed>.csv
    scripts/real_results/multiseed_summary.json
    manuscript/generated/multiseed_table.tex
"""
from __future__ import annotations

import argparse
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

_spec = importlib.util.spec_from_file_location(
    "rre", os.path.join(HERE, "run_real_experiments.py")
)
rre = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rre)

# Seed 20260628 is the archived master seed and is kept first so that the
# multi-seed study contains the published run as its seed 0.
SEEDS = [20260628, 20260629, 20260630, 20260701, 20260702,
         20260703, 20260704, 20260705, 20260706, 20260707]

LEVELS = [0.05, 0.10, 0.20]
M_DRAWS = 60
ABLATIONS = ["singletons", "no_clusters", "no_singletons",
             "grand_mean", "grand_max", "asf_singleton"]

OUTDIR = os.path.join(HERE, "real_results")
MSDIR = os.path.join(OUTDIR, "multiseed")
TEXDIR = os.path.abspath(os.path.join(ROOT, "..", "manuscript", "generated"))


def run_one_seed(seed):
    """One full 500-instance battery. Returns a per-instance DataFrame."""
    rng = np.random.default_rng(seed)
    rows = []
    for label, geom, n_inst, (mlo, mhi), cap in rre.FAMILIES:
        for _ in range(n_inst):
            m = int(rng.integers(mlo, mhi + 1))
            N = int(rng.integers(60, cap + 1))
            F = problems.make_candidate_set(geom, N, m, rng)
            if F.shape[0] < 3:
                continue

            probes = rre.build_probes(F, theta=rre.THETA)[0]
            D = rre.D_matrix(F, probes)
            win, S = rre.fast_leximax_argmin(D)

            unique = not np.any(
                np.all(S == S[win], axis=1) & (np.arange(S.shape[0]) != win)
            )
            depth = rre.explanation_depth(S, win) if unique else np.nan

            asf_win = rre.asf_winner(F)
            rec = {
                "seed": seed,
                "family": label,
                "m": m,
                "N": F.shape[0],
                "unique_winner": bool(unique),
                "depth": depth,
                "div_lexpr_asf": int(asf_win != win),
            }

            for v in ABLATIONS:
                if v == "asf_singleton":
                    vw = asf_win
                else:
                    Dv = rre.D_matrix(F, rre.variant_probes(F, v))
                    vw, _ = rre.fast_leximax_argmin(Dv)
                rec[f"div_{v}"] = int(vw != win)

            cache = metrics.precompute_utilities(
                F, np.random.default_rng(int(rng.integers(1 << 31))), n_per_family=200
            )
            _, rec["tail_lexpr"] = metrics.loss_from_cache(cache, win)
            _, rec["tail_asf"] = metrics.loss_from_cache(cache, asf_win)

            for p in LEVELS:
                fl = fa = 0
                for _d in range(M_DRAWS):
                    idl, ndr = rre.perturb_bounds(F, p, rng)
                    wl, _ = rre.fast_leximax_argmin(rre.D_matrix(F, probes, idl, ndr))
                    fl += int(wl != win)
                    fa += int(rre.asf_winner(F, idl, ndr) != asf_win)
                # per-instance flip RATES over the draws -> paired across methods
                rec[f"flip_lexpr_{p:.2f}"] = fl / M_DRAWS
                rec[f"flip_asf_{p:.2f}"] = fa / M_DRAWS
            rows.append(rec)
    return pd.DataFrame(rows)


def paired_bootstrap_ci(diff, n_boot=10000, alpha=0.05, seed=0):
    """Percentile bootstrap CI for the mean of paired per-instance differences."""
    d = np.asarray(diff, dtype=float)
    d = d[~np.isnan(d)]
    if d.size == 0:
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, d.size, size=(n_boot, d.size))
    means = d[idx].mean(axis=1)
    return (float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2)))


def aggregate():
    files = sorted(f for f in os.listdir(MSDIR) if f.startswith("per_instance_"))
    if not files:
        raise SystemExit("no per-seed files; run without --aggregate-only first")
    df = pd.concat([pd.read_csv(os.path.join(MSDIR, f)) for f in files], ignore_index=True)
    seeds = [int(s) for s in sorted(df["seed"].unique())]

    def pooled(col):
        """Seed-pooled mean and between-seed SD of a per-instance 0/1 or rate column."""
        per_seed = df.groupby("seed")[col].mean()
        return float(per_seed.mean()), float(per_seed.std(ddof=1)), per_seed.to_dict()

    out = {
        "seeds": seeds,
        "n_seeds": len(seeds),
        "instances_per_seed": int(df.groupby("seed").size().median()),
        "m_draws_per_level": M_DRAWS,
        "pooled": {},
        "paired": {},
        "by_family": {},
    }

    cols = ["div_lexpr_asf"] + [f"div_{v}" for v in ABLATIONS]
    for p in LEVELS:
        cols += [f"flip_lexpr_{p:.2f}", f"flip_asf_{p:.2f}"]
    for c in cols:
        mean, sd, per_seed = pooled(c)
        out["pooled"][c] = {
            "mean": round(mean, 4),
            "between_seed_sd": round(sd, 4),
            "min_seed": round(min(per_seed.values()), 4),
            "max_seed": round(max(per_seed.values()), 4),
        }

    # Paired per-instance differences, ASF minus LexPR: positive favours LexPR.
    for p in LEVELS:
        d = df[f"flip_asf_{p:.2f}"] - df[f"flip_lexpr_{p:.2f}"]
        lo, hi = paired_bootstrap_ci(d, seed=int(p * 100))
        out["paired"][f"flip_diff_{p:.2f}"] = {
            "mean": round(float(d.mean()), 4),
            "ci95": [round(lo, 4), round(hi, 4)],
            "n": int(d.notna().sum()),
            "supported": bool(lo > 0),
        }
    d = df["tail_asf"] - df["tail_lexpr"]
    lo, hi = paired_bootstrap_ci(d, seed=7)
    out["paired"]["tail_loss_diff"] = {
        "mean": round(float(d.mean()), 4),
        "ci95": [round(lo, 4), round(hi, 4)],
        "n": int(d.notna().sum()),
        "supported": bool(lo > 0 or hi < 0),
    }

    # Per-generator-family disaggregation (T3.2).
    for fam, g in df.groupby("family"):
        dd = g["flip_asf_0.20"] - g["flip_lexpr_0.20"]
        lo, hi = paired_bootstrap_ci(dd, seed=11)
        out["by_family"][fam] = {
            "n_instances": int(len(g)),
            "div_lexpr_asf": round(float(g["div_lexpr_asf"].mean()), 4),
            "flip_lexpr_0.20": round(float(g["flip_lexpr_0.20"].mean()), 4),
            "flip_asf_0.20": round(float(g["flip_asf_0.20"].mean()), 4),
            "flip_diff_0.20_ci95": [round(lo, 4), round(hi, 4)],
            "tail_lexpr": round(float(g["tail_lexpr"].mean()), 4),
            "tail_asf": round(float(g["tail_asf"].mean()), 4),
        }

    with open(os.path.join(OUTDIR, "multiseed_summary.json"), "w") as f:
        json.dump(out, f, indent=2)

    _write_tex(out)
    return out


def _write_tex(out):
    os.makedirs(TEXDIR, exist_ok=True)
    P = out["pooled"]
    L = [
        "% Auto-generated by scripts/run_multiseed.py. Do not edit.",
        "\\begin{tabular}{lccc}",
        "\\toprule",
        "Quantity & Pooled estimate & Between-seed s.d. & Seed range\\\\",
        "\\midrule",
    ]

    def row(name, key, pct=True):
        d = P[key]
        f = 100.0 if pct else 1.0
        u = "\\%" if pct else ""
        L.append(
            f"{name} & {d['mean']*f:.1f}{u} & {d['between_seed_sd']*f:.1f}{u} & "
            f"[{d['min_seed']*f:.1f}, {d['max_seed']*f:.1f}]{u}\\\\"
        )

    row("Divergence from ASF", "div_lexpr_asf")
    L.append("\\addlinespace")
    for p in LEVELS:
        row(f"Flip rate, LexPR at {int(p*100)}\\%", f"flip_lexpr_{p:.2f}")
    for p in LEVELS:
        row(f"Flip rate, ASF at {int(p*100)}\\%", f"flip_asf_{p:.2f}")
    L.append("\\addlinespace")
    for v, nm in [("singletons", "Singletons only"),
                  ("no_singletons", "No singletons"),
                  ("grand_mean", "Grand mean only"),
                  ("grand_max", "Grand max only"),
                  ("asf_singleton", "ASF-equivalent singleton")]:
        row(f"Ablation divergence: {nm}", f"div_{v}")
    L += ["\\bottomrule", "\\end{tabular}", ""]
    with open(os.path.join(TEXDIR, "multiseed_table.tex"), "w") as f:
        f.write("\n".join(L))

    # Per-generator-family disaggregation with paired bootstrap CIs.
    F = [
        "% Auto-generated by scripts/run_multiseed.py. Do not edit.",
        "\\begin{tabular}{lrrrrr}",
        "\\toprule",
        "Generator & Inst. & Diverge & \\multicolumn{2}{c}{Flip rate at $20\\%$} & "
        "Paired difference\\\\",
        " &  & from ASF & LexPR & ASF & (ASF $-$ LexPR), 95\\% CI\\\\",
        "\\midrule",
    ]
    for fam in sorted(out["by_family"]):
        v = out["by_family"][fam]
        lo, hi = v["flip_diff_0.20_ci95"]
        F.append(
            f"{fam} & {v['n_instances']} & {v['div_lexpr_asf']*100:.1f}\\% & "
            f"{v['flip_lexpr_0.20']*100:.1f}\\% & {v['flip_asf_0.20']*100:.1f}\\% & "
            f"$[{lo:.3f},\\,{hi:.3f}]$\\\\"
        )
    F += ["\\bottomrule", "\\end{tabular}", ""]
    with open(os.path.join(TEXDIR, "multiseed_by_family.tex"), "w") as f:
        f.write("\n".join(F))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=len(SEEDS),
                    help="max number of pending seeds to run in this invocation")
    ap.add_argument("--aggregate-only", action="store_true")
    args = ap.parse_args()

    os.makedirs(MSDIR, exist_ok=True)
    if not args.aggregate_only:
        done = 0
        for s in SEEDS:
            path = os.path.join(MSDIR, f"per_instance_{s}.csv")
            if os.path.exists(path):
                continue
            if done >= args.seeds:
                break
            df = run_one_seed(s)
            df.to_csv(path, index=False)
            print(f"seed {s}: {len(df)} instances -> {os.path.basename(path)}")
            done += 1

    pending = [s for s in SEEDS
               if not os.path.exists(os.path.join(MSDIR, f"per_instance_{s}.csv"))]
    if pending:
        print(f"pending seeds: {pending}")
        return
    out = aggregate()
    print(json.dumps({"pooled": out["pooled"], "paired": out["paired"]}, indent=2))


if __name__ == "__main__":
    main()
