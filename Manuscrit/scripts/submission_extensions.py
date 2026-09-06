"""Sensitivity, ablation, and public-benchmark extensions for the submission.

All calculations reuse the frozen candidate matrices and perturbation directions
from ``submission_study.py``.  The external Energy Efficiency data are checked
against the publisher-provided file hash before use.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import hashlib
import json
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "Experimental/code"))

from submission_analysis import (  # noqa: E402
    lexicographic_argmin,
    pareto_mask,
    relex_choice,
)
from submission_study import DELTAS, representation  # noqa: E402


DATA = ROOT / "Manuscrit/submission/data"
EXTERNAL = DATA / "external/uci_energy_efficiency.csv"
EXPECTED_SHA256 = "db44dbe453acd464b5cf65be2fb01a28aa9c5b2630300e65fbe28cde35f5d96f"
GRID_DELTAS = (0.01, 0.02, 0.05)
ORIGIN_FRACTIONS = (0.0, 0.25, 0.5, 0.75)
PREFIXES = (1, 2, 4)


def profile_blocks(D: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return descending disappointments and maximum/tail profile scores."""

    sorted_d = np.sort(D, axis=1)[:, ::-1]
    k_count = sorted_d.shape[1]
    tails = []
    for alpha in (0.25, 0.5, 1.0):
        mass = alpha * k_count
        whole = int(mass)
        fraction = mass - whole
        numerator = sorted_d[:, :whole].sum(axis=1)
        if fraction:
            numerator += fraction * sorted_d[:, whole]
        tails.append(numerator / mass)
    return sorted_d, np.column_stack((sorted_d[:, 0], *tails))


def aggregate_representation(
    F: np.ndarray, ideal: np.ndarray, nadir: np.ndarray
) -> np.ndarray:
    """Representation retaining only the mean and maximum aggregate probes."""

    r = (F - ideal) / (nadir - ideal)
    q = np.column_stack((r.mean(axis=1), r.max(axis=1)))
    ranges = np.ptp(q, axis=0)
    keep = ranges > 1e-9
    return (q[:, keep] - q[:, keep].min(axis=0)) / ranges[keep]


def choice_for(
    D: np.ndarray,
    delta: float,
    *,
    origin_fraction: float = 0.0,
    coordinates: int = 4,
) -> tuple[int, tuple[int, ...]]:
    sorted_d, scores = profile_blocks(D)
    return relex_choice(
        scores,
        sorted_d,
        delta,
        origin_fraction=origin_fraction,
        coordinates=coordinates,
    )


def summarise_observations(values: list[tuple[bool, bool, int, bool]]) -> dict:
    a = np.asarray(values, dtype=float)
    return {
        "flip": float(a[:, 0].mean()),
        "category_change": float(a[:, 1].mean()),
        "category_size": float(a[:, 2].mean()),
        "retention": float(a[:, 3].mean()),
    }


