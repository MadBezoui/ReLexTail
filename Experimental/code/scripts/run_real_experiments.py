"""Genuine large-scale experiments for the LexPR manuscript.

Replaces the previously mocked scripts (run_ablation, run_perturbation,
run_knapsack_table flip rates, plot_killer_figure mock data) with real
computation using the actual LexPR / baseline implementations.

Everything is seeded by the master seed 20260628. Outputs:
  scripts/real_results/summary.json   -- every number used in the manuscript
  paper/build/killer_figure.png       -- four real diagnostic panels
Run:  python3 scripts/run_real_experiments.py
"""
from __future__ import annotations
import os, sys, json, time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lexpr import methods, problems, metrics
from lexpr.methods import normalize, EPS, build_probes, correlation_clusters
from lexpr.publication_figures import OKABE_ITO, publication_style

SEED = 20260628
THETA = 0.6
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "real_results")
# The composite four-panel figure this script draws has been superseded in the
# manuscript by the single-message figures of scripts/make_paper_figures_v2.py.
# It is still emitted as a diagnostic. It previously wrote to ../../paper/build,
# a directory that does not exist in this repository layout, so the script
# crashed at the very last step after 30 s of correct computation; the output
# now goes beside the other archived results and the directory is created.
FIG_DIR = os.path.join(RESULTS_DIR, "figures")
FIG_PATH = os.path.join(FIG_DIR, "killer_figure.pdf")
FIG_PATH_PNG = os.path.join(FIG_DIR, "killer_figure.png")
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)

# Benchmark protocol matching Table 2 (experiments_new.tex):
# (label, geometry, n_instances, (m_lo, m_hi), |A| cap)
FAMILIES = [
    ("Knapsack", "knapsack", 100, (3, 5), 300),
    ("Job-shop", "jobshop", 100, (3, 5), 300),
    ("WFG2",     "wfg2",     100, (3, 15), 500),
    ("DTLZ",     "concave",  100, (3, 15), 500),
    ("Energy",   "energy",   50,  (4, 8),  500),
    ("Concrete", "concrete", 50,  (4, 8),  500),
]


def fast_leximax_argmin(D):
    """Vectorised lexicographic-argmin of the descending-sorted regret rows.

    Exact total order on the computed binary64 values; no grid quantisation
    (see lexpr.methods.leximax_argmin for why the grid would be a different
    decision rule)."""
    S = -np.sort(-D, axis=1)
    order = np.lexsort(S.T[::-1])   # primary key = column 0 (worst coordinate)
    return int(order[0]), S


def D_matrix(F, probes, ideal=None, nadir=None):
    r = normalize(F, ideal, nadir)
    cols = []
    for q in probes:
        v = q(r)
        a, b = v.min(), v.max()
        cols.append((v - a) / (b - a + EPS))
    return np.column_stack(cols)


def asf_winner(F, ideal=None, nadir=None, rho=1e-4):
    r = normalize(F, ideal, nadir)
    m = r.shape[1]
    w = np.ones(m) / m
    val = np.max(r / (w + EPS), axis=1) + rho * np.sum(r, axis=1)
    return int(np.argmin(val))


def variant_probes(F, name):
    if name == "adaptive":
        return build_probes(F, theta=THETA)[0]
    if name == "singletons":
        return build_probes(F, use_mean=False, use_max=False, use_clusters=False)[0]
    if name == "no_clusters":
        return build_probes(F, use_clusters=False)[0]
    if name == "no_singletons":
        return build_probes(F, use_singletons=False)[0]
    if name == "grand_mean":
        return [lambda r: r.mean(axis=1)]
    if name == "grand_max":
        return [lambda r: r.max(axis=1)]
    raise ValueError(name)


def explanation_depth(S, winner):
    """Worst-case explanation depth: max over rivals of the first sorted
    coordinate at which the winner's sorted profile beats the rival."""
    w = S[winner]
    K = S.shape[1]
    depths = []
    for i in range(S.shape[0]):
        if i == winner:
            continue
        diff = np.where(w != S[i])[0]
        depths.append(int(diff[0]) + 1 if diff.size else K)
    return max(depths) if depths else 0


def perturb_bounds(F, p, rng):
    """Multiplicative bound perturbation used in the supplement:
    nadir *= 1+u, u~Unif(-p,p); ideal *= 1-u', u'~Unif(0,p); floor nadir>ideal."""
    ideal0 = F.min(axis=0)
    nadir0 = F.max(axis=0)
    m = F.shape[1]
    u = rng.uniform(-p, p, size=m)
    up = rng.uniform(0, p, size=m)
    ideal = ideal0 * (1 - up)
    nadir = nadir0 * (1 + u)
    nadir = np.maximum(nadir, ideal + 1e-3)
    return ideal, nadir


