"""Benchmark orchestration: replicated comparison, ablations, sensitivity,
probe-reduction, plus table (CSV + LaTeX) and figure generation."""
from __future__ import annotations
import os, json
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from . import problems, methods, metrics, stats, probes
from .probe_validation import _tolerance_set
from .publication_figures import (
    OKABE_ITO,
    paired_bootstrap_ci,
    publication_style,
    render_cd_diagram,
    wilson_interval,
)

GEOMS = ["linear", "concave", "convex", "disconnected"]
MS = [3, 5, 8, 10]
METHOD_ORDER = [
    "TOPSIS",
    "CP",
    "Knee",
    "WS",
    "Leximax",
    "RW",
    "ASF",
    "SMAA",
    "MMR",
    "LexPR",
    "ReLexTail_0.02",
    "ReLexTail_0.01",
    "ReLexTail_0.005",
]


def rms_choice_distance(a, b):
    """Dimension-comparable RMS distance between normalized criterion vectors."""
    delta = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    if delta.ndim != 1 or delta.size == 0:
        raise ValueError("choice vectors must be non-empty and one-dimensional")
    return float(np.sqrt(np.mean(delta**2)))


def confidence_adjusted_objectives(mu, sd, n_obs, z=1.6449):
    """Upper confidence objective using the standard error of the sample mean."""
    if n_obs <= 0:
        raise ValueError("n_obs must be positive")
    return np.asarray(mu) + z * np.asarray(sd) / np.sqrt(n_obs)


def _smaa_tolerance_set(acceptability, expected_value, tolerance=1e-4):
    top_acceptability = float(np.max(acceptability))
    candidates = np.flatnonzero(acceptability >= top_acceptability - tolerance)
    top_expected = float(np.max(expected_value[candidates]))
    return set(
        int(i) for i in candidates if expected_value[i] >= top_expected - tolerance
    )


# --------------------------------------------------------------------------- #
def _select(name, F, rng):
    if name.startswith("ReLexTail_"):
        delta = float(name.split("_")[1])
        resolutions = {k: str(delta) for k in ["maximum", "tail_025", "tail_050", "tail_100"]}
        return methods.select("ReLexTail", F, rng=rng, resolutions=resolutions)
    return methods.select(name, F, rng=rng)


def run_benchmark_clean(reps=30, n=300, n_test=250, seed=20240601, outdir="results"):
    """Replicated out-of-class loss for every method x geometry x m.
    The held-out test-utility draw is identical across methods within a
    replication, so comparisons are paired."""
    rng_master = np.random.default_rng(seed)
    rows, mean_store, tail_store = [], {}, {}
    for geom in GEOMS:
        for m in MS:
            mmat = np.zeros((reps, len(METHOD_ORDER)))
            tmat = np.zeros((reps, len(METHOD_ORDER)))
            for rep in range(reps):
                rng = np.random.default_rng(rng_master.integers(1 << 31))
                F = problems.make_candidate_set(geom, n, m, rng)
                cache = metrics.precompute_utilities(
                    F, np.random.default_rng(int(rng_master.integers(1 << 31))), n_test
                )
                sel_rng = np.random.default_rng(int(rng_master.integers(1 << 31)))
                for jm, name in enumerate(METHOD_ORDER):
                    idx = _select(name, F, rng=sel_rng)
                    mmat[rep, jm], tmat[rep, jm] = metrics.loss_from_cache(cache, idx)
            mean_store[(geom, m)] = mmat
            tail_store[(geom, m)] = tmat
            for jm, name in enumerate(METHOD_ORDER):
                mc, tc = mmat[:, jm], tmat[:, jm]
                rows.append(
                    dict(
                        geometry=geom,
                        m=m,
                        method=name,
                        mean=mc.mean(),
                        std=mc.std(),
                        tail_mean=tc.mean(),
                        tail_std=tc.std(),
                        median=float(np.median(mc)),
                        iqr=float(np.subtract(*np.percentile(mc, [75, 25]))),
                    )
                )
    df = pd.DataFrame(rows)
    os.makedirs(f"{outdir}/tables", exist_ok=True)
    df.to_csv(f"{outdir}/tables/benchmark_raw.csv", index=False)
    np.savez(
        f"{outdir}/tables/loss_store.npz",
        **{f"mean_{g}_{m}": mean_store[(g, m)] for g in GEOMS for m in MS},
        **{f"tail_{g}_{m}": tail_store[(g, m)] for g in GEOMS for m in MS},
    )
    return df, mean_store, tail_store


