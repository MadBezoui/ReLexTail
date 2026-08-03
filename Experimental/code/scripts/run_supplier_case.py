#!/usr/bin/env python3
"""Run the full sustainable-supplier case study (Work Package 2 + 3).

Produces:
  results/supplier/supplier_case.json     all numbers (auditable)
  paper/generated/supplier_numbers.tex    LaTeX macros for the manuscript
  paper/fig_supplier_certificate.pdf       LexPR decision profile (bar)
  paper/fig_supplier_interval.pdf          interval winner-flip / stability class
  paper/fig_supplier_normsens.pdf          normalisation sensitivity heat strip

All randomness is seeded; rerunning reproduces every figure and number.
"""

from __future__ import annotations
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)  # code/
REPO = os.path.dirname(ROOT)  # repo root
sys.path.insert(0, ROOT)

from lexpr import methods as M
from lexpr.supplier import (
    load_supplier_case,
    pareto_mask,
    correlation_table,
    CRIT_NAMES,
    CRIT_UNITS,
)
from lexpr.families import loss_cache, losses_from

# ---------------------------------------------------------------------------
# Headline probe family (T4.1).
#
# The declared default for this case study is the CANONICAL CORE
#   Q_can = {m singletons} u {grand mean, grand max},
# i.e. build_probes(..., use_clusters=False).  The cluster-augmented family is
# retained, but only as one entry of the archived ablation battery, because the
# cluster layer is an overlap DIAGNOSTIC and not a redundancy-control method.
#
# On these data the two families are observationally identical -- same winner
# (S7), same held-out mean loss (0.1927) and tail loss (0.6171) -- so promoting
# the canonical core changes no reported outcome, only the declared probe count
# (K = 11 -> 9).  See the "adaptive" vs "no_clusters" rows of the ablation.
# ---------------------------------------------------------------------------
HEADLINE_PROBES = {"use_clusters": False}

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from lexpr.publication_figures import OKABE_ITO, publication_style

OUT_RES = os.path.join(REPO, "results", "supplier")
OUT_FIG = os.path.join(REPO, "paper")
OUT_GEN = os.path.join(REPO, "paper", "generated")
for d in (OUT_RES, OUT_GEN):
    os.makedirs(d, exist_ok=True)

SEED = 20260623
THETA = 0.6

# Unified palette shared with the core figures (colour-blind safe, Okabe-Ito).
HILITE = OKABE_ITO["orange"]  # LexPR / high-regret / focal
BASE = OKABE_ITO["blue"]  # baselines / secondary
SKY = OKABE_ITO["sky"]  # mid emphasis
GREEN = OKABE_ITO["green"]  # low / no regret
GREY = OKABE_ITO["gray"]  # neutral
SLATE = OKABE_ITO["black"]  # axes / reference lines


