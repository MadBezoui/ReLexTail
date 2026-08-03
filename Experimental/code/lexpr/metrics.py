"""Evaluation metrics.

Key design choice (addresses the Peer-review critique of the original draft):
the *out-of-class loss* is defined as a NON-NEGATIVE regret, lower = better,
measured against held-out utility models that were NOT used by any method during
selection.  It is the normalised gap between the chosen alternative and the best
feasible alternative under each test utility, averaged over a large Monte-Carlo
sample of test utilities.  This is conceptually an SMAA-style acceptability
loss, made comparable across methods.
"""
from __future__ import annotations
import numpy as np
from .methods import normalize, EPS


# --------------------------------------------------------------------------- #
# held-out utility families  (utility = higher is better; r is minimisation)
# --------------------------------------------------------------------------- #
def sample_test_utilities(m, n_per_family, rng):
    """Return {name: fn} where fn(r) yields an (N x T) matrix of held-out
    utilities (higher = better; r is minimisation) for T sampled parameterisations.

    Six families span additive and NON-additive monotone preferences, so the
    evaluation is not biased toward the additive/scalarising logic of the probes:
      linear, weighted Chebyshev, augmented ASF, CES (additive/scalarising);
      choquet  -- 2-additive Choquet integral with random nonneg Mobius masses
                  (criterion interactions; genuinely non-additive);
      satisfice -- threshold/aspiration utility penalising exceedances of random
                  aspiration levels (non-smooth, satisficing behaviour)."""
    W = rng.dirichlet(np.ones(m), size=n_per_family)  # weights
    rho_ces = rng.uniform(2.0, 5.0, size=n_per_family)  # CES curvature
    # 2-additive Choquet: nonneg Mobius masses on singletons + pairs (monotone)
    a = rng.random((n_per_family, m))  # singleton masses
    iu, ju = np.triu_indices(m, k=1)
    b = rng.random((n_per_family, iu.size)) * 0.5  # pair masses
    tau = rng.uniform(0.2, 0.6, size=(n_per_family, m))  # aspiration levels

    fams = {}
    fams["linear"] = lambda r: -(r @ W.T)
    fams["chebyshev"] = lambda r: -np.stack(
        [np.max(W[t] * r, axis=1) for t in range(W.shape[0])], axis=1
    )
    fams["aug_asf"] = lambda r: -np.stack(
        [np.max(W[t] * r, axis=1) + 1e-3 * (r @ W[t]) for t in range(W.shape[0])],
        axis=1,
    )
    fams["ces"] = lambda r: -np.stack(
        [
            (np.sum(W[t] * r ** rho_ces[t], axis=1)) ** (1.0 / rho_ces[t])
            for t in range(W.shape[0])
        ],
        axis=1,
    )

    def choquet(r):
        cols = []
        for t in range(n_per_family):
            cost = r @ a[t] + (np.maximum(r[:, iu], r[:, ju]) @ b[t])
            cols.append(cost)
        return -np.stack(cols, axis=1)

    fams["choquet"] = choquet

    def satisfice(r):
        cols = []
        for t in range(n_per_family):
            cols.append(np.maximum(r - tau[t], 0.0).sum(axis=1))
        return -np.stack(cols, axis=1)

    fams["satisfice"] = satisfice
    return fams


def precompute_utilities(F, rng, n_per_family=250):
    """Sample all held-out utilities ONCE for a candidate set and cache the
    per-utility (best, worst, value) arrays, so many candidates/methods can be
    scored cheaply and on an identical test draw."""
    r = normalize(F)
    m = r.shape[1]
    fams = sample_test_utilities(m, n_per_family, rng)
    cache = {}
    for name, fn in fams.items():
        U = fn(r)  # (N x T)
        best, worst = U.max(axis=0), U.min(axis=0)
        cache[name] = (U, best, worst)
    # stack per-utility normalised losses for the tail metric
    # loss = (best - U) / (best - worst + EPS), in [0, 1], consistent with loss_from_cache
    cache["_all_loss"] = np.concatenate(
        [
            ((cache[n][1] - cache[n][0][:, :]) / (cache[n][1] - cache[n][2] + EPS))
            for n in fams
        ],
        axis=1,
    )  # (N x 4T) losses, >=0
    cache["_families"] = list(fams)
    return cache


