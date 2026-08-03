"""Shared, testable rendering utilities for publication figures."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Iterator, Mapping

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np


# House palette: natural red, natural blue, natural green, black.
#
# These are exactly the colours declared for the TikZ schematics in
# manuscript/preamble_shared.tex (lexprcrimson / lexprblue / lexprgreen /
# lexprslate), so every figure in the paper -- hand-drawn or plotted -- uses one
# palette. No orange, brown, yellow or purple appears anywhere.
#
# `gray` is a tint of black, used only for axis furniture (gridlines, reference
# rules, neutral baseline bars); it carries no hue.
PALETTE = {
    "red": "#C0392B",
    "blue": "#2980B9",
    "green": "#27AE60",
    "black": "#222222",
    "gray": "#7A7A7A",
}

# Backwards-compatible alias. Older scripts refer to OKABE_ITO keys; every
# non-house hue is mapped onto the nearest house colour so that a script written
# against the old palette cannot reintroduce an off-palette colour.
OKABE_ITO = {
    "blue": PALETTE["blue"],
    "orange": PALETTE["red"],  # was #D55E00 vermillion -- now natural red
    "sky": PALETTE["blue"],
    "green": PALETTE["green"],
    "yellow": PALETTE["green"],
    "purple": PALETTE["red"],
    "black": PALETTE["black"],
    "gray": PALETTE["gray"],
}


@contextmanager
def publication_style() -> Iterator[None]:
    """Apply accessible, journal-safe Matplotlib defaults within a context."""
    with mpl.rc_context(
        {
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            # Springer asks for sans-serif figure lettering (Helvetica or
            # Arial). This deliberately differs from the serif body font: the
            # guideline is about legibility at final size, not about matching
            # the running text.
            "font.family": "sans-serif",
            "font.sans-serif": ["Helvetica", "Arial", "Nimbus Sans", "DejaVu Sans"],
            "mathtext.fontset": "cm",
            "font.size": 9,
            "axes.titlesize": 9.5,
            "axes.labelsize": 9,
            "legend.fontsize": 7.5,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 0.7,
            "axes.axisbelow": True,
            "xtick.major.width": 0.7,
            "ytick.major.width": 0.7,
            "grid.linewidth": 0.5,
            "grid.alpha": 0.28,
            "legend.frameon": False,
            "lines.linewidth": 1.6,
            "savefig.bbox": "tight",
            "savefig.dpi": 300,
        }
    ):
        yield


def paired_bootstrap_ci(
    values: Iterable[float],
    *,
    confidence: float = 0.95,
    n_resamples: int = 2000,
    seed: int = 0,
) -> tuple[float, float]:
    """Percentile bootstrap interval for a mean of paired observations."""
    array = np.asarray(list(values), dtype=float)
    if array.ndim != 1 or array.size == 0:
        raise ValueError("values must be a non-empty one-dimensional sequence")
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, array.size, size=(n_resamples, array.size))
    means = array[indices].mean(axis=1)
    alpha = (1.0 - confidence) / 2.0
    low, high = np.quantile(means, [alpha, 1.0 - alpha])
    return float(low), float(high)


def wilson_interval(
    successes: int,
    trials: int,
    *,
    z: float = 1.959963984540054,
) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion."""
    if trials <= 0 or successes < 0 or successes > trials:
        raise ValueError("require 0 <= successes <= trials and trials > 0")
    rate = successes / trials
    scale = 1.0 + z * z / trials
    center = (rate + z * z / (2.0 * trials)) / scale
    half = (
        z * np.sqrt(rate * (1.0 - rate) / trials + z * z / (4.0 * trials**2)) / scale
    )
    lower = 0.0 if successes == 0 else max(0.0, float(center - half))
    upper = 1.0 if successes == trials else min(1.0, float(center + half))
    return lower, upper


