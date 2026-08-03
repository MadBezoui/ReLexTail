import numpy as np

EPS = 1e-9


def normalize(
    F: np.ndarray, ideal: np.ndarray | None = None, nadir: np.ndarray | None = None
) -> np.ndarray:
    if ideal is None:
        ideal = F.min(axis=0)
    if nadir is None:
        nadir = F.max(axis=0)
    return (F - ideal) / np.maximum(nadir - ideal, EPS)


def singleton_disappointments(F: np.ndarray) -> np.ndarray:
    lo = F.min(axis=0)
    hi = F.max(axis=0)
    rng = hi - lo
    keep = rng > EPS
    if not keep.any():
        return np.zeros((F.shape[0], 0))
    return (F[:, keep] - lo[keep]) / rng[keep]


def disappointment_matrix(F, probes, ideal=None, nadir=None):
    r = normalize(F, ideal, nadir)
    cols = []
    for q in probes:
        v = q(r)
        qstar, qminus = v.min(), v.max()
        cols.append((v - qstar) / (qminus - qstar + EPS))
    return np.column_stack(cols)
