"""Generate publication figures from validated result tables."""

from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(REPO_ROOT / "code"))

from lexpr.figure_evidence import figure_provenance, write_sidecar
from lexpr.publication_figures import (
    OKABE_ITO,
    publication_style,
    render_cd_diagram,
)

TAB = REPO_ROOT / "results" / "tables"
OUT_DIRS = [REPO_ROOT / "paper", REPO_ROOT / "results" / "figures"]


def _source_metadata(paths):
    return {
        str(Path(path).relative_to(REPO_ROOT)): sha256(
            Path(path).read_bytes()
        ).hexdigest()
        for path in paths
    }


def save(fig, name, *, sources):
    params = {"figure": name, "sources": _source_metadata(sources)}
    metadata = figure_provenance(REPO_ROOT, run_id=None, params=params)
    for directory in OUT_DIRS:
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / name
        fig.savefig(path)
        write_sidecar(path, metadata)
    plt.close(fig)
    print("wrote", name)


def _yerr(frame, mean, lower, upper):
    center = frame[mean].to_numpy(float)
    return np.vstack(
        [
            center - frame[lower].to_numpy(float),
            frame[upper].to_numpy(float) - center,
        ]
    )


def fig_tradeoff():
    source = TAB / "main_comparison.csv"
    df = pd.read_csv(source)
    cluster = ["CP", "ASF", "MMR", "LexPR", "TOPSIS"]
    offsets = {
        "CP": (-24, 5),
        "TOPSIS": (5, 6),
        "ASF": (5, 6),
        "MMR": (-30, -11),
        "LexPR": (5, -12),
        "Knee": (5, 5),
        "RW": (-18, -13),
        "SMAA": (5, 5),
    }
    zoom_offsets = {
        "CP": (5, 5),
        "TOPSIS": (-24, 7),
        "ASF": (5, 6),
        "MMR": (-27, -11),
        "LexPR": (5, -11),
    }
    with publication_style():
        fig, axes = plt.subplots(
            1, 2, figsize=(7.4, 3.5), gridspec_kw={"width_ratios": [1.2, 1]}
        )
        for ax, methods, title in (
            (axes[0], list(df["method"]), "All selection rules"),
            (axes[1], cluster, "Robust cluster (zoom)"),
        ):
            subset = df[df["method"].isin(methods)]
            for _, row in subset.iterrows():
                is_lexpr = row["method"] == "LexPR"
                ax.scatter(
                    row["loss_mean"],
                    row["tail_loss"],
                    s=70 if is_lexpr else 40,
                    marker="D" if is_lexpr else "o",
                    color=OKABE_ITO["orange"] if is_lexpr else OKABE_ITO["blue"],
                    edgecolor="white",
                    linewidth=0.6,
                    zorder=3,
                )
                ax.annotate(
                    row["method"],
                    (row["loss_mean"], row["tail_loss"]),
                    textcoords="offset points",
                    xytext=(zoom_offsets if ax is axes[1] else offsets)[row["method"]],
                    fontsize=7.5,
                    color=OKABE_ITO["orange"] if is_lexpr else OKABE_ITO["black"],
                    fontweight="bold" if is_lexpr else "normal",
                )
            ax.set_title(title)
            ax.set_xlabel("mean held-out loss")
            ax.grid(True, alpha=0.2)
        axes[0].set_ylabel("tail held-out loss (CVaR$_{10\%}$)")
        axes[1].set_xlim(0.198, 0.257)
        axes[1].set_ylim(0.462, 0.55)
        fig.suptitle("Average- versus tail-loss trade-off", fontsize=10)
        fig.tight_layout()
        save(fig, "fig_tradeoff.pdf", sources=[source])


