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
    
    Uses 10,000 Dirichlet-linear draws as requested."""
    W = rng.dirichlet(np.ones(m), size=n_per_family)  # weights

    fams = {}
    fams["linear"] = lambda r: -(r @ W.T)
    return fams


def precompute_utilities(F, rng, n_per_family=10000):
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


def loss_from_cache(cache, idx, q=0.75, by_family=False):
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


def out_of_class_loss(F, idx, rng, n_per_family=10000, by_family=False):
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
    F, groups, base, idx, rng, n_per_family=10000, by_family=False
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


def tail_loss(F, idx, rng, n_per_family=10000, q=0.75):
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
