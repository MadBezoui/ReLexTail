"""Candidate-set generators with controlled Pareto-front geometries.

A *candidate set* A is an (N x m) matrix of objective vectors (minimisation).
We sample finite non-dominated approximations of canonical Pareto-front
geometries (linear / concave / convex / disconnected), mirroring the output of
an a-posteriori multi-objective optimiser.  This is the realistic setting for a
*selection* method: every candidate is (near-)efficient and the task is to pick
a single robust recommendation.

Geometries follow the families used by the DTLZ test suite:
    linear        -> DTLZ1   (front on the simplex  sum f_i = 0.5)
    concave       -> DTLZ2/3/4 (front on the unit sphere  sum f_i^2 = 1)
    convex        -> front  sum sqrt(f_i) = 1
    disconnected  -> DTLZ7-like (several concave patches)
"""
from __future__ import annotations
import numpy as np

GEOMETRIES = (
    "linear",
    "concave",
    "convex",
    "disconnected",
    "asymmetric",
    "manyknee",
    "degenerate",
    "irregular",
    "cars",
    "water",
    "knapsack",
    "wfg2",
    "jobshop",
    "energy",
    "concrete",
)


def _dirichlet_simplex(n: int, m: int, rng: np.random.Generator) -> np.ndarray:
    """n points on the (m-1)-simplex, sum_i s_i = 1, s_i >= 0."""
    return rng.dirichlet(np.ones(m), size=n)


def sample_front(geometry: str, n: int, m: int, rng: np.random.Generator) -> np.ndarray:
    """Return an (n x m) non-dominated candidate set for the given geometry."""
    s = _dirichlet_simplex(n, m, rng)
    if geometry == "linear":
        F = 0.5 * s  # sum f_i = 0.5
    elif geometry == "concave":
        d = rng.random((n, m)) ** 0.5  # spread away from axes
        F = d / np.linalg.norm(d, axis=1, keepdims=True)  # sum f_i^2 = 1
    elif geometry == "convex":
        F = s**2  # sum sqrt(f_i) = 1
    elif geometry == "disconnected":
        # union of a few concave patches with offsets along objective 1
        d = rng.random((n, m)) ** 0.5
        F = d / np.linalg.norm(d, axis=1, keepdims=True)
        patch = rng.integers(0, 4, size=n)
        F[:, 0] = F[:, 0] + 0.6 * patch  # creates gaps -> disconnected
    elif geometry == "asymmetric":
        # concave sphere with heterogeneous criterion scales
        d = rng.random((n, m)) ** 0.5
        F = d / np.linalg.norm(d, axis=1, keepdims=True)
        scales = np.linspace(1.0, 5.0, m)
        F = F * scales
    elif geometry == "manyknee":
        # concave base warped to create multiple knees
        d = rng.random((n, m)) ** 0.5
        F = d / np.linalg.norm(d, axis=1, keepdims=True)
        F = F + 0.15 * np.sin(6.0 * F)
        F = np.clip(F, 0, None)
    elif geometry == "degenerate":
        # lower-dimensional front: last criterion tied to the first
        F = s**2
        F[:, -1] = F[:, 0]
    elif geometry == "irregular":
        # concave front with multiplicative noise (noisy/irregular surface)
        d = rng.random((n, m)) ** 0.5
        F = d / np.linalg.norm(d, axis=1, keepdims=True)
        F = F * (1.0 + 0.1 * rng.standard_normal((n, m)))
        F = np.clip(F, 1e-3, None)
    elif geometry == "cars":
        # Classic electric vehicle selection MCDA dataset (minimisation)
        # 10 cars, 5 criteria (cost, -range, -top_speed, charge_time, -battery)
        F = np.array(
            [
                [30000, -250, -150, 8.0, -40],
                [35000, -300, -160, 7.5, -50],
                [25000, -200, -140, 9.0, -35],
                [40000, -350, -180, 6.0, -60],
                [45000, -400, -200, 5.5, -70],
                [28000, -220, -145, 8.5, -38],
                [32000, -280, -155, 7.8, -45],
                [38000, -320, -170, 6.5, -55],
                [50000, -450, -220, 5.0, -80],
                [22000, -180, -130, 10.0, -30],
            ],
            dtype=float,
        )
    elif geometry == "water":
        # Water management MCDA dataset (minimisation)
        # 6 alts, 5 criteria (cost, env_impact, -reliability, -social_acc, time)
        F = np.array(
            [
                [100, 5, -80, -70, 24],
                [150, 3, -90, -80, 36],
                [80, 7, -60, -50, 12],
                [200, 2, -95, -85, 48],
                [120, 6, -75, -65, 18],
                [180, 4, -85, -75, 30],
            ],
            dtype=float,
        )

    elif geometry == "knapsack":
        # Knapsack approximation (simulated combinatorial front)
        d = rng.random((n, m)) ** 0.5
        F = d / np.linalg.norm(d, axis=1, keepdims=True)
        # Shift away from origin and add discrete structure
        F = F + 0.1
        F = np.round(F * 100) / 100
        F = np.clip(F, 0.01, None)

    elif geometry == "wfg2":
        # WFG2-like disconnected/convex front approximation
        d = rng.random((n, m)) ** 0.5
        F = d / np.linalg.norm(d, axis=1, keepdims=True)
        patch = rng.integers(0, 5, size=n)
        F[:, 0] = F[:, 0] + 0.5 * patch
        F = F**2

    elif geometry == "jobshop":
        # Jobshop epsilon-constraint approximation (combinatorial, coarse)
        F = rng.dirichlet(np.ones(m), size=n)
        F = np.round(F * 50) / 50
        F = np.clip(F, 0.02, None)

    elif geometry == "energy":
        # UCI Energy Efficiency surrogate
        # Criteria: Heating load, Cooling load, Surface Area, Wall Area, Roof Area
        base = rng.dirichlet(np.ones(m), size=n)
        F = base * np.array([50, 50, 800, 400, 200][:m] + [100] * max(0, m - 5))
        F = F + rng.normal(0, 0.05, size=(n, m)) * F
        F = np.clip(F, 1, None)

    elif geometry == "concrete":
        # UCI Concrete Strength surrogate
        # Criteria: -Strength, Cement, Water, Coarse Aggr, Fine Aggr
        base = rng.dirichlet(np.ones(m), size=n)
        F = base * np.array([-80, 500, 250, 1000, 900][:m] + [100] * max(0, m - 5))
        F = F + rng.normal(0, 0.05, size=(n, m)) * F
        F = np.abs(F)
        F = np.clip(F, 1, None)

    else:
        raise ValueError(f"unknown geometry {geometry!r}")
    return non_dominated(F)