def loss_from_cache(cache, idx, q=0.90, by_family=False):
    """Return (mean_loss, tail_loss[, per_family]) for candidate idx from a cache."""
    per = {}
    for name in cache["_families"]:
        U, best, worst = cache[name]
        per[name] = float(((best - U[idx]) / (best - worst + EPS)).mean())
    mean_loss = float(np.mean(list(per.values())))
    L = cache["_all_loss"][idx]
    thr = np.quantile(L, q)
    tail = float(L[L >= thr].mean())
    if by_family:
        return mean_loss, tail, per
    return mean_loss, tail


def out_of_class_loss(F, idx, rng, n_per_family=250, by_family=False):
    """Mean normalised held-out loss (>=0, lower better) of candidate `idx`."""
    r = normalize(F)
    m = r.shape[1]
    fams = sample_test_utilities(m, n_per_family, rng)
    per_fam = {}
    for name, fn in fams.items():
        U = fn(r)  # (N x T)
        best = U.max(axis=0)  # best per test utility
        worst = U.min(axis=0)
        loss = (best - U[idx]) / (best - worst + EPS)  # in [0,1], lower better
        per_fam[name] = float(loss.mean())
    overall = float(np.mean(list(per_fam.values())))
    return (overall, per_fam) if by_family else overall


def out_of_class_loss_grouped(
    F, groups, base, idx, rng, n_per_family=250, by_family=False
):
    """Held-out loss when the DM's TRUE preferences are over the underlying
    criteria (the `base` c-dimensional efficient values), not the redundant raw
    objectives.  A method fooled by redundancy (implicitly over-weighting a
    correlated group) will pick a candidate that scores poorly here.  `idx`
    indexes rows of F/base."""
    from .methods import normalize as _norm

    rb = _norm(base)  # evaluate on TRUE criteria
    c = rb.shape[1]
    fams = sample_test_utilities(c, n_per_family, rng)
    per_fam = {}
    for name, fn in fams.items():
        U = fn(rb)
        best, worst = U.max(axis=0), U.min(axis=0)
        loss = (best - U[idx]) / (best - worst + EPS)
        per_fam[name] = float(loss.mean())
    overall = float(np.mean(list(per_fam.values())))
    return (overall, per_fam) if by_family else overall


def tail_loss(F, idx, rng, n_per_family=250, q=0.90):
    """Worst-case (upper-tail) held-out loss: mean of the worst (1-q) fraction of
    per-utility losses, pooled over all four families (a CVaR-style robustness
    measure).  This is the metric LexPR is designed to minimise."""
    r = normalize(F)
    m = r.shape[1]
    fams = sample_test_utilities(m, n_per_family, rng)
    losses = []
    for fn in fams.values():
        U = fn(r)
        best, worst = U.max(axis=0), U.min(axis=0)
        losses.append((best - U[idx]) / (best - worst + EPS))
    L = np.concatenate(losses)
    thr = np.quantile(L, q)
    return float(L[L >= thr].mean())


def worst_case_regret(F, idx, probe_theta=0.6):
    """Worst disappointment of candidate `idx` over the LexPR probe family."""
    from .probes import build_probes
    from .disappointments import disappointment_matrix

    probes, _ = build_probes(F, theta=probe_theta)
    D = disappointment_matrix(F, probes)
    return float(D[idx].max())


def regret_uniformity(F, idx, probe_theta=0.6):
    from .probes import build_probes
    from .disappointments import disappointment_matrix

    probes, _ = build_probes(F, theta=probe_theta)
    D = disappointment_matrix(F, probes)
    return float(np.std(np.sort(D[idx])))


def is_dominated(F, idx):
    f = F[idx]
    dom = np.all(F <= f, axis=1) & np.any(F < f, axis=1)
    dom[idx] = False
    return bool(dom.any())
