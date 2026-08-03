#!/usr/bin/env python3
"""One-off design search for an instructive supplier instance.
Selects a fixed matrix satisfying:
  - corr(GHG,Energy) >= 0.96 (clean named redundancy)
  - all other |corr| < 0.65 (no spurious extra clusters at theta=0.6)
  - clusters at theta=0.6 == exactly {GHG,Energy}
  - >= 4 distinct method recommendations (methods genuinely disagree)
  - point-winner flip rate at 20% nadir noise >= 0.30 (real fragility)
The chosen matrix is printed for pasting into lexpr/supplier.py.
"""

import os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from lexpr import methods as M
from lexpr.supplier import pareto_mask

CRIT = ["Cost", "Defects", "LeadTime", "GHG", "Energy", "SocialRisk", "Resilience"]
GHG, EN = 3, 4

# realistic per-criterion ranges (min, max) for 10 suppliers
LO = np.array([40, 0.5, 12, 6, 10, 15, 20], float)
HI = np.array([62, 4.0, 36, 24, 40, 70, 60], float)


def make(rng):
    N, m = 10, 7
    F = rng.uniform(LO, HI, size=(N, m))
    # tie Energy to GHG: energy ~ 1.55*GHG + small noise -> near-collinear
    F[:, EN] = 1.55 * F[:, GHG] + rng.normal(0, 0.7, size=N) + 5.0
    return F


def flip_rate(F, theta=0.6, p=0.20, trials=200, seed=0):
    win0 = M.lexpr(F, theta=theta)
    ideal0, nadir0 = F.min(0), F.max(0)
    rng = np.random.default_rng(seed)
    flips = 0
    for _ in range(trials):
        noise = rng.uniform(-p, p, size=F.shape[1])
        nadir = nadir0 * (1 + noise)
        nadir = np.maximum(nadir, F.max(0) + 1e-6)  # keep valid upper bound near range
        # allow estimate below true max too: use absolute estimate, clip to stay > ideal
        nadir = nadir0 * (1 + noise)
        nadir = np.maximum(nadir, ideal0 + 1e-3)
        flips += M.lexpr(F, theta=theta, ideal=ideal0, nadir=nadir) != win0
    return flips / trials


def evaluate(F):
    C = np.corrcoef(F.T)
    ge = C[GHG, EN]
    off = C.copy()
    np.fill_diagonal(off, 0)
    mask = np.ones_like(off, bool)
    mask[GHG, EN] = mask[EN, GHG] = False
    other_max = np.abs(off[mask]).max()
    cl = [sorted(c) for c in M.correlation_clusters(F, 0.6) if len(c) > 1]
    picks = set()
    for name in ["TOPSIS", "CP", "VIKOR", "Knee", "HV", "ASF", "SMAA", "MMR", "LexPR"]:
        picks.add(M.select(name, F, rng=np.random.default_rng(0)))
    fr = flip_rate(F)
    ok = (
        ge >= 0.96
        and other_max < 0.65
        and cl == [[GHG, EN]]
        and len(picks) >= 4
        and fr >= 0.30
    )
    return ok, dict(
        ge=ge, other_max=other_max, clusters=cl, ndistinct=len(picks), flip=fr
    )


best = None
for s in range(200000):
    rng = np.random.default_rng(s)
    F = make(rng)
    if pareto_mask(F).sum() < 9:  # require almost all efficient
        continue
    ok, info = evaluate(F)
    if ok:
        best = (s, F, info)
        break

if best is None:
    print("no instance found")
    sys.exit(1)
s, F, info = best
print("seed", s, info)
np.set_printoptions(precision=1, suppress=True)
print("F=\n", F)
# emit as python literal
print("\n_RAW = np.array([")
for i in range(F.shape[0]):
    row = ", ".join(f"{v:5.1f}" for v in F[i])
    print(f"    [{row}],   # S{i+1}")
print("], dtype=float)")