def non_dominated(F: np.ndarray) -> np.ndarray:
    """Return the non-dominated subset of F (minimisation). Vectorised:
    point i is dominated iff some j satisfies F[j] <= F[i] (all) and F[j] < F[i]
    (some). For large N we tile to bound peak memory."""
    n = F.shape[0]
    keep = np.ones(n, dtype=bool)
    block = 256
    for s in range(0, n, block):
        e = min(s + block, n)
        le = (F[None, :, :] <= F[s:e, None, :]).all(axis=2)  # (b x n) F[j]<=F[i]
        lt = (F[None, :, :] < F[s:e, None, :]).any(axis=2)  # (b x n) F[j]<F[i]
        dom = le & lt  # j dominates i
        for k in range(e - s):
            dom[k, s + k] = False
        keep[s:e] = ~dom.any(axis=1)
    return F[keep]


def make_redundant_set(
    geometry: str, n: int, group_sizes, rng: np.random.Generator, noise: float = 0.05
):
    """Realistic case motivating correlation clustering: the decision-maker has
    `c = len(group_sizes)` TRUE underlying criteria, but each is measured by
    several redundant (positively correlated) objectives.

    Returns (F, groups) where F is (n x m), m = sum(group_sizes), and groups is a
    length-m array mapping each objective to its underlying criterion index.
    Within a group, objectives are noisy monotone copies of the same criterion,
    so they are strongly positively correlated; across groups they trade off."""
    c = len(group_sizes)
    base = sample_front(geometry, max(2 * n, 64), c, rng)
    base = non_dominated(base)
    while base.shape[0] < n:
        extra = non_dominated(sample_front(geometry, 2 * n, c, rng))
        base = np.vstack([base, extra])
    base = base[:n]
    cols, groups = [], []
    for g, sz in enumerate(group_sizes):
        for _ in range(sz):
            scale = rng.uniform(0.8, 1.2)
            shift = rng.uniform(-0.02, 0.02)
            col = scale * base[:, g] + shift + noise * rng.standard_normal(n)
            cols.append(col)
            groups.append(g)
    F = np.column_stack(cols)
    F = F - F.min(axis=0) + 1e-3  # keep positive
    return F, np.array(groups), base


def make_candidate_set(
    geometry: str, n: int, m: int, rng: np.random.Generator, n_dominated: int = 0
) -> np.ndarray:
    """Build a candidate set of >= n non-dominated points (resampling until met),
    optionally appended with `n_dominated` strictly dominated interior points
    (used to test dominated-exclusion)."""
    # Single oversample + single non-dominated pass (bounded cost ~O((1.5n)^2 m)).
    # sample_front already returns points on the front, so this yields ~n
    # non-dominated points for typical geometries; for low-fraction geometries
    # (e.g. degenerate at small m) it returns somewhat fewer, which is an
    # acceptable candidate set and avoids unbounded resampling.
    raw = sample_front(geometry, int(1.5 * n) + 16, m, rng)
    F = non_dominated(raw)[:n]
    if F.shape[0] < max(8, n // 5):  # safety: ensure enough points
        F = raw[: max(8, n // 5)]
    if n_dominated > 0:
        # interior points dominated by a random anchor in F
        anchors = F[rng.integers(0, F.shape[0], size=n_dominated)]
        dom = anchors + rng.uniform(0.05, 0.25, size=anchors.shape)
        F = np.vstack([F, dom])
    return F


def sample_continuous_dtlz2(
    n_samples: int, m: int, rng: np.random.Generator, k: int = 10
) -> np.ndarray:
    """Sample candidates from the continuous non-linear DTLZ2 benchmark.
    Returns (n_samples, m) objective matrix (minimisation)."""
    n_vars = m + k - 1
    X = rng.uniform(0, 1, size=(n_samples, n_vars))
    # Distance function g(X_M)
    X_M = X[:, m - 1 :]
    g = np.sum((X_M - 0.5) ** 2, axis=1)

    F = np.zeros((n_samples, m))
    for i in range(m):
        # The base is (1 + g)
        fi = 1.0 + g
        # Multiply by cos(x_j * pi / 2) for j < m - 1 - i
        for j in range(m - 1 - i):
            fi *= np.cos(X[:, j] * np.pi / 2.0)
        # Multiply by sin(x_{m - 1 - i} * pi / 2) if i > 0
        if i > 0:
            fi *= np.sin(X[:, m - 1 - i] * np.pi / 2.0)
        F[:, i] = fi
    return F
