import math
from fractions import Fraction
import numpy as np

from lexpr.probes import build_probes
from lexpr.disappointments import disappointment_matrix


def tail_cvar(D_sorted: np.ndarray, alpha: float) -> float:
    K = len(D_sorted)
    if K == 0:
        return 0.0
    h = alpha * K
    if h <= 1.0:
        return float(D_sorted[0])
    k = int(math.floor(h))
    theta = h - k
    if theta == 0.0:
        return float(np.sum(D_sorted[:k]) / h)
    else:
        return float((np.sum(D_sorted[:k]) + theta * D_sorted[k]) / h)


def get_category(z: float, delta: str) -> int:
    # Task 5.3 and 7.3: B_delta(z) = ceil(z / delta)
    # Using fractions avoids floating point ambiguity
    return math.ceil(Fraction(z) / Fraction(delta))


def compute_profile(D_row: np.ndarray, resolutions: dict):
    # D_row is shape (K,)
    D_sorted = np.sort(D_row)[::-1]
    M = float(D_sorted[0]) if len(D_sorted) > 0 else 0.0

    T_25 = tail_cvar(D_sorted, 0.25)
    T_50 = tail_cvar(D_sorted, 0.50)
    T_100 = tail_cvar(D_sorted, 1.00)

    C_M = get_category(M, resolutions.get("maximum", "0.01"))
    C_25 = get_category(T_25, resolutions.get("tail_025", "0.01"))
    C_50 = get_category(T_50, resolutions.get("tail_050", "0.01"))
    C_100 = get_category(T_100, resolutions.get("tail_100", "0.01"))

    # Stage 1-7
    # 1. C_M
    # 2. C_25
    # 3. C_50
    # 4. C_100
    # 5. T_25, T_50, T_100
    # 6. M
    # 7. D_sorted
    return (
        C_M,
        C_25,
        C_50,
        C_100,
        T_25,
        T_50,
        T_100,
        M,
        tuple(float(x) for x in D_sorted),
    )


def compare_profiles(p1, p2) -> int:
    # Lexicographic comparison of two profiles
    # Returns -1 if p1 < p2, 1 if p1 > p2, 0 if equal
    for i in range(len(p1)):
        if p1[i] < p2[i]:
            return -1
        elif p1[i] > p2[i]:
            return 1
    return 0


def relex_tail_winner_class(D: np.ndarray, resolutions: dict) -> list[int]:
    N = D.shape[0]
    profiles = [compute_profile(D[i], resolutions) for i in range(N)]

    best_idx = 0
    winners = [0]

    for i in range(1, N):
        cmp = compare_profiles(profiles[i], profiles[best_idx])
        if cmp < 0:
            best_idx = i
            winners = [i]
        elif cmp == 0:
            winners.append(i)

    return winners


def relex_tail(
    F: np.ndarray,
    resolutions: dict,
    theta=0.6,
    ideal=None,
    nadir=None,
    return_detail=False,
    probe_kwargs=None,
    **kw
):
    probe_kwargs = probe_kwargs or {}
    probes, labels = build_probes(F, theta=theta, **probe_kwargs)
    D = disappointment_matrix(F, probes, ideal, nadir)

    winners = relex_tail_winner_class(D, resolutions)
    idx = winners[0]  # Deterministic tie-breaking (first index) or returning the class

    if return_detail:
        return idx, D, labels, probes, winners
    return idx
