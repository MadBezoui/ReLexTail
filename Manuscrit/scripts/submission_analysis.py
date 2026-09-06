"""Numerical conventions and paired summaries used by the submission revision."""

from __future__ import annotations

import numpy as np
from scipy import stats


def category_index(values, width: float, origin: float = 0.0) -> np.ndarray:
    """Return fixed-cell indices with closed upper endpoints.

    Values at or below ``origin`` are assigned to category zero.  Values above
    the origin use ``ceil((z-origin)/width)``.  Quotients within eight machine
    epsilons of an integer are snapped to that integer so that a floating-point
    representation of an exact declared boundary remains in the lower cell.
    """

    if not np.isfinite(width) or width <= 0:
        raise ValueError("width must be finite and positive")
    if not np.isfinite(origin):
        raise ValueError("origin must be finite")
    z = np.asarray(values, dtype=float)
    if not np.isfinite(z).all():
        raise ValueError("category values must be finite")
    scaled = (z - origin) / width
    nearest = np.rint(scaled)
    tolerance = 8.0 * np.finfo(float).eps * np.maximum(1.0, np.abs(scaled))
    scaled = np.where(np.abs(scaled - nearest) <= tolerance, nearest, scaled)
    return np.where(scaled <= 0.0, 0, np.ceil(scaled)).astype(np.int64)


def lexicographic_argmin(keys) -> int:
    """Return the first row under lexicographic order, breaking ties by row id."""

    a = np.asarray(keys)
    if a.ndim != 2 or a.shape[0] == 0 or a.shape[1] == 0:
        raise ValueError("keys must be a nonempty matrix")
    order = np.lexsort(tuple(a[:, j] for j in range(a.shape[1] - 1, -1, -1)))
    return int(order[0])


def category_winner_set(
    scores,
    width: float,
    *,
    origin_fraction: float = 0.0,
    coordinates: int = 4,
) -> tuple[int, ...]:
    """Return the alternatives tied on the best declared category prefix."""

    a = np.asarray(scores, dtype=float)
    if a.ndim != 2 or a.shape[0] == 0 or not 1 <= coordinates <= a.shape[1]:
        raise ValueError("scores must be nonempty and coordinates must be valid")
    cats = category_index(a[:, :coordinates], width, origin_fraction * width)
    winner = lexicographic_argmin(cats)
    return tuple(np.flatnonzero(np.all(cats == cats[winner], axis=1)).tolist())


def relex_choice(
    scores,
    sorted_disappointments,
    width: float,
    *,
    origin_fraction: float = 0.0,
    coordinates: int = 4,
) -> tuple[int, tuple[int, ...]]:
    """Apply the declared category prefix followed by exact refinements.

    ``scores`` contains the maximum and tail summaries in profile order;
    ``sorted_disappointments`` contains the final exact lexicographic block.
    The returned set is category-optimal before exact refinements.
    """

    a = np.asarray(scores, dtype=float)
    s = np.asarray(sorted_disappointments, dtype=float)
    if a.ndim != 2 or s.ndim != 2 or a.shape[0] == 0 or a.shape[0] != s.shape[0]:
        raise ValueError("scores and sorted disappointments must be aligned matrices")
    if not 1 <= coordinates <= a.shape[1]:
        raise ValueError("coordinates must select a nonempty score prefix")
    cats = category_index(
        a[:, :coordinates], width, origin=origin_fraction * width
    )
    keys = np.column_stack((cats, a[:, 1:], s))
    winner = lexicographic_argmin(keys)
    tied = tuple(np.flatnonzero(np.all(cats == cats[winner], axis=1)).tolist())
    return winner, tied


def holm_adjust(pvalues) -> np.ndarray:
    """Holm-Bonferroni adjusted p-values in their original order."""

    p = np.asarray(pvalues, dtype=float)
    if p.ndim != 1 or p.size == 0 or np.any((p < 0.0) | (p > 1.0)):
        raise ValueError("pvalues must be a nonempty vector in [0, 1]")
    order = np.argsort(p)
    scaled = (p.size - np.arange(p.size)) * p[order]
    monotone = np.minimum(1.0, np.maximum.accumulate(scaled))
    adjusted = np.empty_like(monotone)
    adjusted[order] = monotone
    return adjusted


def paired_effect_summary(
    method,
    reference,
    *,
    bootstrap_replicates: int = 4000,
    seed: int = 42,
) -> dict:
    """Summarise paired, lower-is-better instance effects."""

    x = np.asarray(method, dtype=float)
    y = np.asarray(reference, dtype=float)
    if x.shape != y.shape or x.ndim != 1 or x.size == 0:
        raise ValueError("method and reference must be nonempty paired vectors")
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("paired vectors must be finite")
    if bootstrap_replicates <= 0:
        raise ValueError("bootstrap_replicates must be positive")
    diff = x - y
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, diff.size, size=(bootstrap_replicates, diff.size))
    boot_means = diff[draws].mean(axis=1)
    ci_low, ci_high = np.quantile(boot_means, [0.025, 0.975])
    equal = np.isclose(diff, 0.0, rtol=0.0, atol=1e-15)
    wins = int(np.sum((diff < 0.0) & ~equal))
    losses = int(np.sum((diff > 0.0) & ~equal))
    ties = int(np.sum(equal))
    if np.all(equal):
        statistic, p_value = 0.0, 1.0
    else:
        result = stats.wilcoxon(diff, zero_method="wilcox", alternative="two-sided")
        statistic, p_value = float(result.statistic), float(result.pvalue)
    return {
        "n": int(diff.size),
        "mean_difference": float(diff.mean()),
        "median_difference": float(np.median(diff)),
        "ci_low": float(ci_low),
        "ci_high": float(ci_high),
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "probability_of_superiority": float((wins + 0.5 * ties) / diff.size),
        "wilcoxon_statistic": statistic,
        "wilcoxon_p": p_value,
    }


def pareto_mask(values) -> np.ndarray:
    """Return the nondominated rows of a finite all-minimisation matrix."""

    a = np.asarray(values, dtype=float)
    if a.ndim != 2 or a.shape[0] == 0 or a.shape[1] == 0:
        raise ValueError("values must be a nonempty matrix")
    if not np.isfinite(a).all():
        raise ValueError("values must be finite")
    keep = np.ones(a.shape[0], dtype=bool)
    for i, row in enumerate(a):
        weak = np.all(a <= row, axis=1)
        strict = np.any(a < row, axis=1)
        if np.any(weak & strict):
            keep[i] = False
    return keep