def grid_and_ablation(archive: np.lib.npyio.NpzFile) -> tuple[pd.DataFrame, pd.DataFrame]:
    grid_rows = []
    ablation_rows = []
    seed_rows = []
    instance_ids = sorted(k for k in archive.files if not k.endswith("-directions"))
    for number, iid in enumerate(instance_ids, start=1):
        F = archive[iid]
        family, m_text, _ = iid.split("-")
        m = int(m_text)
        lo = F.min(axis=0)
        hi = F.max(axis=0)
        span = hi - lo
        _, nominal_D, nominal_keep = representation(F, lo, hi)
        nominal_aggregate = aggregate_representation(F, lo, hi)
        nominal_grid = {
            (delta, origin): choice_for(
                nominal_D, delta, origin_fraction=origin
            )
            for delta in GRID_DELTAS
            for origin in ORIGIN_FRACTIONS
        }
        nominal_ablation = {
            f"prefix-{prefix}": choice_for(
                nominal_D, 0.02, coordinates=prefix
            )
            for prefix in PREFIXES
        }
        nominal_ablation["aggregate-only"] = choice_for(
            nominal_aggregate, 0.02
        )
        grid_obs = {key: [] for key in nominal_grid}
        ablation_obs = {key: [] for key in nominal_ablation}
        for direction in archive[iid + "-directions"]:
            ideal = lo + 0.05 * span * direction[0]
            nadir = hi + 0.05 * span * direction[1]
            _, D, keep = representation(F, ideal, nadir)
            if not np.array_equal(keep, nominal_keep):
                raise AssertionError("retained full probe family changed")
            aggregate_D = aggregate_representation(F, ideal, nadir)
            for key, (winner0, group0) in nominal_grid.items():
                delta, origin = key
                winner, group = choice_for(D, delta, origin_fraction=origin)
                grid_obs[key].append(
                    (winner != winner0, group != group0, len(group), winner0 in group)
                )
            for key, (winner0, group0) in nominal_ablation.items():
                if key == "aggregate-only":
                    winner, group = choice_for(aggregate_D, 0.02)
                else:
                    prefix = int(key.split("-")[1])
                    winner, group = choice_for(D, 0.02, coordinates=prefix)
                ablation_obs[key].append(
                    (winner != winner0, group != group0, len(group), winner0 in group)
                )
        for (delta, origin), observations in grid_obs.items():
            grid_rows.append(
                {
                    "instance": iid,
                    "family": family,
                    "m": m,
                    "delta": delta,
                    "origin_fraction": origin,
                    **summarise_observations(observations),
                }
            )
        for variant, observations in ablation_obs.items():
            ablation_rows.append(
                {
                    "instance": iid,
                    "family": family,
                    "m": m,
                    "variant": variant,
                    **summarise_observations(observations),
                }
            )
        seed_rows.append(number)
        if number % 10 == 0:
            print(f"extensions: {number}/{len(instance_ids)} instances", flush=True)
    if len(seed_rows) != 90:
        raise AssertionError("expected 90 frozen instances")
    return pd.DataFrame(grid_rows), pd.DataFrame(ablation_rows)


def decisive_coordinates(archive: np.lib.npyio.NpzFile) -> pd.DataFrame:
    records = []
    for iid in sorted(k for k in archive.files if not k.endswith("-directions")):
        F = archive[iid]
        lo = F.min(axis=0)
        hi = F.max(axis=0)
        _, D, _ = representation(F, lo, hi)
        sorted_d, scores = profile_blocks(D)
        from submission_analysis import category_index

        cats = category_index(scores, 0.02)
        keys = np.column_stack((cats, scores[:, 1:], sorted_d))
        order = np.lexsort(tuple(keys[:, j] for j in range(keys.shape[1] - 1, -1, -1)))
        winner, rival = map(int, order[:2])
        labels = ["Cmax", "C25", "C50", "Cmean", "T25", "T50", "Tmean"]
        labels.extend(f"D{j + 1}" for j in range(sorted_d.shape[1]))
        differing = np.flatnonzero(keys[winner] != keys[rival])
        if differing.size == 0:
            decisive = "identifier"
            block = "identifier"
        else:
            decisive = labels[int(differing[0])]
            block = (
                "category"
                if decisive.startswith("C")
                else "tail-refinement"
                if decisive.startswith("T")
                else "profile-refinement"
            )
        records.append(
            {
                "instance": iid,
                "family": iid.split("-")[0],
                "m": int(iid.split("-")[1]),
                "winner": winner,
                "nearest_rival": rival,
                "decisive_coordinate": decisive,
                "decisive_block": block,
            }
        )
    return pd.DataFrame(records)


def evaluation_losses(F: np.ndarray, seed: int = 20260906) -> tuple[np.ndarray, np.ndarray]:
    r = (F - F.min(axis=0)) / np.ptp(F, axis=0)
    weights = np.random.default_rng(seed).dirichlet(np.ones(F.shape[1]), size=10_000)
    losses = r @ weights.T
    span = np.ptp(losses, axis=0)
    regrets = np.divide(
        losses - losses.min(axis=0),
        span,
        out=np.zeros_like(losses),
        where=span > 0,
    )
    return regrets.mean(axis=1), np.partition(regrets, 7500, axis=1)[:, 7500:].mean(axis=1)


