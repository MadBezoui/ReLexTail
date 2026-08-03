import numpy as np

from lexpr.probes import build_probes, build_full_probes, build_random_probes
from lexpr.disappointments import disappointment_matrix

EPS = 1e-9


def winner_class(D: np.ndarray, atol: float = 0.0) -> frozenset[int]:
    S = -np.sort(-D, axis=1)
    live = np.ones(S.shape[0], dtype=bool)
    for k in range(S.shape[1]):
        col = np.where(live, S[:, k], np.inf)
        best = col.min()
        live &= col <= best + atol
    return frozenset(int(i) for i in np.flatnonzero(live))


def leximax_argmin(D: np.ndarray) -> int:
    sorted_desc = -np.sort(-D, axis=1)
    best = 0
    for i in range(1, sorted_desc.shape[0]):
        a, b = sorted_desc[i], sorted_desc[best]
        cmp = np.where(a != b)[0]
        if cmp.size and a[cmp[0]] < b[cmp[0]]:
            best = i
    return int(best)


def lexpr(
    F, theta=0.6, ideal=None, nadir=None, return_detail=False, probe_kwargs=None, **kw
):
    probe_kwargs = probe_kwargs or {}
    probes, labels = build_probes(F, theta=theta, **probe_kwargs)
    D = disappointment_matrix(F, probes, ideal, nadir)
    idx = leximax_argmin(D)
    if return_detail:
        return idx, D, labels, probes
    return idx


def lexpr_interval(
    F, n_bounds=100, bounds_std=0.1, rng=None, theta=0.6, return_set=False, **kw
):
    rng = np.random.default_rng(0) if rng is None else rng
    m = F.shape[1]
    ideal_base = F.min(axis=0)
    nadir_base = F.max(axis=0)
    range_base = np.maximum(nadir_base - ideal_base, EPS)

    winners = []
    for _ in range(n_bounds):
        jitter_i = rng.uniform(0, bounds_std, size=m)
        jitter_n = rng.uniform(0, bounds_std, size=m)
        ideal = ideal_base - jitter_i * range_base
        nadir = nadir_base + jitter_n * range_base
        winners.append(lexpr(F, theta=theta, ideal=ideal, nadir=nadir))

    counts = np.bincount(winners, minlength=F.shape[0])
    best = int(np.argmax(counts))
    if return_set:
        stability_set = np.where(counts > 0)[0].tolist()
        return best, stability_set
    return best


def stability_envelope(
    F, tolerance=0.01, theta=0.6, ideal=None, nadir=None, probe_kwargs=None
):
    probe_kwargs = probe_kwargs or {}
    probes, _ = build_probes(F, theta=theta, **probe_kwargs)
    D = disappointment_matrix(F, probes, ideal, nadir)
    max_regret = D.max(axis=1)
    min_max_regret = max_regret.min()
    return np.where(max_regret <= min_max_regret + tolerance)[0].tolist()


def lexpr_variant(
    F,
    variant="adaptive",
    rng=None,
    theta=0.6,
    return_detail=False,
    ideal=None,
    nadir=None,
    **kw
):
    rng = np.random.default_rng(0) if rng is None else rng
    if variant == "adaptive":
        probes, labels = build_probes(F, theta=theta)
    elif variant == "full":
        probes, labels = build_full_probes(F)
    elif variant == "singletons":
        probes, labels = build_probes(
            F, use_mean=False, use_max=False, use_clusters=False
        )
    elif variant == "no_singletons":
        probes, labels = build_probes(F, use_singletons=False)
    elif variant == "max_only":
        probes, labels = build_probes(F, use_mean=False)
    elif variant == "cluster_only":
        probes, labels = build_probes(
            F, use_singletons=False, use_mean=True, use_max=True
        )
    elif variant == "random":
        k = len(build_probes(F, theta=theta)[1])
        probes, labels = build_random_probes(F, k, rng)
    elif variant == "no_clusters":
        probes, labels = build_probes(F, use_clusters=False)
    else:
        raise ValueError(variant)

    D = disappointment_matrix(F, probes, ideal=ideal, nadir=nadir)
    idx = leximax_argmin(D)
    if return_detail:
        return idx, D, labels, probes
    return idx