def fig_perfamily():
    source = TAB / "per_family_concave_m8.csv"
    df = pd.read_csv(source).set_index("method")
    fams = ["linear", "chebyshev", "aug_asf", "ces", "choquet", "satisfice", "overall"]
    labels = [
        "linear",
        "Chebyshev",
        "aug. ASF",
        "CES",
        "Choquet",
        "satisfice",
        "overall",
    ]
    values = df.loc[:, fams].to_numpy(float)
    with publication_style():
        fig, ax = plt.subplots(figsize=(7.2, 4.2))
        mesh = ax.pcolormesh(
            np.arange(values.shape[1] + 1),
            np.arange(values.shape[0] + 1),
            values,
            cmap="viridis_r",
            shading="flat",
            edgecolors="white",
            linewidth=0.6,
        )
        ax.set_xlim(0, values.shape[1])
        ax.set_ylim(values.shape[0], 0)
        ax.set_xticks(np.arange(len(fams)) + 0.5, labels, rotation=30, ha="right")
        ax.set_yticks(np.arange(len(df.index)) + 0.5, df.index)
        midpoint = (values.min() + values.max()) / 2
        for i in range(values.shape[0]):
            for j in range(values.shape[1]):
                ax.text(
                    j + 0.5,
                    i + 0.5,
                    f"{values[i, j]:.2f}",
                    ha="center",
                    va="center",
                    fontsize=7.5,
                    color="white" if values[i, j] > midpoint else "black",
                )
        lexpr_row = list(df.index).index("LexPR")
        ax.add_patch(
            plt.Rectangle(
                (0, lexpr_row),
                len(fams),
                1,
                fill=False,
                edgecolor=OKABE_ITO["orange"],
                lw=2.0,
            )
        )
        ax.set_title(
            "Held-out loss by preference family (concave, $m=8$; lower is better)"
        )
        fig.colorbar(mesh, ax=ax, fraction=0.028, pad=0.02, label="loss")
        fig.tight_layout()
        save(fig, "fig_perfamily.pdf", sources=[source])


def fig_redundancy():
    source = TAB / "redundancy.csv"
    df = pd.read_csv(source)
    x = np.arange(len(df))
    width = 0.37
    with publication_style():
        fig, ax = plt.subplots(figsize=(7.0, 4.0))
        colors = [
            OKABE_ITO["orange"] if method == "LexPR" else OKABE_ITO["blue"]
            for method in df["method"]
        ]
        ax.bar(
            x - width / 2,
            df["grouped_loss"],
            width,
            yerr=_yerr(df, "grouped_loss", "grouped_lower", "grouped_upper"),
            capsize=2,
            color=colors,
            hatch="//",
            label="grouped loss (95% CI)",
        )
        ax.bar(
            x + width / 2,
            df["tail_loss"],
            width,
            yerr=_yerr(df, "tail_loss", "tail_lower", "tail_upper"),
            capsize=2,
            color=colors,
            alpha=0.55,
            label="tail loss (95% CI)",
        )
        ax.set_xticks(x, df["method"])
        ax.set_ylabel("loss (lower is better)")
        ax.set_title("Robustness to redundant criteria")
        handles, labels = ax.get_legend_handles_labels()
        handles.append(Patch(facecolor=OKABE_ITO["orange"], label="LexPR highlight"))
        labels.append("LexPR highlight")
        ax.legend(handles, labels, frameon=False, ncol=3, loc="upper center")
        ax.grid(True, axis="y", alpha=0.2)
        fig.tight_layout()
        save(fig, "fig_redundancy.pdf", sources=[source])


