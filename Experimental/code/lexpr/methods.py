"""Selection methods operating on a finite candidate set.

Every method takes an (N x m) objective matrix `F` (minimisation) and returns
the *index* of the recommended candidate.  All methods operate on the normalised
matrix r in [0,1]^m unless noted.

Implemented:
    Classical post-processing : topsis, compromise_programming, knee_point,
                                random_weights, asf
    Robust MCDA               : smaa, minimax_regret   (Savage regret over a
                                linear weight set)
    Proposed                  : lexpr  (Lexicographic Probe-Regret core, with
                                adaptive correlation-clustering probes)
"""
from __future__ import annotations
import numpy as np

from lexpr.disappointments import normalize
from lexpr.orders.lexpr import lexpr, lexpr_variant, lexpr_interval
from lexpr.orders.relex_tail import relex_tail

EPS = 1e-9


# --------------------------------------------------------------------------- #
# classical post-processing methods
# --------------------------------------------------------------------------- #
def topsis(F, w=None, **kw):
    r = normalize(F)
    m = r.shape[1]
    w = np.ones(m) / m if w is None else np.asarray(w)
    v = r * w
    d_best = np.linalg.norm(v - v.min(axis=0), axis=1)  # to ideal (0)
    d_worst = np.linalg.norm(v - v.max(axis=0), axis=1)  # to nadir (1)
    closeness = d_worst / (d_best + d_worst + EPS)
    return int(np.argmax(closeness))


def compromise_programming(F, w=None, p=2, **kw):
    r = normalize(F)
    m = r.shape[1]
    w = np.ones(m) / m if w is None else np.asarray(w)
    dist = (np.sum(w * r**p, axis=1)) ** (1.0 / p)  # L_p to ideal (0)
    return int(np.argmin(dist))


def knee_point(F, **kw):
    """Distance-to-hyperplane knee: plane through the m extreme points
    (best-in-one-objective); pick the candidate farthest below it (toward ideal)."""
    r = normalize(F)
    m = r.shape[1]
    extremes = np.array([r[np.argmax(r[:, i])] for i in range(m)])
    try:
        a = np.linalg.solve(extremes, np.ones(m))  # plane a^T r = 1
        dist = 1.0 - r @ a  # >0 below the plane
        return int(np.argmax(dist))
    except np.linalg.LinAlgError:
        import logging

        logging.warning(
            "knee_point hyperplane fit failed; falling back to compromise_programming."
        )
        return compromise_programming(F)


def random_weights(F, n_weights=200, rng=None, **kw):
    """Pick the candidate most frequently optimal across random linear weights
    (a simple robustness-by-popularity baseline)."""
    rng = np.random.default_rng(0) if rng is None else rng
    r = normalize(F)
    m = r.shape[1]
    W = rng.dirichlet(np.ones(m), size=n_weights)
    winners = np.argmin(r @ W.T, axis=0)  # best per weight
    counts = np.bincount(winners, minlength=r.shape[0])
    return int(np.argmax(counts))


def asf(F, w=None, rho=1e-4, **kw):
    """Augmented achievement scalarising function, reference point = ideal."""
    r = normalize(F)
    m = r.shape[1]
    w = np.ones(m) / m if w is None else np.asarray(w)
    val = np.max(r / (w + EPS), axis=1) + rho * np.sum(r, axis=1)
    return int(np.argmin(val))


def vikor(F, w=None, v=0.5, **kw):
    """VIKOR compromise ranking; recommend the top-ranked Q alternative."""
    r = normalize(F)
    m = r.shape[1]
    w = np.ones(m) / m if w is None else np.asarray(w)
    S = (w * r).sum(axis=1)  # group utility (already 0..)
    R = (w * r).max(axis=1)  # individual regret
    Sm, SM = S.min(), S.max()
    Rm, RM = R.min(), R.max()
    Q = v * (S - Sm) / (SM - Sm + EPS) + (1 - v) * (R - Rm) / (RM - Rm + EPS)
    return int(np.argmin(Q))


def hypervolume_pick(F, **kw):
    """Pick the alternative with the largest dominated-hypervolume contribution
    to the reference (nadir) point, approximated by the product of slacks."""
    r = normalize(F)
    contrib = np.prod(np.maximum(1.0 - r, 0.0), axis=1)  # box to nadir=1
    return int(np.argmax(contrib))


def dist_to_ideal(F, **kw):
    r = normalize(F)
    return int(np.argmin(np.linalg.norm(r, axis=1)))


