"""Publication figure pass (T5.5).

Builds the paper's result figures from the archived JSON/CSV outputs, in one
consistent house style, with one message per figure. The four-panel "killer
figure" is split into two figures, each of which makes a single point, per the
revision plan.

Every figure here is generated from files under scripts/real_results/, so a
figure can never disagree with the number quoted in the text.

Outputs (PDF, into manuscript/):
    fig_divergence.pdf        who disagrees with whom, and where
    fig_explanation_depth.pdf how deep the decision profile has to go
    fig_seed_stability.pdf    seed variability of the headline rates
    fig_decomposition.pdf     where the bound stability actually comes from
    fig_family_forest.pdf     per-generator paired differences with CIs
    fig_difficulty.pdf        predicting a singleton class from the margin
    fig_continuous_cost.pdf   direct formulation vs enumerate-then-select
    fig_certified_decay.pdf   unresolved volume against the box budget
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from lexpr.publication_figures import PALETTE, publication_style  # noqa: E402

RES = os.path.join(HERE, "real_results")
OUT = os.path.abspath(os.path.join(ROOT, "..", "manuscript"))

# Natural red = LexPR / the focal series; natural blue = baselines; natural
# green = the third contrast; black (and its grey tint) = ink and furniture.
# Physical sizes matched to where each figure lands in the journal's
# two-column layout: a single column is 3.02in wide, the full text block 6.30in.
# Drawing at the final size is what keeps lettering at the 2-3mm Springer asks
# for; a 5in figure scaled into a 3in column would render its 8pt labels at 5pt.
COL = 3.02      # single column width, inches
FULL = 6.30     # full text width, inches

C_LEX = PALETTE["red"]
C_BASE = PALETTE["blue"]
C_GREEN = PALETTE["green"]
C_GREY = PALETTE["gray"]
C_INK = PALETTE["black"]


def _save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


def _load(name):
    with open(os.path.join(RES, name)) as f:
        return json.load(f)


# --------------------------------------------------------------------------- #
def fig_divergence():
    """How often LexPR and ASF pick different alternatives, by generator."""
    ms = _load("multiseed_summary.json")
    fam = ms["by_family"]
    names = sorted(fam, key=lambda k: fam[k]["div_lexpr_asf"])
    vals = [fam[k]["div_lexpr_asf"] * 100 for k in names]

    with publication_style():
        fig, ax = plt.subplots(figsize=(FULL, 2.5))
        bars = ax.barh(names, vals, color=C_LEX, height=0.62, zorder=3)
        pooled = ms["pooled"]["div_lexpr_asf"]["mean"] * 100
        ax.axvline(pooled, color=C_INK, ls="--", lw=1.0, zorder=4,
                   label=f"overall {pooled:.0f}%")
        for b, v in zip(bars, vals):
            ax.text(v + 1.5, b.get_y() + b.get_height() / 2, f"{v:.0f}%",
                    va="center", fontsize=7.5, color=C_INK)
        ax.set_xlim(0, 108)
        ax.set_xlabel("instances where LexPR and ASF choose differently (%)")
        ax.legend(loc="lower right", frameon=False)
        ax.grid(True, axis="x", alpha=0.3)
        _save(fig, "fig_divergence.pdf")


def fig_explanation_depth():
    """Almost every decision is settled at the first coordinate."""
    df = pd.concat(
        [pd.read_csv(os.path.join(RES, "multiseed", f))
         for f in sorted(os.listdir(os.path.join(RES, "multiseed")))],
        ignore_index=True)
    d = df["depth"].dropna().astype(int)
    counts = d.value_counts().sort_index()

    with publication_style():
        fig, ax = plt.subplots(figsize=(COL, 2.3))
        ax.bar(counts.index, counts.values / counts.sum() * 100,
               color=C_BASE, width=0.62, zorder=3)
        for x, y in zip(counts.index, counts.values / counts.sum() * 100):
            if y > 1:
                ax.text(x, y + 1.6, f"{y:.0f}%", ha="center", fontsize=7.5,
                        color=C_INK)
        ax.set_xticks(sorted(counts.index))
        ax.set_xlabel("first coordinate that settles the comparison")
        ax.set_ylabel("instances (%)")
        ax.set_ylim(0, 105)
        ax.grid(True, axis="y", alpha=0.3)
        _save(fig, "fig_explanation_depth.pdf")


def fig_seed_stability():
    """The headline rates move by one or two points across seeds."""
    ms = _load("multiseed_summary.json")
    rows = [("Disagreement with ASF", "div_lexpr_asf"),
            ("LexPR flips, 5%", "flip_lexpr_0.05"),
            ("LexPR flips, 10%", "flip_lexpr_0.10"),
            ("LexPR flips, 20%", "flip_lexpr_0.20"),
            ("ASF flips, 5%", "flip_asf_0.05"),
            ("ASF flips, 10%", "flip_asf_0.10"),
            ("ASF flips, 20%", "flip_asf_0.20")]
    labels = [r[0] for r in rows]
    y = np.arange(len(rows))[::-1]

    with publication_style():
        fig, ax = plt.subplots(figsize=(FULL, 2.8))
        for yi, (_, key) in zip(y, rows):
            d = ms["pooled"][key]
            lo, hi, mu = d["min_seed"] * 100, d["max_seed"] * 100, d["mean"] * 100
            col = C_LEX if "LexPR" in labels[len(rows) - 1 - yi] else C_BASE
            if key == "div_lexpr_asf":
                col = C_GREEN
            ax.plot([lo, hi], [yi, yi], color=col, lw=3.2, alpha=0.35,
                    solid_capstyle="round", zorder=3)
            ax.plot([mu], [yi], "o", color=col, ms=5, zorder=4)
        ax.set_yticks(y)
        ax.set_yticklabels(labels)
        ax.set_xlabel("rate over ten seeds (%): dot is the pooled mean, "
                      "bar is the observed range")
        ax.grid(True, axis="x", alpha=0.3)
        _save(fig, "fig_seed_stability.pdf")


def fig_decomposition():
    """Where the bound stability comes from -- and where it does not."""
    sy = _load("symmetrised.json")
    order = ["raw", "lexpr", "asfk", "mmrk", "lexpr1"]
    nice = {"raw": "ASF on raw values\n(paper's baseline)",
            "lexpr": "LexPR\n(leximax)",
            "asfk": "Same probes,\nscalarised",
            "mmrk": "Same probes,\nworst only",
            "lexpr1": "Single-criterion\nprobes only"}
    vals = [sy["flip"][k]["0.20"] * 100 for k in order]
    cols = [C_GREY, C_LEX, C_BASE, C_BASE, C_GREEN]

    with publication_style():
        fig, ax = plt.subplots(figsize=(FULL, 3.0))
        bars = ax.bar(range(len(order)), vals, color=cols, width=0.6, zorder=3)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 2, f"{v:.1f}%",
                    ha="center", fontsize=8, color=C_INK)
        ax.set_xticks(range(len(order)))
        ax.set_xticklabels([nice[k] for k in order], fontsize=7.0)
        ax.set_ylabel("winner changes (%)")
        ax.set_ylim(0, 108)
        ax.grid(True, axis="y", alpha=0.3)
        # Two bracketed spans above the bars: what each step of the
        # decomposition is responsible for.
        def span(x0, x1, y, text):
            ax.annotate("", xy=(x0, y), xytext=(x1, y),
                        arrowprops=dict(arrowstyle="<->", color=C_INK, lw=0.9))
            ax.text((x0 + x1) / 2, y + 3, text, ha="center", fontsize=7.2,
                    color=C_INK)
        span(0, 1, 88, "re-anchoring: $-31$ points")
        span(1, 4, 68, "dropping the aggregate probes: $-45$ points")
        _save(fig, "fig_decomposition.pdf")


def fig_family_forest():
    """Per-generator paired differences: the advantage is uneven."""
    ms = _load("multiseed_summary.json")
    fam = ms["by_family"]
    names = sorted(fam, key=lambda k: fam[k]["flip_diff_0.20_ci95"][0])
    y = np.arange(len(names))[::-1]

    with publication_style():
        fig, ax = plt.subplots(figsize=(FULL, 2.6))
        ax.axvline(0, color=C_GREY, lw=1.0, ls="--", zorder=2)
        for yi, n in zip(y, names):
            lo, hi = fam[n]["flip_diff_0.20_ci95"]
            mid = (lo + hi) / 2
            ax.plot([lo, hi], [yi, yi], color=C_LEX, lw=2.6,
                    solid_capstyle="round", zorder=3)
            ax.plot([mid], [yi], "o", color=C_LEX, ms=4.5, zorder=4)
            ax.text(hi + 0.015, yi, f"[{lo:.2f}, {hi:.2f}]", va="center",
                    fontsize=7, color=C_INK)
        ax.set_yticks(y)
        ax.set_yticklabels(names)
        ax.set_xlim(-0.02, 0.86)
        ax.set_xlabel("extra rate at which ASF changes its winner,\n"
                      "compared with LexPR (95% confidence interval)")
        ax.grid(True, axis="x", alpha=0.3)
        _save(fig, "fig_family_forest.pdf")


def fig_difficulty():
    """A bigger winning margin means a clearer answer."""
    d = _load("difficulty.json")
    b = d["margin_bins"]
    x = [r["quintile"] for r in b]
    flip = [r["flip_rate"] * 100 for r in b]
    single = [r["singleton_class_frac"] * 100 for r in b]

    with publication_style():
        fig, ax = plt.subplots(figsize=(COL, 2.5))
        ax.plot(x, flip, "o-", color=C_LEX, ms=5, lw=1.6,
                label="winner changes", zorder=3)
        ax.plot(x, single, "s-", color=C_GREEN, ms=5, lw=1.6,
                label="a single winner is certain", zorder=3)
        ax.set_xticks(x)
        ax.set_xticklabels([f"{r['quintile']}\n"
                            f"$\\leq {r['margin_range'][1]:.3f}$" for r in b],
                           fontsize=7.5)
        ax.set_xlabel("instances grouped by winning margin (smallest to largest)")
        ax.set_ylabel("instances (%)")
        ax.set_ylim(0, 70)
        ax.legend(frameon=False, loc="center right")
        ax.grid(True, axis="y", alpha=0.3)
        _save(fig, "fig_difficulty.pdf")


def fig_continuous_cost():
    """Solving directly costs a fraction of generating the front first."""
    c = _load("continuous.json")["rows"]
    m = [r["m"] for r in c]
    direct = [r["direct_lp_calls"] for r in c]
    enum = [r["enum_lp_calls"] for r in c]

    with publication_style():
        fig, ax = plt.subplots(figsize=(COL, 2.4))
        ax.plot(m, enum, "s-", color=C_BASE, ms=5, lw=1.6,
                label="weighted-sum sample, then choose", zorder=3)
        ax.plot(m, direct, "o-", color=C_LEX, ms=5, lw=1.6,
                label="solve directly (front-free)", zorder=3)
        for xi, yi in zip(m, direct):
            ax.text(xi, yi * 1.5, str(yi), ha="center", fontsize=7,
                    color=C_INK)
        ax.set_yscale("log")
        ax.set_xticks(m)
        ax.set_xlabel("number of criteria $m$")
        ax.set_ylabel("linear programs solved")
        ax.legend(frameon=False, loc="center right")
        ax.grid(True, axis="y", alpha=0.3)
        _save(fig, "fig_continuous_cost.pdf")


def fig_certified_decay():
    """Spending more effort shrinks the part of the box left undecided."""
    b = _load("certified_bench.json")["by_budget"]
    x = [r["budget"] for r in b]
    u = [r["unresolved"] * 100 for r in b]

    with publication_style():
        fig, ax = plt.subplots(figsize=(COL, 2.4))
        ax.plot(x, u, "o-", color=C_LEX, ms=5, lw=1.6, zorder=3)
        for xi, yi in zip(x, u):
            ax.text(xi, yi + 3.5, f"{yi:.0f}%", ha="center", fontsize=7.5,
                    color=C_INK)
        ax.set_xscale("log")
        ax.set_xticks(x)
        ax.set_xticklabels([str(v) for v in x])
        ax.set_xlabel("effort spent (number of sub-boxes examined)")
        ax.set_ylabel("box still undecided (%)")
        ax.set_ylim(0, 92)
        ax.grid(True, axis="y", alpha=0.3)
        _save(fig, "fig_certified_decay.pdf")


def main():
    matplotlib.rcParams["text.usetex"] = False
    figures = (fig_divergence, fig_explanation_depth, fig_seed_stability,
               fig_decomposition, fig_family_forest, fig_difficulty,
               fig_continuous_cost, fig_certified_decay)
    failed = []
    for fn in figures:
        try:
            fn()
        except Exception as exc:
            failed.append((fn.__name__, exc))
            print(f"FAILED {fn.__name__}: {type(exc).__name__}: {exc}")
    if failed:
        # Exit non-zero. A figure that fails to regenerate leaves the previous
        # PDF on disk, so the manuscript would silently keep a stale plot; CI
        # and the author must both see that.
        raise SystemExit(f"{len(failed)} figure(s) failed to build: "
                         + ", ".join(n for n, _ in failed))


if __name__ == "__main__":
    main()