def significance_groups(ranks: Mapping[str, float], cd: float) -> list[tuple[str, ...]]:
    """Return maximal contiguous method groups whose rank span is at most CD."""
    ordered = sorted(ranks, key=ranks.get)
    candidates: list[tuple[str, ...]] = []
    for start in range(len(ordered)):
        end = start
        while (
            end + 1 < len(ordered)
            and ranks[ordered[end + 1]] - ranks[ordered[start]] <= cd
        ):
            end += 1
        if end > start:
            candidates.append(tuple(ordered[start : end + 1]))

    maximal: list[tuple[str, ...]] = []
    for group in candidates:
        group_set = set(group)
        if any(group_set < set(other) for other in candidates):
            continue
        if group not in maximal:
            maximal.append(group)
    return maximal


def render_cd_diagram(
    ranks: Mapping[str, float],
    cd: float,
    output_path: str | Path,
    *,
    title: str,
    highlight: str = "LexPR",
) -> Path:
    """Render a collision-resistant Nemenyi critical-difference diagram."""
    output_path = Path(output_path)
    ordered = sorted(ranks, key=ranks.get)
    midpoint = (len(ordered) + 1) // 2
    left = ordered[:midpoint]
    right = ordered[midpoint:]

    with publication_style():
        fig, ax = plt.subplots(figsize=(8.0, 4.2))
        axis_y = 0.64
        lo = 1.0
        hi = max(float(len(ordered)), max(ranks.values()) + 0.5)
        ax.set_xlim(lo - 0.2, hi + 0.2)
        ax.set_ylim(0.0, 1.0)
        ax.hlines(axis_y, lo, hi, color=OKABE_ITO["black"], linewidth=1.0)

        for method, rank in ranks.items():
            ax.vlines(
                rank,
                axis_y - 0.025,
                axis_y + 0.025,
                color=OKABE_ITO["black"],
                linewidth=0.8,
            )

        for row, method in enumerate(left):
            y = 0.50 - row * 0.075
            color = OKABE_ITO["orange"] if method == highlight else OKABE_ITO["black"]
            ax.annotate(
                f"{method}  {ranks[method]:.2f}",
                xy=(ranks[method], axis_y),
                xycoords="data",
                xytext=(0.02, y),
                textcoords="axes fraction",
                ha="left",
                va="center",
                color=color,
                fontweight="bold" if method == highlight else "normal",
                arrowprops={"arrowstyle": "-", "color": "0.55", "lw": 0.6},
            )

        for row, method in enumerate(right):
            y = 0.50 - row * 0.075
            color = OKABE_ITO["orange"] if method == highlight else OKABE_ITO["black"]
            ax.annotate(
                f"{method}  {ranks[method]:.2f}",
                xy=(ranks[method], axis_y),
                xycoords="data",
                xytext=(0.98, y),
                textcoords="axes fraction",
                ha="right",
                va="center",
                color=color,
                fontweight="bold" if method == highlight else "normal",
                arrowprops={"arrowstyle": "-", "color": "0.55", "lw": 0.6},
            )

        for index, group in enumerate(significance_groups(ranks, cd)):
            start = min(ranks[name] for name in group)
            end = max(ranks[name] for name in group)
            y = 0.72 + index * 0.035
            ax.plot(
                [start, end],
                [y, y],
                color=OKABE_ITO["blue"],
                lw=2.4,
                solid_capstyle="round",
            )

        ax.plot([lo, lo + cd], [0.91, 0.91], color=OKABE_ITO["orange"], lw=3)
        ax.text(
            lo + cd / 2,
            0.94,
            f"CD = {cd:.3f}",
            ha="center",
            color=OKABE_ITO["orange"],
            fontsize=8,
        )
        ax.set_title(title)
        ax.text(
            0.5,
            0.58,
            "average rank (lower is better)",
            transform=ax.transAxes,
            ha="center",
            fontsize=8,
        )
        ax.axis("off")
        fig.savefig(output_path)
        plt.close(fig)
    return output_path