def _stats_block(store, control="LexPR"):
    big = np.vstack(list(store.values()))
    fried_stat, fried_p = stats.friedman(big)
    ranks = stats.average_ranks(big)
    cd = stats.nemenyi_cd(len(METHOD_ORDER), big.shape[0])
    wh = stats.wilcoxon_holm(big, METHOD_ORDER, control=control)
    return (
        dict(
            friedman_stat=fried_stat,
            friedman_p=fried_p,
            n_datasets=int(big.shape[0]),
            cd=cd,
            avg_ranks={n: float(r) for n, r in zip(METHOD_ORDER, ranks)},
            wilcoxon_vs_LexPR={
                n: dict(p_raw=v[0], p_holm=v[1], cliffs_delta=v[2])
                for n, v in wh.items()
            },
        ),
        ranks,
        cd,
    )


def stats_summary(mean_store, tail_store, outdir="results"):
    """Friedman + Wilcoxon-Holm vs LexPR + CD diagram, for BOTH the mean-loss and
    the tail (worst-case) loss.  Tail loss is the headline robustness metric."""
    mean_block, _, _ = _stats_block(mean_store)
    tail_block, tail_ranks, cd = _stats_block(tail_store)
    summary = dict(mean_loss=mean_block, tail_loss=tail_block)
    os.makedirs(f"{outdir}/tables", exist_ok=True)
    with open(f"{outdir}/tables/stats_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    _cd_diagram(tail_ranks, cd, outdir)  # CD diagram on the headline metric
    return summary


def _cd_diagram(ranks, cd, outdir):
    os.makedirs(f"{outdir}/figures", exist_ok=True)
    render_cd_diagram(
        dict(zip(METHOD_ORDER, ranks)),
        cd,
        f"{outdir}/figures/cd_diagram.pdf",
        title="Tail held-out loss ranks: controlled mechanistic study",
    )


REDUNDANCY_CONFIGS = {
    "R1 (5 groups, m=10)": [3, 3, 2, 1, 1],
    "R2 (4 groups, m=10)": [4, 3, 2, 1],
    "R3 (4 groups, m=12)": [5, 4, 2, 1],
    "R4 (3 groups, m=12)": [6, 4, 2],
}


def run_redundancy(reps=30, n=300, n_test=300, seed=909, outdir="results"):
    """Realistic redundant-objective benchmark: held-out preferences are over the
    TRUE underlying criteria.  Reports grouped loss (de-redundification quality)
    and tail loss.  This is where adaptive clustering earns its keep."""
    rng_master = np.random.default_rng(seed)
    rows = {}
    store_grp = {}
    observation_rows = []
    for cfg, sizes in REDUNDANCY_CONFIGS.items():
        for geom in ["linear", "concave", "convex"]:
            gmat = np.zeros((reps, len(METHOD_ORDER)))
            tmat = np.zeros((reps, len(METHOD_ORDER)))
            for rep in range(reps):
                rng = np.random.default_rng(rng_master.integers(1 << 31))
                F, groups, base = problems.make_redundant_set(geom, n, sizes, rng)
                s1 = int(rng_master.integers(1 << 31))
                s2 = int(rng_master.integers(1 << 31))
                cache_base = metrics.precompute_utilities(
                    base, np.random.default_rng(s1), n_test
                )
                cache_F = metrics.precompute_utilities(
                    F, np.random.default_rng(s2), n_test
                )
                sel_rng = np.random.default_rng(int(rng_master.integers(1 << 31)))
                for jm, name in enumerate(METHOD_ORDER):
                    idx = _select(name, F, rng=sel_rng)
                    gmat[rep, jm] = metrics.loss_from_cache(cache_base, idx)[0]
                    tmat[rep, jm] = metrics.loss_from_cache(cache_F, idx)[1]
            store_grp[(cfg, geom)] = gmat
            for jm, name in enumerate(METHOD_ORDER):
                rows.setdefault(name, {"grp": [], "tail": []})
                rows[name]["grp"].append(gmat[:, jm].mean())
                rows[name]["tail"].append(tmat[:, jm].mean())
                for rep in range(reps):
                    observation_rows.append(
                        {
                            "config": cfg,
                            "geometry": geom,
                            "replication": rep,
                            "method": name,
                            "grouped_loss": float(gmat[rep, jm]),
                            "tail_loss": float(tmat[rep, jm]),
                        }
                    )
    observations = pd.DataFrame(observation_rows)
    summary_rows = []
    for method_index, name in enumerate(METHOD_ORDER):
        method_obs = observations[observations["method"] == name]
        grouped_ci = paired_bootstrap_ci(
            method_obs["grouped_loss"], seed=seed + method_index
        )
        tail_ci = paired_bootstrap_ci(
            method_obs["tail_loss"], seed=seed + 100 + method_index
        )
        summary_rows.append(
            {
                "method": name,
                "grouped_loss": float(method_obs["grouped_loss"].mean()),
                "grouped_std": float(method_obs["grouped_loss"].std(ddof=0)),
                "grouped_lower": grouped_ci[0],
                "grouped_upper": grouped_ci[1],
                "tail_loss": float(method_obs["tail_loss"].mean()),
                "tail_std": float(method_obs["tail_loss"].std(ddof=0)),
                "tail_lower": tail_ci[0],
                "tail_upper": tail_ci[1],
            }
        )
    df = pd.DataFrame(summary_rows)
    os.makedirs(f"{outdir}/tables", exist_ok=True)
    df.to_csv(f"{outdir}/tables/redundancy.csv", index=False)
    observations.to_csv(f"{outdir}/tables/redundancy_observations.csv", index=False)
    big = np.vstack([store_grp[k] for k in store_grp])
    blk, ranks, cd = _stats_block(store_grp)
    with open(f"{outdir}/tables/redundancy_stats.json", "w") as f:
        json.dump(blk, f, indent=2)
    return df, blk


def per_family_table(
    reps=30, n=300, n_test=400, seed=7, outdir="results", geom="concave", m=8
):
    """Out-of-class loss broken down by held-out utility family for one setting."""
    rng_master = np.random.default_rng(seed)
    _fams = ["linear", "chebyshev", "aug_asf", "ces", "choquet", "satisfice"]
    acc = {name: {fam: [] for fam in _fams} for name in METHOD_ORDER}
    for rep in range(reps):
        rng = np.random.default_rng(rng_master.integers(1 << 31))
        F = problems.make_candidate_set(geom, n, m, rng)
        test_seed = int(rng_master.integers(1 << 31))
        sel_rng = np.random.default_rng(int(rng_master.integers(1 << 31)))
        for name in METHOD_ORDER:
            idx = _select(name, F, rng=sel_rng)
            _, per = metrics.out_of_class_loss(
                F,
                idx,
                np.random.default_rng(test_seed),
                n_per_family=n_test,
                by_family=True,
            )
            for fam, v in per.items():
                acc[name][fam].append(v)
    fam_names = ["linear", "chebyshev", "aug_asf", "ces", "choquet", "satisfice"]
    rows = []
    for name in METHOD_ORDER:
        row = dict(method=name)
        for fam in fam_names:
            row[fam] = float(np.mean(acc[name][fam]))
        row["overall"] = float(np.mean([row[f] for f in fam_names]))
        rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(f"{outdir}/tables/per_family_{geom}_m{m}.csv", index=False)
    return df


def worstcase_table(reps=30, n=300, seed=11, outdir="results", geom="concave", m=8):
    """Worst-case regret + regret uniformity by method (LexPR's own certificate)."""
    rng_master = np.random.default_rng(seed)
    acc = {name: {"wcr": [], "ru": []} for name in METHOD_ORDER}
    for rep in range(reps):
        rng = np.random.default_rng(rng_master.integers(1 << 31))
        F = problems.make_candidate_set(geom, n, m, rng)
        sel_rng = np.random.default_rng(int(rng_master.integers(1 << 31)))
        for name in METHOD_ORDER:
            idx = _select(name, F, rng=sel_rng)
            acc[name]["wcr"].append(metrics.worst_case_regret(F, idx))
            acc[name]["ru"].append(metrics.regret_uniformity(F, idx))
    rows = [
        dict(
            method=n_,
            wcr_mean=float(np.mean(acc[n_]["wcr"])),
            wcr_std=float(np.std(acc[n_]["wcr"])),
            ru_mean=float(np.mean(acc[n_]["ru"])),
        )
        for n_ in METHOD_ORDER
    ]
    df = pd.DataFrame(rows)
    df.to_csv(f"{outdir}/tables/worstcase_{geom}_m{m}.csv", index=False)
    return df


def ablation_table(
    reps=30, n=300, n_test=400, seed=23, outdir="results", geom="concave", m=8
):
    """Ablate LexPR probe components; report overall out-of-class loss + WCR."""
    configs = {
        "Full LexPR": dict(),
        "No clustering": dict(use_clusters=False),
        "No singletons": dict(use_singletons=False),
        "Mean only": dict(use_max=False),
        "Max only": dict(use_mean=False),
    }
    rng_master = np.random.default_rng(seed)
    acc = {c: {"loss": [], "wcr": []} for c in configs}
    for rep in range(reps):
        rng = np.random.default_rng(rng_master.integers(1 << 31))
        F = problems.make_candidate_set(geom, n, m, rng)
        test_seed = int(rng_master.integers(1 << 31))
        for c, pk in configs.items():
            idx = methods.lexpr(F, probe_kwargs=pk)
            acc[c]["loss"].append(
                metrics.out_of_class_loss(
                    F, idx, np.random.default_rng(test_seed), n_per_family=n_test
                )
            )
            acc[c]["wcr"].append(metrics.worst_case_regret(F, idx))
    rows = []
    observation_rows = []
    for config_index, config in enumerate(configs):
        loss_ci = paired_bootstrap_ci(acc[config]["loss"], seed=seed + config_index)
        wcr_ci = paired_bootstrap_ci(acc[config]["wcr"], seed=seed + 100 + config_index)
        rows.append(
            {
                "config": config,
                "loss_mean": float(np.mean(acc[config]["loss"])),
                "loss_std": float(np.std(acc[config]["loss"])),
                "loss_lower": loss_ci[0],
                "loss_upper": loss_ci[1],
                "wcr_mean": float(np.mean(acc[config]["wcr"])),
                "wcr_std": float(np.std(acc[config]["wcr"])),
                "wcr_lower": wcr_ci[0],
                "wcr_upper": wcr_ci[1],
            }
        )
        observation_rows.extend(
            {
                "replication": rep,
                "config": config,
                "loss": float(loss),
                "wcr": float(wcr),
            }
            for rep, (loss, wcr) in enumerate(
                zip(acc[config]["loss"], acc[config]["wcr"])
            )
        )
    df = pd.DataFrame(rows)
    os.makedirs(f"{outdir}/tables", exist_ok=True)
    df.to_csv(f"{outdir}/tables/ablation_{geom}_m{m}.csv", index=False)
    pd.DataFrame(observation_rows).to_csv(
        f"{outdir}/tables/ablation_{geom}_m{m}_observations.csv", index=False
    )
    return df


def probe_reduction_table(n=400, seed=3, outdir="results"):
    """Full coalition count (3*2^m - ...) vs. adaptive cluster-probe count."""
    rng = np.random.default_rng(seed)
    rows = []
    for m in [3, 5, 8, 10, 15]:
        F = problems.make_candidate_set("concave", n, m, rng)
        probes_list, labels = probes.build_probes(F, theta=0.6)
        clusters = probes.correlation_clusters(F, theta=0.6)
        nontrivial_clusters = sum(len(cluster) > 1 for cluster in clusters)
        # full family = {mean_S, max_S : non-empty S subset of {1..m}};
        # mean and max coincide on singletons, so the count is 2(2^m-1)-m.
        full = 2 * (2**m - 1) - m
        rows.append(
            dict(
                m=m,
                full_coalitions=full,
                nontrivial_clusters=nontrivial_clusters,
                cluster_probes=len(labels),
                reduction=round(full / len(labels), 1),
            )
        )
    df = pd.DataFrame(rows)
    os.makedirs(f"{outdir}/tables", exist_ok=True)
    df.to_csv(f"{outdir}/tables/probe_reduction.csv", index=False)
    return df


def sensitivity_theta(reps=20, n=300, n_test=300, seed=31, outdir="results", m=8):
    """theta sensitivity across ALL four geometries (addresses the concern that
    robustness was only shown on one geometry)."""
    thetas = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    fig, ax = plt.subplots(figsize=(5.5, 3.2))
    out = {"theta": thetas}
    for geom in GEOMS:
        rng_master = np.random.default_rng(seed + hash(geom) % 1000)
        means = []
        for th in thetas:
            vals = []
            for rep in range(reps):
                rng = np.random.default_rng(rng_master.integers(1 << 31))
                F = problems.make_candidate_set(geom, n, m, rng)
                test_seed = int(rng_master.integers(1 << 31))
                idx = methods.lexpr(F, theta=th)
                vals.append(
                    metrics.out_of_class_loss(
                        F, idx, np.random.default_rng(test_seed), n_per_family=n_test
                    )
                )
            means.append(float(np.mean(vals)))
        ax.plot(thetas, means, marker="o", label=geom)
        out[geom] = means
    ax.set_xlabel(r"clustering threshold $\theta$")
    ax.set_ylabel("out-of-class loss")
    ax.legend(fontsize=8)
    ax.set_title(
        f"LexPR sensitivity to $\\theta$ across geometries (m={m})", fontsize=9
    )
    fig.tight_layout()
    os.makedirs(f"{outdir}/figures", exist_ok=True)
    fig.savefig(f"{outdir}/figures/sensitivity_theta.pdf")
    plt.close(fig)
    pd.DataFrame(out).to_csv(f"{outdir}/tables/sensitivity_theta.csv", index=False)
    return out


def stochastic_demo(
    reps=40,
    n=200,
    m=6,
    seed=71,
    outdir="results",
    obs_grid=(1, 2, 5, 10, 20, 50, 100),
    resamples=5,
    alpha=0.95,
    tolerance=1e-4,
):
    """Recovery of confidence-aware LexPR as observations per criterion grow."""
    if alpha != 0.95:
        raise ValueError("the publication experiment fixes alpha=0.95")
    z = 1.6449
    rng_master = np.random.default_rng(seed)
    observations = []
    for problem_id in range(reps):
        problem_seed = int(rng_master.integers(1 << 31))
        Ftrue = problems.make_candidate_set(
            "concave", n, m, np.random.default_rng(problem_seed)
        )
        true_idx, Dtrue, _, _ = methods.lexpr(Ftrue, return_detail=True)
        true_set = _tolerance_set(Dtrue, tolerance)
        noise = 0.15 * (Ftrue.std(axis=0) + 1e-6)
        for nobs in obs_grid:
            for resample in range(resamples):
                sample_seed = int(rng_master.integers(1 << 31))
                sample_rng = np.random.default_rng(sample_seed)
                samples = Ftrue[None, :, :] + noise[
                    None, None, :
                ] * sample_rng.standard_normal((nobs, n, m))
                mu_hat = samples.mean(axis=0)
                sd_hat = samples.std(axis=0, ddof=1 if nobs > 1 else 0)
                adjusted = confidence_adjusted_objectives(mu_hat, sd_hat, nobs, z=z)
                idx = methods.lexpr(adjusted)
                observations.append(
                    {
                        "problem_id": problem_id,
                        "resample": resample,
                        "n_obs": int(nobs),
                        "exact_recovered": int(idx == true_idx),
                        "tolerance_covered": int(idx in true_set),
                    }
                )

    obs = pd.DataFrame(observations)
    rows = []
    for nobs, group in obs.groupby("n_obs", sort=True):
        trials = len(group)
        exact = int(group["exact_recovered"].sum())
        covered = int(group["tolerance_covered"].sum())
        exact_ci = wilson_interval(exact, trials)
        tolerance_ci = wilson_interval(covered, trials)
        rows.append(
            {
                "n_obs": int(nobs),
                "trials": trials,
                "exact_recovery": exact / trials,
                "exact_lower": exact_ci[0],
                "exact_upper": exact_ci[1],
                "tolerance_coverage": covered / trials,
                "tolerance_lower": tolerance_ci[0],
                "tolerance_upper": tolerance_ci[1],
            }
        )
    summary = pd.DataFrame(rows)

    os.makedirs(f"{outdir}/figures", exist_ok=True)
    os.makedirs(f"{outdir}/tables", exist_ok=True)
    with publication_style():
        fig, ax = plt.subplots(figsize=(5.5, 3.4))
        for prefix, label, color, marker in (
            ("exact", "exact winner", OKABE_ITO["blue"], "o"),
            ("tolerance", "noise-free $\\tau$-class", OKABE_ITO["orange"], "s"),
        ):
            y = (
                summary[f"{prefix}_recovery"]
                if prefix == "exact"
                else summary["tolerance_coverage"]
            )
            low = summary[f"{prefix}_lower"]
            high = summary[f"{prefix}_upper"]
            ax.errorbar(
                summary["n_obs"],
                y,
                yerr=np.vstack([y - low, high - y]),
                marker=marker,
                color=color,
                capsize=2,
                label=label,
            )
        ax.set_xscale("log")
        ax.set_ylim(0, 1.02)
        ax.set_xlabel("observations per criterion $n$")
        ax.set_ylabel("recovery / coverage rate")
        ax.set_title(f"Confidence-aware LexPR recovery (concave, $m={m}$)")
        ax.legend(frameon=False)
        fig.savefig(f"{outdir}/figures/stochastic_consistency.pdf")
        plt.close(fig)
    summary.to_csv(f"{outdir}/tables/stochastic_consistency.csv", index=False)
    obs.to_csv(f"{outdir}/tables/stochastic_consistency_observations.csv", index=False)
    return summary


def sensitivity_nadir(
    reps=20,
    n=300,
    n_test=300,
    seed=37,
    outdir="results",
    geom="concave",
    m=8,
    error_levels=(0.0, 0.05, 0.1, 0.2, 0.3, 0.5),
    return_observations=False,
):
    """Paired sensitivity to an RMS-scaled nadir perturbation direction."""
    rng_master = np.random.default_rng(seed)
    observations = []
    for problem_id in range(reps):
        problem_rng = np.random.default_rng(int(rng_master.integers(1 << 31)))
        F = problems.make_candidate_set(geom, n, m, problem_rng)
        test_seed = int(rng_master.integers(1 << 31))
        ideal = F.min(axis=0)
        nadir0 = F.max(axis=0)
        active_range = np.maximum(nadir0 - ideal, methods.EPS)
        direction = problem_rng.choice(np.array([-1.0, 1.0]), size=m)
        idx0 = methods.lexpr(F, ideal=ideal, nadir=nadir0)
        baseline_loss = metrics.out_of_class_loss(
            F,
            idx0,
            np.random.default_rng(test_seed),
            n_per_family=n_test,
        )
        for error_level in error_levels:
            perturbed = nadir0 + float(error_level) * direction * active_range
            idx = methods.lexpr(F, ideal=ideal, nadir=perturbed)
            loss = metrics.out_of_class_loss(
                F,
                idx,
                np.random.default_rng(test_seed),
                n_per_family=n_test,
            )
            realized = float(
                np.sqrt(np.mean(((perturbed - nadir0) / active_range) ** 2))
            )
            observations.append(
                {
                    "problem_id": problem_id,
                    "error_level": float(error_level),
                    "realized_rms_error": realized,
                    "loss": float(loss),
                    "loss_change": float(loss - baseline_loss),
                    "winner_changed": int(idx != idx0),
                }
            )

    obs = pd.DataFrame(observations)
    rows = []
    for error_level, group in obs.groupby("error_level", sort=True):
        loss_ci = paired_bootstrap_ci(group["loss_change"], seed=seed)
        changed = int(group["winner_changed"].sum())
        flip_ci = wilson_interval(changed, len(group))
        rows.append(
            {
                "nadir_err": float(error_level),
                "realized_rms_error": float(group["realized_rms_error"].mean()),
                "loss": float(group["loss"].mean()),
                "loss_change": float(group["loss_change"].mean()),
                "loss_change_lower": loss_ci[0],
                "loss_change_upper": loss_ci[1],
                "flip_rate": changed / len(group),
                "flip_lower": flip_ci[0],
                "flip_upper": flip_ci[1],
            }
        )
    summary = pd.DataFrame(rows)

    os.makedirs(f"{outdir}/figures", exist_ok=True)
    os.makedirs(f"{outdir}/tables", exist_ok=True)
    with publication_style():
        fig, ax1 = plt.subplots(figsize=(5.5, 3.4))
        x = summary["realized_rms_error"] * 100
        y = summary["loss_change"]
        ax1.errorbar(
            x,
            y,
            yerr=np.vstack(
                [y - summary["loss_change_lower"], summary["loss_change_upper"] - y]
            ),
            marker="o",
            color=OKABE_ITO["blue"],
            capsize=2,
            label="paired held-out loss change",
        )
        ax1.axhline(0, color="0.5", linewidth=0.7)
        ax1.set_xlabel("realized RMS nadir perturbation (%)")
        ax1.set_ylabel("paired held-out loss change", color=OKABE_ITO["blue"])
        ax2 = ax1.twinx()
        rate = summary["flip_rate"] * 100
        ax2.errorbar(
            x,
            rate,
            yerr=np.vstack(
                [
                    rate - summary["flip_lower"] * 100,
                    summary["flip_upper"] * 100 - rate,
                ]
            ),
            marker="s",
            linestyle="--",
            color=OKABE_ITO["orange"],
            capsize=2,
            label="winner-change rate",
        )
        ax2.set_ylim(0, 105)
        ax2.set_ylabel("winner-change rate (%)", color=OKABE_ITO["orange"])
        ax1.set_title("Nadir sensitivity: paired quality and identity diagnostics")
        fig.savefig(f"{outdir}/figures/sensitivity_nadir.pdf")
        plt.close(fig)
    summary.to_csv(f"{outdir}/tables/sensitivity_nadir.csv", index=False)
    obs.to_csv(f"{outdir}/tables/sensitivity_nadir_observations.csv", index=False)
    if return_observations:
        return summary, obs
    return summary


def agreement_with_smaa(reps=40, n=300, seed=41, outdir="results"):
    """How often does LexPR's recommendation coincide with SMAA's, and how far
    apart are they when they differ (objective-space distance)."""
    rng_master = np.random.default_rng(seed)
    rows = []
    for geom in GEOMS:
        for m in MS:
            agree, dists, overlaps = 0, [], []
            for rep in range(reps):
                rng = np.random.default_rng(rng_master.integers(1 << 31))
                F = problems.make_candidate_set(geom, n, m, rng)
                i_lexpr, D_lexpr, _, _ = methods.lexpr(F, return_detail=True)
                i_smaa, acceptability, expected = methods.smaa(
                    F, rng=np.random.default_rng(99 + rep), return_detail=True
                )
                if i_lexpr == i_smaa:
                    agree += 1
                r = methods.normalize(F)
                dists.append(rms_choice_distance(r[i_lexpr], r[i_smaa]))
                lexpr_set = _tolerance_set(D_lexpr, 1e-4)
                smaa_set = _smaa_tolerance_set(acceptability, expected, 1e-4)
                union = lexpr_set | smaa_set
                overlaps.append(len(lexpr_set & smaa_set) / len(union))
            rows.append(
                dict(
                    geometry=geom,
                    m=m,
                    agreement=agree / reps,
                    mean_rms_distance=float(np.mean(dists)),
                    tolerance_jaccard=float(np.mean(overlaps)),
                )
            )
    df = pd.DataFrame(rows)
    df.to_csv(f"{outdir}/tables/agreement_smaa.csv", index=False)
    return df


def dominated_exclusion_check(trials=200, n=200, seed=5):
    """Empirically verify Corollary 2.1: LexPR never selects a dominated point."""
    rng = np.random.default_rng(seed)
    violations = 0
    for _ in range(trials):
        m = int(rng.integers(3, 9))
        geom = GEOMS[int(rng.integers(0, len(GEOMS)))]
        F = problems.make_candidate_set(geom, n, m, rng, n_dominated=30)
        idx = methods.lexpr(F)
        if metrics.is_dominated(F, idx):
            violations += 1
    return dict(trials=trials, violations=violations)


from .experiments_phase6 import *