def main():
    F, sup, crit = load_supplier_case()
    N, m = F.shape
    rng = np.random.default_rng(SEED)
    res = {
        "suppliers": sup,
        "criteria": crit,
        "units": CRIT_UNITS,
        "n_suppliers": N,
        "n_criteria": m,
        "theta": THETA,
        "seed": SEED,
    }

    # --- 1. Pareto screen + redundancy structure --------------------------- #
    eff = pareto_mask(F)
    res["n_efficient"] = int(eff.sum())
    C = correlation_table(F)
    gi, ei = crit.index("GHG"), crit.index("Energy")
    res["corr_ghg_energy"] = float(C[gi, ei])
    from lexpr import probes as probes_mod
    clusters = probes_mod.correlation_clusters(F, theta=THETA)
    cl_named = [[crit[i] for i in c] for c in clusters if len(c) > 1]
    res["redundant_clusters"] = cl_named

    # --- 2. Method recommendations ---------------------------------------- #
    method_list = [
        "TOPSIS",
        "CP",
        "VIKOR",
        "Knee",
        "HV",
        "ASF",
        "SMAA",
        "MMR",
        "ChebMMR",
        "LexPR",
    ]
    picks = {}
    for name in method_list:
        idx = M.select(name, F, rng=np.random.default_rng(SEED))
        picks[name] = sup[idx]
    res["recommendations"] = picks
    res["n_distinct_picks"] = len(set(picks.values()))

    # --- 3. LexPR certificate --------------------------------------------- #
    idx, D, labels, probes = M.lexpr(
        F, theta=THETA, return_detail=True, probe_kwargs=HEADLINE_PROBES
    )
    lexpr_winner = sup[idx]
    res["lexpr_winner"] = lexpr_winner
    cert = sorted(zip(labels, D[idx].tolist()), key=lambda t: -t[1])
    res["certificate"] = [{"probe": l, "regret": float(v)} for l, v in cert]
    res["n_probes"] = len(labels)
    # runner-up by leximax: temporarily remove winner
    order = sorted(range(N), key=lambda i: sorted(D[i], reverse=True))
    res["leximax_order"] = [sup[i] for i in order]

    # --- 3b. ReLexTail Diagnostics (S7 vs S1) ----------------------------- #
    from lexpr.orders.relex_tail import compute_profile
    s7_idx = sup.index("S7")
    s1_idx = sup.index("S1")
    resolutions = {k: "0.02" for k in ["maximum", "tail_025", "tail_050", "tail_100"]}
    p7 = compute_profile(D[s7_idx], resolutions)
    p1 = compute_profile(D[s1_idx], resolutions)
    
    decisive_k = None
    cat_names = ["C_M", "C_25", "C_50", "C_100"]
    for k in range(4):
        if p7[k] != p1[k]:
            decisive_k = k
            break
            
    if decisive_k is not None:
        delta_cat = p1[decisive_k] - p7[decisive_k]
        
        if decisive_k == 0:
            v7, v1 = p7[7], p1[7]
        else:
            v7, v1 = p7[decisive_k + 3], p1[decisive_k + 3]
            
        delta_exact = v1 - v7
        mu_cell = p7[decisive_k] * 0.02 - v7
        
        res["relex_diagnostics"] = {
            "S7_profile_cats": list(p7[:4]),
            "S1_profile_cats": list(p1[:4]),
            "S7_exact_M": p7[7],
            "S7_exact_T25": p7[4],
            "S7_exact_T50": p7[5],
            "S7_exact_T100": p7[6],
            "S1_exact_M": p1[7],
            "S1_exact_T25": p1[4],
            "S1_exact_T50": p1[5],
            "S1_exact_T100": p1[6],
            "decisive_coordinate": cat_names[decisive_k],
            "delta_cat": int(delta_cat),
            "delta_exact": float(delta_exact),
            "mu_cell": float(mu_cell)
        }


    # --- 4. Held-out loss on the case (10 preference families) ------------ #
    cache = loss_cache(F, M.normalize, np.random.default_rng(SEED), n_per_family=400)
    loss_tbl = {}
    for name in method_list:
        j = sup.index(picks[name])
        mean_l, tail_l, worst_fam, per = losses_from(cache, j)
        loss_tbl[name] = {"mean": mean_l, "tail": tail_l, "worst_family": worst_fam}
    res["heldout_loss"] = loss_tbl

    # --- 5. Normalisation sensitivity (point bounds) ---------------------- #
    # Model the analyst's *estimated* ideal/nadir as a multiplicative
    # perturbation of the active extrema: each bound estimate may be too high
    # or too low by up to p (a realistic elicited-bound error).
    ideal0 = F.min(axis=0)
    nadir0 = F.max(axis=0)

    def perturbed_bounds(rng, p):
        nadir = nadir0 * (1 + rng.uniform(-p, p, size=m))
        ideal = ideal0 * (1 - rng.uniform(0, p, size=m))
        nadir = np.maximum(nadir, ideal + 1e-3)
        return ideal, nadir

    norm_sens = []
    for p in [0.0, 0.05, 0.10, 0.20, 0.30, 0.50]:
        flips = 0
        trials = 300
        r2 = np.random.default_rng(SEED + 1)
        for _ in range(trials):
            idl, ndr = perturbed_bounds(r2, p)
            w = M.lexpr(
                F, theta=THETA, ideal=idl, nadir=ndr,
                probe_kwargs=HEADLINE_PROBES,
            )
            flips += sup[w] != lexpr_winner
        norm_sens.append({"perturb": p, "flip_rate": flips / trials})
    res["norm_sensitivity"] = norm_sens

    # --- 6. Interval-robust LexPR: necessary / possible winners ----------- #
    interval = {}
    for bstd in [0.05, 0.10, 0.20]:
        # sample bounds, collect per-bound winners -> necessary/possible
        winners = []
        r3 = np.random.default_rng(SEED + 7)
        nb = 500
        for _ in range(nb):
            idl, ndr = perturbed_bounds(r3, bstd)
            w = M.lexpr(
                F, theta=THETA, ideal=idl, nadir=ndr,
                probe_kwargs=HEADLINE_PROBES,
            )
            winners.append(w)
        winners = np.array(winners)
        counts = np.bincount(winners, minlength=N)
        possible = [sup[i] for i in np.where(counts > 0)[0]]
        # necessary = winner under (almost) all bounds: appears in >=99%
        necessary = [sup[i] for i in np.where(counts >= 0.99 * nb)[0]]
        modal = sup[int(np.argmax(counts))]
        modal_freq = float(counts.max() / nb)
        interval[f"{bstd:.2f}"] = {
            "possible": possible,
            "necessary": necessary,
            "stability_class_size": len(possible),
            "modal_winner": modal,
            "modal_frequency": modal_freq,
            "counts": {sup[i]: int(counts[i]) for i in np.where(counts > 0)[0]},
        }
    res["interval_robust"] = interval

    # --- 7. IIA / rank-reversal test (fair across self-normalising rules) - #
    # Remove one non-selected supplier at a time and check whether each
    # method's recommendation changes. This exposes every active-set
    # normalising rule to the same independence-of-irrelevant-alternatives
    # stress, unlike external-bound perturbation which baselines absorb.
    iia = {}
    for name in ["TOPSIS", "CP", "ASF", "MMR", "LexPR"]:
        base_idx = sup.index(picks[name])
        changes = 0
        tested = 0
        for drop in range(N):
            if drop == base_idx:
                continue
            keep = [k for k in range(N) if k != drop]
            Fk = F[keep]
            w_local = M.select(name, Fk, rng=np.random.default_rng(SEED))
            w_global = keep[w_local]
            changes += w_global != base_idx
            tested += 1
        iia[name] = changes / tested
    res["iia_reversal"] = iia

    # Fraction of non-winner removals satisfying Theorem 1's interior condition
    # (removed supplier is NOT the unique min/max of any criterion or probe).
    probes_i, _ = probes_mod.build_probes(F, theta=THETA, **HEADLINE_PROBES)
    P = np.column_stack([q(M.normalize(F)) for q in probes_i])

    def _uniq_extremum(col, i):
        return ((col == col.min()).sum() == 1 and col[i] == col.min()) or (
            (col == col.max()).sum() == 1 and col[i] == col.max()
        )

    win_idx = sup.index(picks["LexPR"])
    interior = 0
    tot = 0
    for y in range(N):
        if y == win_idx:
            continue
        tot += 1
        cu = any(_uniq_extremum(F[:, j], y) for j in range(m))
        pu = any(_uniq_extremum(P[:, k], y) for k in range(P.shape[1]))
        if not (cu or pu):
            interior += 1
    res["iia_interior_fraction"] = interior / tot

    # --- 8. Probe-design ablation (WP5) ----------------------------------- #
    # Vary the probe family and measure: winner, #probes, held-out loss, and
    # certificate sharpness (the worst binding regret of the winner; lower is a
    # flatter, less informative certificate). Also flag strict-Pareto safety:
    # dropping singletons can let a dominated alternative tie its dominator.
    eff_mask = pareto_mask(F)
    ablation = {}
    variant_order = [
        "adaptive",
        "no_clusters",
        "singletons",
        "no_singletons",
        "max_only",
        "random",
    ]
    for v in variant_order:
        vidx, vD, vlabels, _ = M.lexpr_variant(
            F, variant=v, rng=np.random.default_rng(SEED), return_detail=True
        )
        j = vidx
        mean_l, tail_l, _, _ = losses_from(cache, j)
        sharp = float(vD[j].max())  # worst binding regret of winner
        ablation[v] = {
            "winner": sup[j],
            "n_probes": len(vlabels),
            "mean_loss": mean_l,
            "tail_loss": tail_l,
            "cert_sharpness": sharp,
            "winner_efficient": bool(eff_mask[j]),
        }
    # Deduplicated probe family: drop any probe whose disappointment column
    # duplicates another (so multiplicity cannot drive the result). Confirms the
    # certificate is not an artefact of accidental duplicate probes.
    from lexpr import disappointments
    probes_a, labels_a = probes_mod.build_probes(F, theta=THETA)
    Da = disappointments.disappointment_matrix(F, probes_a)
    seen = {}
    keep = []
    for c in range(Da.shape[1]):
        key = tuple(np.round(Da[:, c], 9))
        if key not in seen:
            seen[key] = c
            keep.append(c)
    Dd = Da[:, keep]
    from lexpr.orders.lexpr import leximax_argmin
    jd = leximax_argmin(Dd)
    mean_d, tail_d, _, _ = losses_from(cache, jd)
    ablation["dedup"] = {
        "winner": sup[jd],
        "n_probes": len(keep),
        "mean_loss": mean_d,
        "tail_loss": tail_d,
        "cert_sharpness": float(Dd[jd].max()),
        "winner_efficient": bool(eff_mask[jd]),
        "n_duplicates_removed": int(Da.shape[1] - len(keep)),
    }
    res["ablation"] = ablation

    # ---------------- write JSON ----------------------------------------- #
    with open(os.path.join(OUT_RES, "supplier_case.json"), "w") as fh:
        json.dump(res, fh, indent=2)

    make_figures(res, D, labels, idx, sup, crit)
    write_latex_macros(res)
    write_ablation_table(res)
    print(
        json.dumps(
            {
                k: res[k]
                for k in [
                    "lexpr_winner",
                    "n_distinct_picks",
                    "recommendations",
                    "redundant_clusters",
                    "n_probes",
                    "iia_reversal",
                    "ablation",
                ]
            },
            indent=2,
        )
    )


