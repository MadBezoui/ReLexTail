"""Hierarchical and cluster bootstrap for the paired flip-rate differences (MC4).

The manuscript reports paired bootstrap intervals whose resampling unit is the
individual instance.  Instances are nested within master seeds and within
generator families, so an instance-level bootstrap is anticonservative if
instances sharing a seed or a family are dependent -- and the per-family
disaggregation shows they plainly are, the effect ranging from about 0.03 on
job-shop instances to about 0.58 on WFG2.

This script recomputes every headline paired difference under three resampling
schemes on the same data:

  instance   the published scheme: resample instances with replacement,
             ignoring the nesting;
  seed       cluster bootstrap at the master-seed level: resample the 10 seeds
             with replacement and take every instance of each drawn seed;
  hier       hierarchical bootstrap: resample the 6 generator families with
             replacement, then within each drawn family resample its seeds,
             then within each drawn (family, seed) cell resample its instances.

It also reports the seed-level paired summary with an exact two-sided sign test
over the 10 seeds, which makes no distributional assumption at all and is the
honest fallback when only ten clusters are available.

Inputs   scripts/real_results/multiseed/per_instance_*.csv
         scripts/real_results/symmetrised/per_instance_*.csv
Outputs  scripts/real_results/hierarchical_bootstrap.json
         manuscript/generated/hierarchical_bootstrap.tex

Usage    python scripts/run_hierarchical_bootstrap.py [--boot 10000]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from math import comb

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

RES = os.path.join(HERE, "real_results")
TEXDIR = os.path.abspath(os.path.join(ROOT, "..", "manuscript", "generated"))

N_BOOT = 10_000
SEED = 20260628
LEVELS = ["0.05", "0.10", "0.20"]


# --------------------------------------------------------------------------- #
def load(subdir):
    files = sorted(glob.glob(os.path.join(RES, subdir, "per_instance_*.csv")))
    if not files:
        raise SystemExit(f"no per-instance files under {subdir}/")
    return pd.concat([pd.read_csv(f) for f in files], ignore_index=True)


# --------------------------------------------------------------------------- #
# three resampling schemes, each returning a (n_boot,) vector of resampled means
# --------------------------------------------------------------------------- #
def boot_instance(d, rng, n_boot):
    n = d.size
    idx = rng.integers(0, n, size=(n_boot, n))
    return d[idx].mean(axis=1)


def boot_cluster(d, keys, rng, n_boot):
    """Resample whole clusters (all instances of a drawn key), with replacement."""
    groups = [np.flatnonzero(keys == k) for k in np.unique(keys)]
    g = len(groups)
    out = np.empty(n_boot)
    for b in range(n_boot):
        pick = rng.integers(0, g, size=g)
        idx = np.concatenate([groups[i] for i in pick])
        out[b] = d[idx].mean()
    return out


def boot_hierarchical(d, fam, seed, rng, n_boot):
    """families -> seeds within family -> instances within (family, seed)."""
    fams = np.unique(fam)
    cells = {}
    for f in fams:
        sds = np.unique(seed[fam == f])
        cells[f] = {s: np.flatnonzero((fam == f) & (seed == s)) for s in sds}
    out = np.empty(n_boot)
    nf = len(fams)
    for b in range(n_boot):
        chunks = []
        for f in fams[rng.integers(0, nf, size=nf)]:
            sds = list(cells[f])
            for s in [sds[i] for i in rng.integers(0, len(sds), size=len(sds))]:
                idx = cells[f][s]
                chunks.append(idx[rng.integers(0, idx.size, size=idx.size)])
        out[b] = d[np.concatenate(chunks)].mean()
    return out


def ci(v, alpha=0.05):
    lo, hi = np.quantile(v, [alpha / 2, 1 - alpha / 2])
    return float(lo), float(hi)


def sign_test(x):
    """Exact two-sided sign test that the per-seed paired mean differs from 0."""
    pos = int(np.sum(x > 0))
    neg = int(np.sum(x < 0))
    n = pos + neg
    if n == 0:
        return 1.0, pos, neg
    k = min(pos, neg)
    tail = sum(comb(n, i) for i in range(k + 1)) / 2 ** n
    return float(min(1.0, 2 * tail)), pos, neg


# --------------------------------------------------------------------------- #
def analyse(name, diff, fam, seed, rng, n_boot):
    diff = np.asarray(diff, dtype=float)
    per_seed = np.array([diff[seed == s].mean() for s in np.unique(seed)])
    p_sign, pos, neg = sign_test(per_seed)
    res = {
        "quantity": name,
        "n_instances": int(diff.size),
        "n_seeds": int(np.unique(seed).size),
        "n_families": int(np.unique(fam).size),
        "mean": float(diff.mean()),
        "ci_instance": ci(boot_instance(diff, rng, n_boot)),
        "ci_seed_cluster": ci(boot_cluster(diff, seed, rng, n_boot)),
        "ci_hierarchical": ci(boot_hierarchical(diff, fam, seed, rng, n_boot)),
        "per_seed_mean": [float(x) for x in per_seed],
        "per_seed_min": float(per_seed.min()),
        "per_seed_max": float(per_seed.max()),
        "sign_test_p": p_sign,
        "sign_pos": pos,
        "sign_neg": neg,
    }
    for k in ("ci_instance", "ci_seed_cluster", "ci_hierarchical"):
        lo, hi = res[k]
        res[k + "_width"] = hi - lo
    return res


def main(n_boot=N_BOOT):
    rng = np.random.default_rng(SEED)
    ms = load("multiseed")
    sym = load("symmetrised")

    rows = []
    # --- headline: ASF minus LexPR point fragility, per level ----------------
    for lv in LEVELS:
        d = ms[f"flip_asf_{lv}"].to_numpy() - ms[f"flip_lexpr_{lv}"].to_numpy()
        rows.append(analyse(f"flip ASF$-$LexPR, $p={float(lv)*100:.0f}\\%$",
                            d, ms["family"].to_numpy(), ms["seed"].to_numpy(),
                            rng, n_boot))

    # --- held-out tail loss, which cuts the other way ------------------------
    d = ms["tail_asf"].to_numpy() - ms["tail_lexpr"].to_numpy()
    rows.append(analyse("tail loss ASF$-$LexPR",
                        d, ms["family"].to_numpy(), ms["seed"].to_numpy(),
                        rng, n_boot))

    # --- decomposition: the re-anchoring effect and the leximax effect -------
    d = sym["flip_raw_0.20"].to_numpy() - sym["flip_asfk_0.20"].to_numpy()
    rows.append(analyse("re-anchoring effect, $p=20\\%$",
                        d, sym["family"].to_numpy(), sym["seed"].to_numpy(),
                        rng, n_boot))
    d = sym["flip_asfk_0.20"].to_numpy() - sym["flip_lexpr_0.20"].to_numpy()
    rows.append(analyse("leximax effect (ASF$_K-$LexPR), $p=20\\%$",
                        d, sym["family"].to_numpy(), sym["seed"].to_numpy(),
                        rng, n_boot))

    out = {"seed": SEED, "n_boot": n_boot, "rows": rows}
    with open(os.path.join(RES, "hierarchical_bootstrap.json"), "w") as f:
        json.dump(out, f, indent=2)
    write_table(out)

    for r in rows:
        print(f"{r['quantity']:44s} mean={r['mean']:+.4f} "
              f"inst={fmt_ci(r['ci_instance'])} "
              f"seed={fmt_ci(r['ci_seed_cluster'])} "
              f"hier={fmt_ci(r['ci_hierarchical'])} "
              f"widen x{r['ci_hierarchical_width']/r['ci_instance_width']:.1f} "
              f"sign p={r['sign_test_p']:.3f}")
    return out


def fmt_ci(t):
    return f"[{t[0]:+.4f},{t[1]:+.4f}]"


def write_table(out):
    lines = [
        "% Auto-generated by scripts/run_hierarchical_bootstrap.py. Do not edit.",
        "\\footnotesize",
        "\\setlength{\\tabcolsep}{2pt}",
        "\\resizebox{\\linewidth}{!}{%",
        "\\begin{tabular}{@{}lrccccr@{}}",
        "\\toprule",
        "Paired quantity & mean & instance CI & seed-cluster CI & hierarchical CI & widening & sign test\\\\",
        "\\midrule",
    ]
    for r in out["rows"]:
        w = r["ci_hierarchical_width"] / r["ci_instance_width"]
        lines.append(
            f"{r['quantity']} & ${r['mean']:+.4f}$ & "
            f"$[{r['ci_instance'][0]:+.3f},{r['ci_instance'][1]:+.3f}]$ & "
            f"$[{r['ci_seed_cluster'][0]:+.3f},{r['ci_seed_cluster'][1]:+.3f}]$ & "
            f"$[{r['ci_hierarchical'][0]:+.3f},{r['ci_hierarchical'][1]:+.3f}]$ & "
            f"$\\times{w:.1f}$ & $p={r['sign_test_p']:.3f}$" + r"\\"
        )
    lines += [
        "\\bottomrule",
        "\\end{tabular}%",
        "}"
    ]
    os.makedirs(TEXDIR, exist_ok=True)
    with open(os.path.join(TEXDIR, "hierarchical_bootstrap.tex"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("wrote generated/hierarchical_bootstrap.tex")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=N_BOOT)
    main(ap.parse_args().boot)