def fig_nadir():
    source = TAB / "sensitivity_nadir.csv"
    df = pd.read_csv(source)
    x = df["realized_rms_error"] * 100
    with publication_style():
        fig, ax1 = plt.subplots(figsize=(6.2, 4.0))
        loss = df["loss_change"]
        ax1.errorbar(
            x,
            loss,
            yerr=_yerr(df, "loss_change", "loss_change_lower", "loss_change_upper"),
            color=OKABE_ITO["blue"],
            marker="o",
            capsize=2,
            label="paired held-out loss change",
        )
        ax1.axhline(0, color="0.5", linewidth=0.7)
        ax1.set_xlabel("realized RMS nadir perturbation (%)")
        ax1.set_ylabel("paired held-out loss change", color=OKABE_ITO["blue"])
        ax2 = ax1.twinx()
        rate = df["flip_rate"] * 100
        ax2.errorbar(
            x,
            rate,
            yerr=np.vstack(
                [rate - df["flip_lower"] * 100, df["flip_upper"] * 100 - rate]
            ),
            color=OKABE_ITO["orange"],
            marker="s",
            linestyle="--",
            capsize=2,
            label="winner-change rate",
        )
        ax2.set_ylim(0, 105)
        ax2.set_ylabel("winner-change rate (%)", color=OKABE_ITO["orange"])
        ax1.set_title("Nadir sensitivity: quality and identity are paired diagnostics")
        fig.tight_layout()
        save(fig, "fig_nadir.pdf", sources=[source])


def fig_probe_reduction():
    source = TAB / "probe_reduction.csv"
    df = pd.read_csv(source)
    with publication_style():
        fig, ax = plt.subplots(figsize=(6.2, 4.0))
        ax.plot(
            df["m"],
            df["full_coalitions"],
            "o-",
            color=OKABE_ITO["blue"],
            lw=2,
            label="full coalition family $2(2^m-1)-m$",
        )
        ax.plot(
            df["m"],
            df["cluster_probes"],
            "s-",
            color=OKABE_ITO["orange"],
            lw=2,
            label="adaptive family $m+2+2c$",
        )
        ax.set_yscale("log")
        ax.set_xlabel("number of criteria $m$")
        ax.set_ylabel("probe-family size (log scale)")
        ax.set_title("Probe-family size and realized cluster count")
        for _, row in df.iterrows():
            ax.annotate(
                f"c={int(row['nontrivial_clusters'])}",
                (row["m"], row["cluster_probes"]),
                xytext=(0, -14),
                textcoords="offset points",
                ha="center",
                fontsize=7,
            )
            ax.annotate(
                f"{row['reduction']:.0f}$\\times$",
                (row["m"], row["full_coalitions"]),
                xytext=(0, 6),
                textcoords="offset points",
                ha="center",
                fontsize=7,
            )
        ax.legend(frameon=False, loc="upper left")
        ax.grid(True, which="both", alpha=0.18)
        fig.tight_layout()
        save(fig, "fig_probe_reduction.pdf", sources=[source])


def fig_ablation():
    source = TAB / "ablation_concave_m8.csv"
    df = pd.read_csv(source)
    x = np.arange(len(df))
    width = 0.38
    with publication_style():
        fig, ax = plt.subplots(figsize=(7.0, 4.0))
        ax.bar(
            x - width / 2,
            df["loss_mean"],
            width,
            yerr=_yerr(df, "loss_mean", "loss_lower", "loss_upper"),
            capsize=2,
            color=OKABE_ITO["blue"],
            label="mean held-out loss (95% CI)",
        )
        ax.bar(
            x + width / 2,
            df["wcr_mean"],
            width,
            yerr=_yerr(df, "wcr_mean", "wcr_lower", "wcr_upper"),
            capsize=2,
            color=OKABE_ITO["orange"],
            alpha=0.75,
            label="worst certificate regret (95% CI)",
        )
        ax.set_xticks(x, df["config"], rotation=20, ha="right")
        ax.set_ylabel("normalized value (lower is better)")
        ax.set_title("Probe-family ablations, including null results")
        ax.legend(frameon=False)
        ax.grid(True, axis="y", alpha=0.2)
        fig.tight_layout()
        save(fig, "fig_ablation.pdf", sources=[source])