def write_ablation_table(res):
    # T4.1: the canonical core is the declared headline family and is listed
    # first and in bold; the cluster-augmented family is now just one variant
    # of the ablation battery.
    label = {
        "no_clusters": "Canonical core $\\Q_{\\mathrm{can}}$",
        "adaptive": "+ cluster probes (optional layer)",
        "dedup": "Deduplicated $\\Q_{\\mathrm{aug}}$",
        "singletons": "Singletons only",
        "no_singletons": "No singletons",
        "max_only": "No mean aggregates",
        "random": "Random probes",
    }
    order = [
        "no_clusters",
        "adaptive",
        "dedup",
        "singletons",
        "no_singletons",
        "max_only",
        "random",
    ]
    HEADLINE_VARIANT = "no_clusters"
    ab = res["ablation"]
    rows = []
    for v in order:
        d = ab[v]
        name = label[v]
        if v == HEADLINE_VARIANT:
            name = "\\textbf{" + name + "}"
        rows.append(
            f"{name} & {d['winner']} & {d['n_probes']} & "
            f"{d['mean_loss']:.3f} & {d['tail_loss']:.3f} & "
            f"{d['cert_sharpness']:.2f}\\\\"
        )
    body = "\n".join(rows)
    tex = (
        "% Auto-generated by run_supplier_case.py. Do not edit.\n"
        "\\begin{tabular}{lccccc}\n\\toprule\n"
        "Probe family & winner & \\#probes & mean loss & tail loss & max cert.\\ regret\\\\\n"
        "\\midrule\n" + body + "\n\\bottomrule\n\\end{tabular}\n"
    )
    with open(os.path.join(OUT_GEN, "supplier_ablation.tex"), "w") as fh:
        fh.write(tex)


