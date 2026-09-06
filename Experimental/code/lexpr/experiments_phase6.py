import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.datasets import fetch_california_housing

from lexpr import problems, methods, metrics, stats, probes
from lexpr.publication_figures import (
    OKABE_ITO,
    paired_bootstrap_ci,
    publication_style,
    wilson_interval,
)
from lexpr.orders.relex_tail import relex_tail, compute_profile

DELTAS = [0.001, 0.01, 0.05, 0.1, 0.2]
METHODS_TO_TEST = ["TOPSIS", "CP", "WS", "Leximax", "RW", "ASF", "SMAA", "MMR", "LexPR"]


def _eval_method(F, test_seed, n_test, name=None, delta=None, nadir=None, ideal=None, method_seed=None):
    rng = np.random.default_rng(method_seed) if method_seed is not None else None
    if name == "ReLexTail":
        resolutions = {
            k: str(delta) for k in ["maximum", "tail_025", "tail_050", "tail_100"]
        }
        idx = methods.select(
            "ReLexTail", F, resolutions=resolutions, nadir=nadir, ideal=ideal, rng=rng
        )
    else:
        idx = methods.select(name, F, nadir=nadir, ideal=ideal, rng=rng)

    # Manuscript metric: empirical upper-25% CVaR of the range-normalised
    # hidden-preference regret Delta L_w (NOT the mean).  metrics.tail_loss
    # computes exactly CVaR_{0.25}^{up} of (best-U)/(best-worst).
    loss = metrics.tail_loss(
        F, idx, np.random.default_rng(test_seed), n_per_family=n_test, q=0.75
    )
    _, family_loss = metrics.out_of_class_loss(
        F, idx, np.random.default_rng(test_seed), n_per_family=n_test, by_family=True
    )
    return idx, loss, family_loss


def run_quality_stability_frontier(
    reps=10, n=200, m=6, n_test=200, seed=101, outdir="results"
):
    rng_master = np.random.default_rng(seed)
    results = []

    for rep in range(reps):
        rng = np.random.default_rng(int(rng_master.integers(1 << 31)))
        F = problems.make_candidate_set("concave", n, m, rng)
        test_seed = int(rng_master.integers(1 << 31))

        ideal = F.min(axis=0)
        nadir0 = F.max(axis=0)
        active_range = np.maximum(nadir0 - ideal, methods.EPS)
        direction = rng.choice(np.array([-1.0, 1.0]), size=m)
        perturbed_nadir = nadir0 + 0.1 * direction * active_range

        # Test baseline methods
        for name in METHODS_TO_TEST:
            method_seed = int(rng_master.integers(1 << 31))
            idx0, loss0, fam0 = _eval_method(
                F, test_seed, n_test, name=name, nadir=nadir0, ideal=ideal, method_seed=method_seed
            )
            idx1, loss1, fam1 = _eval_method(
                F, test_seed, n_test, name=name, nadir=perturbed_nadir, ideal=ideal, method_seed=method_seed
            )
            results.append(
                {
                    "method": name,
                    "delta": 0,
                    "rep": rep,
                    "is_relex": False,
                    "loss": loss0,
                    "flip": int(idx0 != idx1),
                    "family_loss": fam0,
                }
            )

        # Test ReLexTail
        for d in DELTAS:
            idx0, loss0, fam0 = _eval_method(
                F,
                test_seed,
                n_test,
                name="ReLexTail",
                delta=d,
                nadir=nadir0,
                ideal=ideal,
                method_seed=42, # Deterministic method, but pass for completeness
            )
            idx1, loss1, fam1 = _eval_method(
                F,
                test_seed,
                n_test,
                name="ReLexTail",
                delta=d,
                nadir=perturbed_nadir,
                ideal=ideal,
                method_seed=42,
            )
            results.append(
                {
                    "method": f"ReLexTail(d={d})",
                    "delta": d,
                    "rep": rep,
                    "is_relex": True,
                    "loss": loss0,
                    "flip": int(idx0 != idx1),
                    "family_loss": fam0,
                }
            )

    df = pd.DataFrame(results)

    summary_rows = []
    for method, group in df.groupby("method"):
        row = {
            "method": method,
            "is_relex": group["is_relex"].iloc[0],
            "delta": group["delta"].iloc[0],
            "tail_loss": float(group["loss"].mean()),
            "flip_rate": float(group["flip"].mean()),
        }
        # Average the family losses
        fam_losses = {k: [] for k in group["family_loss"].iloc[0].keys()}
        for fl in group["family_loss"]:
            for k, v in fl.items():
                fam_losses[k].append(v)
        for k, v in fam_losses.items():
            row[f"fam_{k}"] = float(np.mean(v))
        summary_rows.append(row)

    summary = pd.DataFrame(summary_rows)

    # Plotting 2D frontier
    os.makedirs(f"{outdir}/figures", exist_ok=True)
    with publication_style():
        fig, ax = plt.subplots(figsize=(6, 4))

        baselines = summary[~summary["is_relex"]]
        relex = summary[summary["is_relex"]].sort_values("delta")

        ax.scatter(
            baselines["tail_loss"],
            baselines["flip_rate"],
            label="Baselines",
            color=OKABE_ITO["blue"],
        )
        for _, r in baselines.iterrows():
            ax.annotate(
                r["method"], (r["tail_loss"], r["flip_rate"]), fontsize=8, alpha=0.7
            )

        ax.plot(
            relex["tail_loss"],
            relex["flip_rate"],
            "o-",
            label="ReLexTail",
            color=OKABE_ITO["orange"],
        )
        for _, r in relex.iterrows():
            ax.annotate(
                f"d={r['delta']}",
                (r["tail_loss"], r["flip_rate"]),
                fontsize=8,
                alpha=0.7,
            )

        ax.set_xlabel("Upper-tail regret")
        ax.set_ylabel("Point flip rate")
        ax.set_title("Quality–stability trade-off")
        ax.legend()
        fig.tight_layout()
        fig.savefig(f"{outdir}/figures/quality_stability_frontier.pdf")
        plt.close(fig)

    summary.to_csv(f"{outdir}/tables/quality_stability_frontier.csv", index=False)
    return summary


