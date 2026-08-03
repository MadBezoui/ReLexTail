import numpy as np
import pandas as pd


def cluster_bootstrap_difference(
    frame, control, treatment, cluster_columns, seed, n_boot=10000, alpha=0.05
):
    """
    Cluster bootstrap difference in mean tail_loss (or other metric).
    frame must contain 'method', 'tail_loss', and the cluster_columns.
    Returns (mean_diff, ci_lower, ci_upper, reversal_fraction).
    """
    rng = np.random.default_rng(seed)

    pivot = (
        frame[frame["method"].isin([control, treatment])]
        .pivot(index=cluster_columns, columns="method", values="tail_loss")
        .dropna()
    )

    diffs = (
        pivot[control] - pivot[treatment]
    ).values  # >0 if control > treatment (treatment is better)
    n_clusters = len(diffs)

    if n_clusters == 0:
        return 0.0, 0.0, 0.0, 0.0

    indices = rng.integers(0, n_clusters, size=(n_boot, n_clusters))
    boot_diffs = diffs[indices].mean(axis=1)

    mean_diff = float(diffs.mean())
    ci_lower = float(np.percentile(boot_diffs, 100 * (alpha / 2)))
    ci_upper = float(np.percentile(boot_diffs, 100 * (1 - alpha / 2)))

    if mean_diff > 0:
        reversal = float((boot_diffs < 0).mean())
    else:
        reversal = float((boot_diffs > 0).mean())

    return mean_diff, ci_lower, ci_upper, reversal