def _pretty(label, crit):
    """Map probe labels (f1.., mean(f4,f5)..) to readable criterion names."""
    import re

    def fi(tok):
        m = re.fullmatch(r"f(\d+)", tok)
        return crit[int(m.group(1)) - 1] if m else tok

    if label in ("mean(all)", "max(all)"):
        return label.replace("all", "all criteria")
    m = re.fullmatch(r"(mean|max)\((.*)\)", label)
    if m:
        parts = [fi(t) for t in m.group(2).split(",")]
        return f"{m.group(1)}({', '.join(parts)})"
    return fi(label)


def make_figures(res, D, labels, widx, sup, crit):
    from matplotlib.patches import Patch

    winner = res["lexpr_winner"]

    # --- certificate bar -------------------------------------------------- #
    cert = res["certificate"]
    names = [_pretty(c["probe"], crit) for c in cert]
    vals = [c["regret"] for c in cert]
    with publication_style():
        fig, ax = plt.subplots(figsize=(6.6, 3.6))
        cols = [HILITE if v >= 0.5 else (SKY if v >= 0.25 else GREY) for v in vals]
        bars = ax.barh(
            range(len(vals)), vals, color=cols, edgecolor="white", linewidth=0.5
        )
        for i, v in enumerate(vals):
            ax.text(
                v + 0.015,
                i,
                f"{v:.2f}",
                va="center",
                ha="left",
                fontsize=7,
                color=SLATE,
            )
        ax.set_yticks(range(len(vals)))
        ax.set_yticklabels(names)
        ax.invert_yaxis()
        ax.set_xlabel("normalised disappointment $D_q$ (0 = none, 1 = worst)")
        ax.set_xlim(0, 1.08)
        ax.axvline(0.5, color=GREY, ls=":", lw=0.9)
        # No title inside the artwork: Springer requires titles and captions to
        # live in the manuscript text, not in the figure file.
        ax.legend(
            handles=[
                Patch(facecolor=HILITE, label="high regret ($\\geq 0.5$)"),
                Patch(facecolor=SKY, label="moderate"),
                Patch(facecolor=GREY, label="low / none"),
            ],
            frameon=False,
            fontsize=7,
            loc="lower right",
        )
        fig.tight_layout()
        fig.savefig(os.path.join(OUT_FIG, "fig_supplier_certificate.pdf"))
        plt.close(fig)

    # --- normalisation sensitivity + interval stability ------------------- #
    ns = res["norm_sensitivity"]
    iv = res["interval_robust"]
    with publication_style():
        fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.2))
        ax = axes[0]
        xs = [d["perturb"] * 100 for d in ns]
        ys = [d["flip_rate"] for d in ns]
        ax.plot(xs, ys, "-o", color=HILITE, ms=4, lw=1.6)
        ax.set_xlabel("bound perturbation $p$ (fraction of the nominal bound)")
        ax.set_ylabel("point-winner flip rate")
        ax.set_ylim(-0.02, 1.02)
        ax.set_title("(a)", loc="left")
        ax.grid(True, alpha=0.25)

        ax = axes[1]
        bstds = sorted(iv.keys())
        sizes = [iv[b]["stability_class_size"] for b in bstds]
        modal = [iv[b]["modal_frequency"] for b in bstds]
        x = np.arange(len(bstds))
        b = ax.bar(
            x,
            sizes,
            width=0.55,
            color=BASE,
            edgecolor="white",
            label="possible-winner set size",
        )
        ax2 = ax.twinx()
        ax2.plot(
            x, modal, "-D", color=HILITE, ms=4, lw=1.6, label="modal-winner frequency"
        )
        ax.set_xticks(x)
        ax.set_xticklabels([f"{float(bb)*100:.0f}%" for bb in bstds])
        ax.set_xlabel("bound uncertainty")
        ax.set_ylabel("# suppliers in class")
        ax.set_ylim(0, max(sizes) + 1)
        ax2.set_ylabel("modal-winner frequency")
        ax2.set_ylim(0, 1.02)
        ax.set_title("(b)", loc="left")
        h1, l1 = ax.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        ax.legend(h1 + h2, l1 + l2, frameon=False, fontsize=7, loc="upper left")
        fig.tight_layout()
        fig.savefig(os.path.join(OUT_FIG, "fig_supplier_interval.pdf"))
        plt.close(fig)

    # --- IIA / rank-reversal bar ------------------------------------------ #
    fc = res["iia_reversal"]
    with publication_style():
        fig, ax = plt.subplots(figsize=(4.8, 3.0))
        keys = ["TOPSIS", "CP", "ASF", "MMR", "LexPR"]
        vals = [fc[k] for k in keys]
        cols = [BASE if k != "LexPR" else HILITE for k in keys]
        ax.bar(keys, vals, color=cols, edgecolor="white", linewidth=0.5)
        ax.set_ylabel("recommendation change rate\n(single-supplier removal)")
        ax.set_ylim(0, max(vals) * 1.25 + 0.02)
        # Title lives in the caption, not in the artwork.
        for i, v in enumerate(vals):
            ax.text(i, v + 0.005, f"{v:.2f}", ha="center", va="bottom", fontsize=7.5)
        ax.grid(True, axis="y", alpha=0.25)
        fig.tight_layout()
        fig.savefig(os.path.join(OUT_FIG, "fig_supplier_iia.pdf"))
        plt.close(fig)