def run_class_evaluation(reps=10, n=200, m=6, n_test=200, seed=102, outdir="results"):
    rng_master = np.random.default_rng(seed)
    results = []

    for rep in range(reps):
        rng = np.random.default_rng(int(rng_master.integers(1 << 31)))
        F = problems.make_candidate_set("concave", n, m, rng)
        test_seed = int(rng_master.integers(1 << 31))

        cache = metrics.precompute_utilities(
            F, np.random.default_rng(test_seed), n_test
        )

        for d in DELTAS:
            resolutions = {
                k: str(d) for k in ["maximum", "tail_025", "tail_050", "tail_100"]
            }
            # call relex_tail with return_detail=True to get winners
            idx, D, labels, probes, winners = methods.select(
                "ReLexTail", F, resolutions=resolutions, return_detail=True
            )

            class_size = len(winners)

            # calculate losses for each member of the class
            class_losses = []
            for w in winners:
                ml, tl = metrics.loss_from_cache(cache, w)
                class_losses.append(tl)  # use tail loss as primary

            # best possible tail loss among all alternatives
            all_losses = []
            for alt in range(n):
                _, tl = metrics.loss_from_cache(cache, alt)
                all_losses.append(tl)
            best_loss = min(all_losses)

            coverage = 1 if min(class_losses) <= best_loss + 1e-6 else 0

            results.append(
                {
                    "delta": d,
                    "class_size": class_size,
                    "opt_class_loss": min(class_losses),
                    "pess_class_loss": max(class_losses),
                    "mean_class_loss": float(np.mean(class_losses)),
                    "coverage": coverage,
                    "reduction_ratio": 1.0 - (class_size / float(n)),
                }
            )

    df = pd.DataFrame(results)
    summary = (
        df.groupby("delta")
        .agg(
            avg_class_size=("class_size", "mean"),
            median_class_size=("class_size", "median"),
            p90_class_size=("class_size", lambda x: np.percentile(x, 90)),
            opt_class_loss=("opt_class_loss", "mean"),
            pess_class_loss=("pess_class_loss", "mean"),
            mean_class_loss=("mean_class_loss", "mean"),
            optimal_alt_coverage=("coverage", "mean"),
            reduction_ratio=("reduction_ratio", "mean"),
        )
        .reset_index()
    )

    summary.to_csv(f"{outdir}/tables/class_evaluation.csv", index=False)
    return summary