def perturb_bounds_range_proportional(F, p, rng, EPS=1e-9):
    """Perturb bounds proportionally to the active criterion range.
    This provides a scale-coherent uncertainty model (reviewer MC6).
    ideal is shifted down by up * Range, nadir is shifted up by u * Range,
    with up in (0, p) and u in (-p, p)."""
    ideal0 = F.min(axis=0)
    nadir0 = F.max(axis=0)
    R = nadir0 - ideal0
    R = np.maximum(R, EPS)
    m = F.shape[1]
    u = rng.uniform(-p, p, size=m)
    up = rng.uniform(0, p, size=m)
    ideal = ideal0 - up * R
    nadir = nadir0 + u * R
    nadir = np.maximum(nadir, ideal + 1e-3)
    return ideal, nadir


def main():
    rng = np.random.default_rng(SEED)

    ablation_variants = ["singletons", "no_clusters", "no_singletons",
                         "grand_mean", "grand_max", "asf_singleton"]
    div_counts = {v: 0 for v in ablation_variants}
    n_unique = 0
    depths = []
    lexpr_vs_asf_div = 0
    per_inst = []   # (family, m, rho_max, tail_asf, tail_lexpr, div_lexpr_asf)

    levels = [0.05, 0.10, 0.20]
    flip_lexpr = {p: [0, 0] for p in levels}   # [flips, draws]
    flip_asf = {p: [0, 0] for p in levels}
    M_draws = 60

    n_total = 0
    t_start = time.time()
    for label, geom, n_inst, (mlo, mhi), cap in FAMILIES:
        for _ in range(n_inst):
            m = int(rng.integers(mlo, mhi + 1))
            N = int(rng.integers(60, cap + 1))
            F = problems.make_candidate_set(geom, N, m, rng)
            if F.shape[0] < 3:
                continue
            n_total += 1

            probes = build_probes(F, theta=THETA)[0]
            D = D_matrix(F, probes)
            win, S = fast_leximax_argmin(D)

            # uniqueness of winner (for explanation depth)
            unique = not np.any(np.all(S == S[win], axis=1) & (np.arange(S.shape[0]) != win))
            if unique:
                n_unique += 1
                depths.append(explanation_depth(S, win))

            asf_win = asf_winner(F)
            div_la = int(asf_win != win)
            lexpr_vs_asf_div += div_la

            # probe-family ablation divergences (winner vs adaptive winner)
            for v in ablation_variants:
                if v == "asf_singleton":
                    vw = asf_win
                else:
                    vp = variant_probes(F, v)
                    Dv = D_matrix(F, vp)
                    vw, _ = fast_leximax_argmin(Dv)
                if vw != win:
                    div_counts[v] += 1

            # held-out losses (LexPR vs ASF) on a common utility draw
            cache = metrics.precompute_utilities(F, np.random.default_rng(int(rng.integers(1 << 31))),
                                                 n_per_family=200)
            _, tail_lexpr = metrics.loss_from_cache(cache, win)
            _, tail_asf = metrics.loss_from_cache(cache, asf_win)

            # realised max positive off-diagonal correlation (redundancy proxy)
            Fc = F - F.mean(axis=0, keepdims=True)
            nrm = np.linalg.norm(Fc, axis=0)
            valid = nrm > EPS
            rho_max = 0.0
            if valid.sum() >= 2:
                Z = Fc[:, valid] / nrm[valid]
                C = np.clip(Z.T @ Z, -1, 1)
                np.fill_diagonal(C, -1)
                rho_max = float(C.max())

            per_inst.append((label, m, rho_max, tail_asf, tail_lexpr, div_la))

            # bound-perturbation flip rates (LexPR + ASF)
            for p in levels:
                for _d in range(M_draws):
                    idl, ndr = perturb_bounds(F, p, rng)
                    Dp = D_matrix(F, probes, idl, ndr)
                    wl, _ = fast_leximax_argmin(Dp)
                    flip_lexpr[p][0] += int(wl != win)
                    flip_lexpr[p][1] += 1
                    wa = asf_winner(F, idl, ndr)
                    flip_asf[p][0] += int(wa != asf_win)
                    flip_asf[p][1] += 1

    elapsed = time.time() - t_start

    # ---- aggregate ----
    div_rates = {v: div_counts[v] / n_total for v in ablation_variants}
    flip_rate_lexpr = {p: flip_lexpr[p][0] / flip_lexpr[p][1] for p in levels}
    flip_rate_asf = {p: flip_asf[p][0] / flip_asf[p][1] for p in levels}
    per = np.array([(r[3], r[4]) for r in per_inst], dtype=float)  # (tail_asf, tail_lexpr)

    summary = {
        "seed": SEED,
        "n_instances": n_total,
        "n_unique_winner": n_unique,
        "elapsed_sec": round(elapsed, 1),
        "ablation_divergence": {v: round(div_rates[v], 4) for v in ablation_variants},
        "lexpr_vs_asf_divergence": round(lexpr_vs_asf_div / n_total, 4),
        "explanation_depth_mean": round(float(np.mean(depths)), 4),
        "explanation_depth_std": round(float(np.std(depths)), 4),
        "flip_rate_lexpr": {str(p): round(flip_rate_lexpr[p], 4) for p in levels},
        "flip_rate_asf": {str(p): round(flip_rate_asf[p], 4) for p in levels},
        "tail_loss_lexpr_mean": round(float(per[:, 1].mean()), 4),
        "tail_loss_asf_mean": round(float(per[:, 0].mean()), 4),
    }
    with open(os.path.join(RESULTS_DIR, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))

    # ---- killer figure (4 real panels) ----
    rho_arr = np.array([r[2] for r in per_inst])
    div_arr = np.array([r[5] for r in per_inst])
    C_HI = OKABE_ITO["orange"]    # LexPR / focal
    C_BASE = OKABE_ITO["blue"]    # baselines / secondary
    C_GREEN = OKABE_ITO["green"]
    C_SLATE = OKABE_ITO["black"]

    with publication_style():
        fig, ax = plt.subplots(2, 2, figsize=(7.4, 5.6))

        # (a) divergence LexPR vs ASF, binned by realised max correlation
        bins = np.linspace(min(rho_arr.min(), 0), 1.0, 7)
        cx, cy, cn = [], [], []
        for b0, b1 in zip(bins[:-1], bins[1:]):
            msk = (rho_arr >= b0) & (rho_arr < b1)
            if msk.sum() >= 5:
                cx.append((b0 + b1) / 2)
                cy.append(div_arr[msk].mean())
                cn.append(int(msk.sum()))
        a = ax[0, 0]
        a.plot(cx, cy, "o-", color=C_HI, ms=4.5, zorder=3)
        for xv, yv, nv in zip(cx, cy, cn):
            a.annotate(f"$n$={nv}", (xv, yv), textcoords="offset points",
                       xytext=(0, 7), ha="center", fontsize=6.5,
                       color=C_SLATE)
        a.set_title("(a) disagreement with ASF by correlation", loc="left")
        a.set_xlabel(r"realised max positive correlation $\rho$")
        a.set_ylabel("disagreement rate")
        a.set_ylim(0, 1)
        a.grid(True, axis="y")

        # (b) explanation depth histogram
        a = ax[0, 1]
        dmax = max(depths)
        a.hist(depths, bins=[d - 0.5 for d in range(1, dmax + 2)],
               color=C_BASE, rwidth=0.82, zorder=3)
        a.axvline(np.mean(depths), color=C_HI, ls="--", lw=1.2,
                  label=f"mean = {np.mean(depths):.2f}")
        a.set_title("(b) worst-case explanation depth", loc="left")
        a.set_xlabel("deciding coordinate depth")
        a.set_ylabel("instances")
        a.set_xticks(range(1, dmax + 1))
        a.legend(loc="upper right")
        a.grid(True, axis="y")

        # (c) flip rate vs bound uncertainty
        a = ax[1, 0]
        xs = [int(p * 100) for p in levels]
        a.plot(xs, [flip_rate_asf[p] for p in levels], "s-",
               color=C_BASE, ms=4.5, label="ASF", zorder=3)
        a.plot(xs, [flip_rate_lexpr[p] for p in levels], "o-",
               color=C_HI, ms=4.5, label="LexPR", zorder=3)
        a.set_title("(c) point-winner flip rate", loc="left")
        a.set_xlabel("bound perturbation (% of nominal)")
        a.set_ylabel("flip rate over draws")
        a.set_ylim(0, 1)
        a.set_xticks(xs)
        a.legend(loc="upper left")
        a.grid(True, axis="y")

        # (d) held-out tail loss: LexPR vs ASF
        a = ax[1, 1]
        lim_hi = float(max(per.max(), 1.0))
        a.scatter(per[:, 0], per[:, 1], s=9, alpha=0.35, color=C_GREEN,
                  edgecolors="none", zorder=3)
        a.plot([0, lim_hi], [0, lim_hi], ls="--", lw=0.9, color=C_SLATE,
               zorder=2)
        a.set_title("(d) per-instance held-out tail loss", loc="left")
        a.set_xlabel("ASF tail loss")
        a.set_ylabel("LexPR tail loss")
        a.set_xlim(0, lim_hi)
        a.set_ylim(0, lim_hi)
        a.set_aspect("equal", adjustable="box")

        fig.tight_layout(w_pad=2.0, h_pad=1.6)
        fig.savefig(FIG_PATH)
        fig.savefig(FIG_PATH_PNG, dpi=300)
    print("wrote", FIG_PATH)


if __name__ == "__main__":
    main()