def write_latex_macros(res):
    def cmd(name, val):
        return f"\\newcommand{{\\{name}}}{{{val}}}\n"

    s = "% Auto-generated by scripts/run_supplier_case.py. Do not edit.\n"
    s += cmd("supN", res["n_suppliers"])
    s += cmd("supM", res["n_criteria"])
    s += cmd("supEff", res["n_efficient"])
    s += cmd("supCorrGE", f"{res['corr_ghg_energy']:.3f}")
    s += cmd("supWinner", res["lexpr_winner"])
    s += cmd("supNprobes", res["n_probes"])
    s += cmd("supDistinct", res["n_distinct_picks"])
    iv = res["interval_robust"]
    s += cmd("supPossibleTwenty", iv["0.20"]["stability_class_size"])
    s += cmd("supModalTwenty", f"{iv['0.20']['modal_frequency']*100:.0f}")
    s += cmd("supClassFive", iv["0.05"]["stability_class_size"])
    ns = res["norm_sensitivity"]
    flip20 = next(d["flip_rate"] for d in ns if abs(d["perturb"] - 0.20) < 1e-9)
    s += cmd("supPointFlipTwenty", f"{flip20*100:.0f}")
    fc = res["iia_reversal"]
    s += cmd("supIIALexPR", f"{fc['LexPR']*100:.0f}")
    s += cmd("supIIATOPSIS", f"{fc['TOPSIS']*100:.0f}")
    s += cmd("supIIAASF", f"{fc['ASF']*100:.0f}")
    s += cmd("supIIAInterior", f"{res['iia_interior_fraction']*100:.0f}")
    
    if "relex_diagnostics" in res:
        rd = res["relex_diagnostics"]
        s += cmd("supReLexDecisive", rd["decisive_coordinate"])
        s += cmd("supReLexDeltaCat", str(rd["delta_cat"]))
        s += cmd("supReLexDeltaExact", f"{rd['delta_exact']:.4f}")
        s += cmd("supReLexMuCell", f"{rd['mu_cell']:.4f}")
        s += cmd("supReLexSSevenCM", str(rd["S7_profile_cats"][0]))
        s += cmd("supReLexSSevenCq", str(rd["S7_profile_cats"][1]))
        s += cmd("supReLexSOneCM", str(rd["S1_profile_cats"][0]))
        s += cmd("supReLexSOneCq", str(rd["S1_profile_cats"][1]))
        
    with open(os.path.join(OUT_GEN, "supplier_numbers.tex"), "w") as fh:
        fh.write(s)


if __name__ == "__main__":
    main()
