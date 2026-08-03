"""Held-out preference (disutility) families for out-of-class evaluation.

Each family yields, given the normalised candidate matrix r in [0,1]^m
(minimisation), an (N x T) matrix of *utilities* (higher = better) for T sampled
parameterisations.  Families span additive and non-additive monotone preferences
so the evaluation is not biased toward LexPR's additive/scalarising probes.

Weights are drawn from Dirichlet(alpha * 1) to control preference shape:
  alpha = 0.2  -> sparse / extreme   ;  1 -> uniform simplex ;  5 -> balanced.

NONE of these families is used to construct LexPR probes.
"""
from __future__ import annotations
import numpy as np

EPS = 1e-9

ALL_FAMILIES = [
    "linear",
    "sparse_linear",
    "chebyshev",
    "aug_asf",
    "lp_compromise",
    "ces",
    "owa",
    "choquet",
    "satisfice",
    "group_regret",
]


def build_families(m, n_per_family, rng, alpha=1.0, family_list=None):
    family_list = family_list or ALL_FAMILIES
    W = rng.dirichlet(alpha * np.ones(m), size=n_per_family)
    fams = {}

    if "linear" in family_list:
        fams["linear"] = lambda r, W=W: -(r @ W.T)

    if "sparse_linear" in family_list:
        # keep the k largest weights (DM cares about a few criteria)
        k = max(1, m // 3)
        Ws = W.copy()
        for t in range(n_per_family):
            idx = np.argsort(Ws[t])[:-k]
            Ws[t, idx] = 0.0
            s = Ws[t].sum()
            Ws[t] = Ws[t] / s if s > 0 else np.ones(m) / m
        fams["sparse_linear"] = lambda r, Ws=Ws: -(r @ Ws.T)

    # All families below are fully vectorised (no per-utility Python loops):
    # they map r (N x m) to an (N x T) utility matrix via tensor contractions.
    if "chebyshev" in family_list:
        fams["chebyshev"] = lambda r, W=W: -(r[:, None, :] * W[None, :, :]).max(axis=2)

    if "aug_asf" in family_list:
        fams["aug_asf"] = lambda r, W=W: -(
            (r[:, None, :] * W[None, :, :]).max(axis=2) + 0.05 * (r @ W.T)
        )

    if "lp_compromise" in family_list:
        p = rng.uniform(1.5, 4.0, size=n_per_family)

        def lpc(r, W=W, p=p):
            rp = r[:, None, :] ** p[None, :, None]  # N x T x m
            s = (W[None, :, :] * rp).sum(axis=2)  # N x T
            return -(s ** (1.0 / p[None, :]))

        fams["lp_compromise"] = lpc

    if "ces" in family_list:
        rho = rng.uniform(2.0, 5.0, size=n_per_family)

        def ces(r, W=W, rho=rho):
            rp = r[:, None, :] ** rho[None, :, None]
            s = (W[None, :, :] * rp).sum(axis=2)
            return -(s ** (1.0 / rho[None, :]))

        fams["ces"] = ces

    if "owa" in family_list:
        ow = np.sort(rng.dirichlet(np.ones(m), size=n_per_family), axis=1)[:, ::-1]

        def owa(r, ow=ow):
            rs = np.sort(r, axis=1)[:, ::-1]  # N x m descending
            return -(rs @ ow.T)  # N x T

        fams["owa"] = owa

    if "choquet" in family_list:
        a = rng.random((n_per_family, m))
        iu, ju = np.triu_indices(m, k=1)
        b = rng.random((n_per_family, iu.size)) * 0.5

        def choquet(r, a=a, b=b, iu=iu, ju=ju):
            mp = np.maximum(r[:, iu], r[:, ju])  # N x P
            return -(r @ a.T + mp @ b.T)  # N x T

        fams["choquet"] = choquet

    if "satisfice" in family_list:
        tau = rng.uniform(0.2, 0.6, size=(n_per_family, m))

        def satisfice(r, tau=tau):
            return -np.maximum(r[:, None, :] - tau[None, :, :], 0.0).sum(axis=2)

        fams["satisfice"] = satisfice

    if "group_regret" in family_list:
        Wg = rng.dirichlet(alpha * np.ones(m), size=(n_per_family, 3))  # T x 3 x m

        def group_regret(r, Wg=Wg):
            cost = np.einsum("nm,tsm->nts", r, Wg)  # N x T x 3
            return -cost.max(axis=2)  # worst stakeholder

        fams["group_regret"] = group_regret

    return {k: fams[k] for k in family_list if k in fams}


def loss_cache(F, normalize_fn, rng, alpha=1.0, n_per_family=300, family_list=None):
    """Precompute per-utility loss arrays for a candidate set (paired across
    methods). Returns dict with per-family (best,worst,U) and a pooled loss array."""
    r = normalize_fn(F)
    m = r.shape[1]
    fams = build_families(m, n_per_family, rng, alpha, family_list)
    cache = {"_families": list(fams)}
    pooled = []
    for name, fn in fams.items():
        U = fn(r)
        best, worst = U.max(axis=0), U.min(axis=0)
        cache[name] = (U, best, worst)
        pooled.append((best[None, :] - U) / (best - worst + EPS))  # (N x T) loss>=0
    cache["_pooled"] = np.concatenate(pooled, axis=1)
    return cache


def losses_from(cache, idx, q=0.90):
    """Return (mean_loss, tail_loss, worst_family_loss, per_family_dict)."""
    per = {}
    for name in cache["_families"]:
        U, best, worst = cache[name]
        per[name] = float(((best - U[idx]) / (best - worst + EPS)).mean())
    mean_loss = float(np.mean(list(per.values())))
    worst_family = float(max(per.values()))
    L = cache["_pooled"][idx]
    thr = np.quantile(L, q)
    tail = float(L[L >= thr].mean())
    return mean_loss, tail, worst_family, per