def plot_relex_decision_profile(seed=103, outdir="results"):
    from .supplier import load_supplier_case
    F, sup, crit = load_supplier_case()
    resolutions = {k: "0.01" for k in ["maximum", "tail_025", "tail_050", "tail_100"]}
    idx, D, labels, pbs, winners = methods.select(
        "ReLexTail", F, resolutions=resolutions, return_detail=True
    )

    # Extract data for the winner
    D_winner = D[idx]
    sorted_D = np.sort(D_winner)[::-1]

    os.makedirs(f"{outdir}/figures", exist_ok=True)
    with publication_style():
        fig, axes = plt.subplots(3, 1, figsize=(6, 8))

        # Panel A: Labelled probe disappointments
        ax = axes[0]
        y_pos = np.arange(len(D_winner))
        # sort by disappointment to make it look like a spectrum
        sort_idx = np.argsort(D_winner)
        ax.barh(y_pos, D_winner[sort_idx], align="center", color=OKABE_ITO["blue"])
        ax.set_yticks(y_pos)
        ax.set_yticklabels([labels[i][:15] for i in sort_idx], fontsize=6)
        ax.set_xlabel("Disappointment")
        ax.set_title("Panel A: Probe Disappointments")

        # Panel B: Tail spectrum
        ax = axes[1]
        alphas = np.linspace(0.1, 1.0, 100)
        from lexpr.orders.relex_tail import tail_cvar

        t_vals = [tail_cvar(sorted_D, a) for a in alphas]
        ax.plot(alphas, t_vals, color=OKABE_ITO["orange"], lw=2)
        ax.scatter(
            [0.25, 0.5, 1.0],
            [tail_cvar(sorted_D, a) for a in [0.25, 0.5, 1.0]],
            color="red",
            zorder=5,
        )
        ax.set_xlabel(r"Tail fraction $\alpha$")
        ax.set_ylabel(r"Tail Score $T_\alpha(x)$")
        ax.set_title("Panel B: Tail Spectrum")

        # Panel C: Resolution categories
        ax = axes[2]
        prof = compute_profile(D_winner, resolutions)
        # prof: (C_M, C_25, C_50, C_100, T_25, T_50, T_100, M, ...)
        cats = [prof[0], prof[1], prof[2], prof[3]]
        vals = [prof[7], prof[4], prof[5], prof[6]]
        names = ["Maximum", "T_0.25", "T_0.50", "T_1.00"]
        x_pos = np.arange(4)
        ax.bar(x_pos, cats, alpha=0.5, color="gray", label="Category (C)")
        ax2 = ax.twinx()
        ax2.plot(x_pos, vals, "ro-", label="Raw Value")
        ax.set_xticks(x_pos)
        ax.set_xticklabels(names)
        ax.set_ylabel("Category Integer")
        ax2.set_ylabel("Score Value")
        ax.set_title("Panel C: Resolution Categories")

        fig.tight_layout()
        fig.savefig(f"{outdir}/figures/relex_decision_profile.pdf")
        plt.close(fig)


def run_real_case_study(outdir="results"):
    # Load california housing dataset
    data = fetch_california_housing()
    X = data.data
    y = data.target

    # We create a candidate set from a subset to avoid N=20000
    rng = np.random.default_rng(104)
    indices = rng.choice(X.shape[0], size=150, replace=False)

    # Let's say we want to:
    # 1. Maximize Median Income (MedInc) -> minimize -MedInc
    # 2. Minimize HouseAge
    # 3. Maximize AveRooms -> minimize -AveRooms
    # 4. Minimize Population

    F = np.zeros((150, 4))
    F[:, 0] = -X[indices, 0]  # MedInc (index 0)
    F[:, 1] = X[indices, 1]  # HouseAge (index 1)
    F[:, 2] = -X[indices, 2]  # AveRooms (index 2)
    F[:, 3] = X[indices, 4]  # Population (index 4)

    # Normalize F to [0,1] manually for consistent interpretation if needed,
    # though methods.select usually handles it.

    resolutions = {k: "0.02" for k in ["maximum", "tail_025", "tail_050", "tail_100"]}

    # Run ReLexTail
    idx, D, labels, pbs, winners = methods.select(
        "ReLexTail", F, resolutions=resolutions, return_detail=True
    )

    res = {
        "dataset": "California Housing Subset",
        "N": 150,
        "m": 4,
        "delta_used": 0.02,
        "winner_index": int(idx),
        "class_size": len(winners),
    }

    os.makedirs(f"{outdir}/tables", exist_ok=True)
    with open(f"{outdir}/tables/real_case_study.json", "w") as f:
        json.dump(res, f, indent=2)

    return res