def chebyshev_mmr(F, n_weights=1000, rng=None, **kw):
    """Minimax regret under weighted-Chebyshev utilities over a weight set."""
    rng = np.random.default_rng(0) if rng is None else rng
    r = normalize(F)
    n, m = r.shape
    W = rng.dirichlet(np.ones(m), size=n_weights)
    C = np.stack([np.max(W[t] * r, axis=1) for t in range(n_weights)], axis=1)  # NxT
    regret = C - C.min(axis=0, keepdims=True)
    return int(np.argmin(regret.max(axis=1)))


def weighted_sum(F, w=None, **kw):
    """Simple weighted sum (linear scalarisation)."""
    r = normalize(F)
    m = r.shape[1]
    w = np.ones(m) / m if w is None else np.asarray(w)
    return int(np.argmin(np.sum(w * r, axis=1)))


def exact_leximax(F, **kw):
    """Exact leximax on the raw objectives (sorted descending)."""
    # For minimisation problems, leximax means we want to minimise the worst objective,
    # then the second worst, etc.
    # So we sort each candidate's objectives descending, then find the lexicographic minimum.
    S = np.sort(F, axis=1)[:, ::-1]
    # np.lexsort sorts by the last column first, so we pass columns in reverse order
    order = np.lexsort(S[:, ::-1].T)
    return int(order[0])


# --------------------------------------------------------------------------- #
# robust-MCDA baselines
# --------------------------------------------------------------------------- #
def smaa(F, n_weights=1000, rng=None, return_detail=False, **kw):
    """SMAA-2 style: Monte-Carlo over the uniform weight simplex with additive
    (linear) value; recommend the alternative with the highest first-rank
    acceptability index (ties broken by expected value)."""
    rng = np.random.default_rng(0) if rng is None else rng
    r = normalize(F)
    n, m = r.shape
    W = rng.dirichlet(np.ones(m), size=n_weights)
    V = -(r @ W.T)  # value, higher better
    first = np.argmax(V, axis=0)
    a1 = np.bincount(first, minlength=n) / n_weights  # rank-1 acceptability
    exp_val = V.mean(axis=1)
    order = np.lexsort((exp_val, a1))  # primary a1, tie exp_val
    winner = int(order[-1])
    if return_detail:
        return winner, a1, exp_val
    return winner


def minimax_regret(F, n_weights=1000, rng=None, **kw):
    """Savage minimax regret over a linear weight set: choose the alternative
    minimising its maximum (over weights) regret vs. the best alternative."""
    rng = np.random.default_rng(0) if rng is None else rng
    r = normalize(F)
    n, m = r.shape
    W = rng.dirichlet(np.ones(m), size=n_weights)
    C = r @ W.T  # cost (lower better)
    best = C.min(axis=0, keepdims=True)
    regret = C - best  # >=0
    max_regret = regret.max(axis=1)
    return int(np.argmin(max_regret))


# --------------------------------------------------------------------------- #
# registry
# --------------------------------------------------------------------------- #
METHODS = {
    "TOPSIS": topsis,
    "CP": compromise_programming,
    "VIKOR": vikor,
    "Knee": knee_point,
    "HV": hypervolume_pick,
    "DistIdeal": dist_to_ideal,
    "WS": weighted_sum,
    "Leximax": exact_leximax,
    "RW": random_weights,
    "ASF": asf,
    "SMAA": smaa,
    "MMR": minimax_regret,
    "ChebMMR": chebyshev_mmr,
    "LexPR": lexpr,
    "LexPR-noclust": lambda F, **kw: lexpr_variant(F, variant="no_clusters", **kw),
    "LexPR-interval": lexpr_interval,
    "ReLexTail": lambda F, **kw: relex_tail(
        F,
        resolutions=kw.pop(
            "resolutions",
            {
                "maximum": "0.01",
                "tail_025": "0.01",
                "tail_050": "0.01",
                "tail_100": "0.01",
            },
        ),
        **kw,
    ),
}
CLASSICAL = [
    "TOPSIS",
    "CP",
    "VIKOR",
    "Knee",
    "HV",
    "DistIdeal",
    "WS",
    "Leximax",
    "RW",
    "ASF",
]
ROBUST = ["SMAA", "MMR", "ChebMMR"]
RANDOMIZED = {"RW", "SMAA", "MMR", "ChebMMR"}  # need an rng


def select(name, F, rng=None, **kwargs):
    fn = METHODS[name]
    if name in RANDOMIZED:
        return fn(F, rng=rng, **kwargs)
    return fn(F, **kwargs)