def uci_benchmark() -> dict:
    digest = hashlib.sha256(EXTERNAL.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        raise AssertionError(f"unexpected UCI file hash: {digest}")
    raw = pd.read_csv(EXTERNAL).reset_index(names="source_row")
    objectives = raw[["X2", "Y1", "Y2"]].drop_duplicates()
    unique = raw.loc[objectives.index, ["source_row", "X2", "Y1", "Y2"]].copy()
    keep = pareto_mask(unique[["X2", "Y1", "Y2"]].to_numpy(float))
    front = unique.loc[keep].reset_index(drop=True)
    F = front[["X2", "Y1", "Y2"]].to_numpy(float)
    lo = F.min(axis=0)
    hi = F.max(axis=0)
    span = hi - lo
    r, D, _ = representation(F, lo, hi)
    sorted_d, _ = profile_blocks(D)
    mean_loss, tail_loss = evaluation_losses(F)
    nominal = {
        "LexPR": (lexicographic_argmin(sorted_d), None),
        "Mean-D": (int(np.argmin(D.mean(axis=1))), None),
        "Weighted-sum": (int(np.argmin(r.mean(axis=1))), None),
    }
    for delta in DELTAS:
        nominal[f"ReLexTail {delta:g}"] = choice_for(D, delta)
    rng = np.random.default_rng(20260906)
    rows = []
    for p in (0.01, 0.05, 0.1, 0.2):
        observations = {name: [] for name in nominal}
        directions = rng.uniform(-1.0, 1.0, size=(500, 2, F.shape[1]))
        for direction in directions:
            r1, D1, _ = representation(
                F,
                lo + p * span * direction[0],
                hi + p * span * direction[1],
            )
            sorted_d1, _ = profile_blocks(D1)
            changed = {
                "LexPR": (lexicographic_argmin(sorted_d1), None),
                "Mean-D": (int(np.argmin(D1.mean(axis=1))), None),
                "Weighted-sum": (int(np.argmin(r1.mean(axis=1))), None),
            }
            for delta in DELTAS:
                changed[f"ReLexTail {delta:g}"] = choice_for(D1, delta)
            for name, (winner, group) in changed.items():
                winner0, group0 = nominal[name]
                observations[name].append(
                    (
                        winner != winner0,
                        mean_loss[winner],
                        tail_loss[winner],
                        group != group0 if group is not None else np.nan,
                    )
                )
        for name, values in observations.items():
            a = np.asarray(values, dtype=float)
            winner0, group0 = nominal[name]
            rows.append(
                {
                    "p": p,
                    "method": name,
                    "nominal_source_row": int(front.loc[winner0, "source_row"]),
                    "nominal_category_size": len(group0) if group0 else 1,
                    "flip": float(a[:, 0].mean()),
                    "mean_regret": float(a[:, 1].mean()),
                    "tail_regret": float(a[:, 2].mean()),
                    "category_change": None if group0 is None else float(a[:, 3].mean()),
                }
            )
    return {
        "source": "UCI Energy Efficiency, DOI 10.24432/C51307",
        "license": "CC BY 4.0",
        "sha256": digest,
        "raw_rows": int(len(raw)),
        "unique_objective_profiles": int(len(unique)),
        "nondominated_profiles": int(len(front)),
        "objectives_all_minimise": ["surface area X2", "heating load Y1", "cooling load Y2"],
        "front": front.to_dict(orient="records"),
        "results": rows,
    }


def main() -> None:
    archive = np.load(DATA / "candidates.npz")
    grid, ablation = grid_and_ablation(archive)
    decisive = decisive_coordinates(archive)
    grid.to_csv(DATA / "grid_sensitivity.csv", index=False)
    ablation.to_csv(DATA / "ablation.csv", index=False)
    decisive.to_csv(DATA / "decisive_coordinates.csv", index=False)
    uci = uci_benchmark()
    (DATA / "uci_benchmark.json").write_text(json.dumps(uci, indent=2))
    print("grid means at delta=0.02", flush=True)
    print(
        grid[grid.delta == 0.02]
        .groupby("origin_fraction")[["flip", "category_change", "category_size", "retention"]]
        .mean()
        .to_string(),
        flush=True,
    )
    print("ablation means", flush=True)
    print(
        ablation.groupby("variant")[["flip", "category_change", "category_size", "retention"]]
        .mean()
        .to_string(),
        flush=True,
    )
    print("decisive blocks", Counter(decisive.decisive_block), flush=True)
    print("UCI nondominated profiles", uci["nondominated_profiles"], flush=True)


if __name__ == "__main__":
    main()