def fig_smaa_distinct():
    source = TAB / "agreement_smaa.csv"
    df = pd.read_csv(source)
    distance = df.pivot(index="geometry", columns="m", values="mean_rms_distance")
    agreement = df.pivot(index="geometry", columns="m", values="agreement")
    overlap = df.pivot(index="geometry", columns="m", values="tolerance_jaccard")
    with publication_style():
        fig, ax = plt.subplots(figsize=(6.8, 4.0))
        mesh = ax.pcolormesh(
            np.arange(distance.shape[1] + 1),
            np.arange(distance.shape[0] + 1),
            distance.values,
            cmap="viridis",
            shading="flat",
            edgecolors="white",
            linewidth=0.7,
            vmin=0,
            vmax=1,
        )
        ax.set_xlim(0, distance.shape[1])
        ax.set_ylim(distance.shape[0], 0)
        ax.set_xticks(
            np.arange(distance.shape[1]) + 0.5,
            [f"m={value}" for value in distance.columns],
        )
        ax.set_yticks(np.arange(distance.shape[0]) + 0.5, distance.index)
        for i in range(distance.shape[0]):
            for j in range(distance.shape[1]):
                ax.text(
                    j + 0.5,
                    i + 0.5,
                    f"RMS {distance.values[i,j]:.2f}\nexact {agreement.values[i,j]*100:.0f}%\nset J {overlap.values[i,j]:.2f}",
                    ha="center",
                    va="center",
                    fontsize=6.8,
                    color="white",
                )
        ax.set_title("LexPR versus SMAA recommendations")
        fig.colorbar(
            mesh,
            ax=ax,
            fraction=0.04,
            pad=0.03,
            label="RMS normalized criterion distance",
        )
        fig.tight_layout()
        save(fig, "fig_smaa_distinct.pdf", sources=[source])


def fig_stochastic():
    source = TAB / "stochastic_consistency.csv"
    df = pd.read_csv(source)
    with publication_style():
        fig, ax = plt.subplots(figsize=(5.8, 3.5))
        for prefix, mean_col, label, color, marker in (
            ("exact", "exact_recovery", "exact winner", OKABE_ITO["blue"], "o"),
            (
                "tolerance",
                "tolerance_coverage",
                "$\\tau$-class coverage",
                OKABE_ITO["orange"],
                "s",
            ),
        ):
            y = df[mean_col]
            ax.errorbar(
                df["n_obs"],
                y,
                yerr=np.vstack([y - df[f"{prefix}_lower"], df[f"{prefix}_upper"] - y]),
                color=color,
                marker=marker,
                capsize=2,
                label=label,
            )
        ax.set_xscale("log")
        ax.set_ylim(0, 1.02)
        ax.set_xlabel("observations per criterion $n$ (log scale)")
        ax.set_ylabel("recovery / coverage rate")
        ax.set_title("Confidence-aware LexPR recovery ($m=6$, $\\alpha=0.95$)")
        ax.legend(frameon=False)
        fig.tight_layout()
        save(fig, "stochastic_consistency.pdf", sources=[source])


def fig_cd_mechanistic():
    source = TAB / "stats_summary.json"
    payload = json.loads(source.read_text())
    tail = payload["tail_loss"]
    for directory in OUT_DIRS:
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "cd_diagram.pdf"
        render_cd_diagram(
            tail["avg_ranks"],
            tail["cd"],
            path,
            title="Tail held-out loss ranks: controlled mechanistic study",
        )
        write_sidecar(
            path,
            figure_provenance(
                REPO_ROOT,
                run_id=None,
                params={
                    "figure": "cd_diagram.pdf",
                    "sources": _source_metadata([source]),
                },
            ),
        )
    print("wrote cd_diagram.pdf")


def main():
    fig_tradeoff()
    fig_perfamily()
    fig_redundancy()
    fig_nadir()
    fig_probe_reduction()
    fig_ablation()
    fig_smaa_distinct()
    fig_stochastic()
    fig_cd_mechanistic()


if __name__ == "__main__":
    main()
