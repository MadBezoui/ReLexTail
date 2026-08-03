import numpy as np
import time
from .methods import lexpr_variant


def _tolerance_set(D: np.ndarray, tol: float = 1e-9) -> set[int]:
    sorted_desc = -np.sort(-D, axis=1)
    sorted_desc = np.round(sorted_desc / tol) * tol

    best = 0
    for i in range(1, sorted_desc.shape[0]):
        a, b = sorted_desc[i], sorted_desc[best]
        cmp = np.where(a != b)[0]
        if cmp.size and a[cmp[0]] < b[cmp[0]]:
            best = i

    best_sig = sorted_desc[best]
    is_best = np.all(sorted_desc == best_sig, axis=1)
    return set(np.where(is_best)[0])


def compare_probe_families(
    F: np.ndarray, tolerance: float = 1e-9, theta: float = 0.6
) -> dict:
    t0 = time.perf_counter()
    i_ada, D_ada, labels_ada, _ = lexpr_variant(
        F, variant="adaptive", theta=theta, return_detail=True
    )
    t_ada = time.perf_counter() - t0

    t0 = time.perf_counter()
    i_full, D_full, labels_full, _ = lexpr_variant(
        F, variant="full", return_detail=True
    )
    t_full = time.perf_counter() - t0

    set_ada = _tolerance_set(D_ada, tolerance)
    set_full = _tolerance_set(D_full, tolerance)

    inter = set_ada.intersection(set_full)
    union = set_ada.union(set_full)
    jaccard = len(inter) / len(union) if union else 1.0

    # Worst regret gap
    # If we chose i_ada instead of i_full, what is the maximum regret under full probes?
    # Actually regret gap: max_{q in full} (D_full[i_ada, q] - D_full[i_full, q])
    # But regret is usually measured against the best candidate for each probe.
    # D_full is already disappointment matrix (loss vs best).
    # So regret of i_ada under full probes is D_full[i_ada].max()
    # regret of i_full under full probes is D_full[i_full].max()
    regret_ada = D_full[i_ada].max()
    regret_full = D_full[i_full].max()
    worst_regret_gap = float(regret_ada - regret_full)

    # Certificate sup-norm gap
    # Sort the vectors and take the max absolute difference
    cert_ada = -np.sort(-D_ada[i_ada])
    cert_full = -np.sort(-D_full[i_full])
    # Pad to same length if different, with zeros?
    k_ada = len(cert_ada)
    k_full = len(cert_full)
    k_max = max(k_ada, k_full)

    pad_ada = np.pad(cert_ada, (0, k_max - k_ada))
    pad_full = np.pad(cert_full, (0, k_max - k_full))
    sup_norm_gap = float(np.max(np.abs(pad_ada - pad_full)))

    return {
        "winner_agreement": int(i_ada == i_full),
        "tolerance_jaccard": jaccard,
        "worst_regret_gap": worst_regret_gap,
        "certificate_sup_norm_gap": sup_norm_gap,
        "probes_adaptive": k_ada,
        "probes_full": k_full,
        "time_adaptive": t_ada,
        "time_full": t_full,
    }
