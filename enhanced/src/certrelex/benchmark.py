"""Prespecified benchmark families and a frozen split manifest.

Six *development* families and two *stress* families are generated from a fixed
master seed.  The split is a deterministic function of the family, the
criterion count and the replicate index, so it is fixed before any run and can
be recomputed by anyone from this file alone; it is also written out as a
manifest with checksums by ``analysis/build_benchmark.py``.

Development families (in-distribution)
    ``simplex``       linear front, sum f_i constant
    ``spherical``     concave front on a sphere
    ``convex``        convex front, sum sqrt(f_i) constant
    ``disconnected``  several concave patches separated by gaps
    ``correlated``    redundant criteria: a low-rank core plus small noise
    ``asymmetric``    concave front with heterogeneous criterion scales

Stress families (locked, out of distribution)
    ``narrow``        near-tied candidates: margins deliberately close to the
                      resolution cells, so category boundaries are active
    ``heavytail``     correlated Student-t measurement noise on a concave front

Every candidate set is non-dominated by construction or filtered to its
non-dominated subset, which is the realistic input for a *selection* method.
All criteria are minimised.
"""
from __future__ import annotations

import hashlib

import numpy as np

MASTER_SEED = 20260906
DEV_FAMILIES = ("simplex", "spherical", "convex", "disconnected", "correlated", "asymmetric")
STRESS_FAMILIES = ("narrow", "heavytail")
FAMILIES = DEV_FAMILIES + STRESS_FAMILIES
CRITERIA = (3, 6, 10)
REPLICATES = 8
N_CANDIDATES = 40

#: replicate index -> split, fixed before any run
SPLIT_OF_REPLICATE = {
    0: "development",
    1: "development",
    2: "development",
    3: "calibration",
    4: "test",
    5: "test",
    6: "test",
    7: "test",
}


def instance_id(family: str, m: int, rep: int) -> str:
    return f"{family}-{m}-{rep}"


def split_of(family: str, rep: int) -> str:
    """Stress families are locked out-of-distribution in their entirety."""
    if family in STRESS_FAMILIES:
        return "stress"
    return SPLIT_OF_REPLICATE[rep]


def _seed(family: str, m: int, rep: int) -> int:
    """Deterministic across processes and machines.

    ``hash()`` is deliberately not used: Python randomises string hashing per
    process unless ``PYTHONHASHSEED`` is pinned, which would make the benchmark
    depend on an environment variable instead of on this file.
    """
    key = f"{MASTER_SEED}|{family}|{m}|{rep}".encode()
    return int.from_bytes(hashlib.sha256(key).digest()[:4], "big")


def _nondominated(F: np.ndarray) -> np.ndarray:
    keep = np.ones(F.shape[0], dtype=bool)
    for i in range(F.shape[0]):
        if not keep[i]:
            continue
        le = np.all(F <= F[i], axis=1)
        lt = np.any(F < F[i], axis=1)
        if np.any(le & lt):
            keep[i] = False
    return F[keep]


def _pad_to(F: np.ndarray, n: int, rng) -> np.ndarray:
    """Trim or top up to exactly ``n`` rows without reintroducing dominance."""
    if F.shape[0] >= n:
        idx = rng.choice(F.shape[0], size=n, replace=False)
        return F[np.sort(idx)]
    reps = int(np.ceil(n / max(F.shape[0], 1)))
    G = np.tile(F, (reps, 1))[:n]
    return G + rng.normal(0.0, 1e-6, size=G.shape)


def sample_family(family: str, m: int, rep: int, n: int = N_CANDIDATES) -> np.ndarray:
    """Generate one candidate set, deterministic in ``(family, m, rep)``."""
    rng = np.random.default_rng(_seed(family, m, rep))
    raw = 4 * n
    s = rng.dirichlet(np.ones(m), size=raw)
    if family == "simplex":
        F = 0.5 * s
    elif family == "spherical":
        d = rng.random((raw, m)) ** 0.5
        F = d / np.linalg.norm(d, axis=1, keepdims=True)
    elif family == "convex":
        F = s**2
    elif family == "disconnected":
        d = rng.random((raw, m)) ** 0.5
        F = d / np.linalg.norm(d, axis=1, keepdims=True)
        F[:, 0] = F[:, 0] + 0.6 * rng.integers(0, 4, size=raw)
    elif family == "correlated":
        # a rank-2 core replicated across criteria plus small independent noise:
        # criteria are near collinear, which is where anchor slack bites hardest
        core = rng.random((raw, 2))
        load = rng.random((2, m)) + 0.5
        F = core @ load + 0.03 * rng.random((raw, m))
    elif family == "asymmetric":
        d = rng.random((raw, m)) ** 0.5
        F = d / np.linalg.norm(d, axis=1, keepdims=True)
        F = F * (10.0 ** np.linspace(-1.0, 2.0, m))
    elif family == "narrow":
        d = rng.random((raw, m)) ** 0.5
        F = d / np.linalg.norm(d, axis=1, keepdims=True)
        # compress the spread so that many candidates share resolution cells
        F = F.mean(axis=0, keepdims=True) + 0.02 * (F - F.mean(axis=0, keepdims=True))
    elif family == "heavytail":
        d = rng.random((raw, m)) ** 0.5
        F = d / np.linalg.norm(d, axis=1, keepdims=True)
        t = rng.standard_t(df=3, size=(raw, 1)) * np.ones((1, m))
        F = F + 0.02 * (t + rng.standard_t(df=3, size=(raw, m)))
        F = F - F.min(axis=0, keepdims=True) + 1e-3
    else:
        raise ValueError(f"unknown family {family!r}")
    F = _nondominated(np.asarray(F, dtype=float))
    F = _pad_to(F, n, rng)
    # guard against a collapsed criterion range, which would leave the rule
    # undefined rather than merely uncertain
    span = F.max(axis=0) - F.min(axis=0)
    if np.any(span <= 1e-9):
        F = F + rng.normal(0.0, 1e-4, size=F.shape)
    return F


def iter_instances(splits=None, families=None, criteria=None, replicates=None):
    """Yield ``(instance_id, family, m, rep, split, F)`` in a fixed order."""
    for family in families or FAMILIES:
        for m in criteria or CRITERIA:
            for rep in replicates if replicates is not None else range(REPLICATES):
                split = split_of(family, rep)
                if splits is not None and split not in splits:
                    continue
                yield (
                    instance_id(family, m, rep),
                    family,
                    m,
                    rep,
                    split,
                    sample_family(family, m, rep),
                )
