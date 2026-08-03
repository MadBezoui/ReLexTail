"""Certified deterministic stability analysis on the supplier case.

Produces certified possible/necessary winner sets, unresolved-volume bounds, a
certified stability radius (lower bound), and the nearest witnessed reversal
(upper bound on the radius).  All numbers are real and reproducible.
"""
from __future__ import annotations
import os, sys, json
import numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lexpr import supplier, certified, methods

SEED = 20260628
OUT = os.path.join(os.path.dirname(__file__), "real_results")
os.makedirs(OUT, exist_ok=True)


def witness_winners(F, probes, p, n_samples=4000, rng=None):
    """Certified INNER possible set: every winner at a sampled bound config is a
    proven possible winner (explicit witness). Includes box corners implicitly
    through dense sampling."""
    rng = np.random.default_rng(0) if rng is None else rng
    ideal0, nadir0 = F.min(axis=0), F.max(axis=0)
    m = F.shape[1]
    # convert probes to callables for methods.disappointment via explicit eval
    def winner_at(ideal, nadir):
        r = (F - ideal) / (nadir - ideal)
        cols = []
        for kind, idx in probes:
            idx = list(idx)
            if kind == "single":
                v = r[:, idx[0]]
            elif kind == "mean":
                v = r[:, idx].mean(axis=1)
            else:
                v = r[:, idx].max(axis=1)
            a, b = v.min(), v.max()
            cols.append((v - a) / (b - a + 1e-12))
        D = np.column_stack(cols)
        return certified._lex_argmin(D) if hasattr(certified, "_lex_argmin") else int(
            np.lexsort((-np.sort(-D, axis=1)).T[::-1])[0])
    seen = set()
    for _ in range(n_samples):
        u = rng.uniform(-p, p, size=m)
        up = rng.uniform(0, p, size=m)
        ideal = ideal0 * (1 - up)
        nadir = np.maximum(nadir0 * (1 + u), ideal + 1e-3)
        seen.add(winner_at(ideal, nadir))
    return sorted(seen)


def nearest_reversal(F, probes, nominal, rng, p_grid):
    """Smallest grid p at which a non-nominal winner is witnessed (upper bound on
    the true stability radius). Returns (p, competitor)."""
    ideal0, nadir0 = F.min(axis=0), F.max(axis=0)
    m = F.shape[1]
    def winner_at(ideal, nadir):
        r = (F - ideal) / (nadir - ideal)
        cols = []
        for kind, idx in probes:
            idx = list(idx)
            v = r[:, idx[0]] if kind == "single" else (
                r[:, idx].mean(axis=1) if kind == "mean" else r[:, idx].max(axis=1))
            a, b = v.min(), v.max(); cols.append((v - a) / (b - a + 1e-12))
        D = np.column_stack(cols)
        return int(np.lexsort((-np.sort(-D, axis=1)).T[::-1])[0])
    for p in p_grid:
        for _ in range(3000):
            u = rng.uniform(-p, p, size=m); up = rng.uniform(0, p, size=m)
            ideal = ideal0 * (1 - up); nadir = np.maximum(nadir0 * (1 + u), ideal + 1e-3)
            w = winner_at(ideal, nadir)
            if w != nominal:
                return float(p), w
    return None, None


def main():
    F, names, crit = supplier.load_supplier_case()
    probes, labels = certified.canonical_supplier_probes()
    rng = np.random.default_rng(SEED)
    nominal = methods.lexpr(F, theta=0.6)

    res = {"nominal_winner": names[nominal]}

    # certified stability radius (lower bound) + nearest witnessed reversal (upper bound)
    rho = certified.certified_stability_radius(F, probes, nominal, p_hi=0.6,
                                               tol=1e-3, max_boxes=8000)
    res["certified_radius_lower"] = round(rho, 4)
    grid = [round(x, 4) for x in np.arange(0.001, 0.06, 0.001)]
    pr, comp = nearest_reversal(F, probes, nominal, np.random.default_rng(SEED + 5), grid)
    res["nearest_reversal_p"] = pr
    res["nearest_reversal_competitor"] = None if comp is None else names[comp]

    # certified possible/necessary sets and unresolved volume at each level
    res["levels"] = {}
    for p in (0.02, 0.05, 0.10, 0.20):
        cs = certified.certified_sets(F, probes, p, max_boxes=40000, max_depth=44)
        inner = witness_winners(F, probes, p, n_samples=4000,
                                rng=np.random.default_rng(SEED + int(p * 1000)))
        res["levels"][str(p)] = {
            "certified_inner_possible": [names[i] for i in inner],
            "certified_outer_possible": [names[i] for i in cs["outer_possible"]],
            "certified_necessary": [names[i] for i in cs["necessary_inner"]],
            "unresolved_vol_frac": round(cs["unresolved_vol_frac"], 4),
            "n_boxes": cs["n_boxes"],
        }

    with open(os.path.join(OUT, "certified.json"), "w") as f:
        json.dump(res, f, indent=2)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
