from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


REQUIRED_BENCHMARK_COLUMNS = {
    "run_id",
    "config_sha256",
    "seed",
    "N",
    "m",
    "geometry",
    "replication",
    "dirichlet_alpha",
    "method",
    "utility_scope",
    "mean_loss",
    "tail_loss",
    "worst_family",
    "worst_family_loss",
    "selected_index",
}
CELL_COLUMNS = ["N", "m", "geometry", "replication"]
ROW_KEY_COLUMNS = CELL_COLUMNS + ["method"]


def expected_benchmark_cells(cfg: dict) -> int:
    return (
        len(cfg["candidate_sizes"])
        * len(cfg["criteria"])
        * len(cfg["geometries"])
        * int(cfg["replications"])
    )


def _require_exact_levels(frame: pd.DataFrame, column: str, expected) -> None:
    actual = set(frame[column].unique())
    expected = set(expected)
    if actual != expected:
        raise ValueError(
            f"unexpected {column} levels: expected {sorted(expected)}, "
            f"found {sorted(actual)}"
        )


def validate_benchmark_frame(frame, cfg: dict, run_id: str) -> None:
    missing = REQUIRED_BENCHMARK_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"missing benchmark columns: {sorted(missing)}")
    if frame.empty:
        raise ValueError("benchmark frame is empty")
    if set(frame["run_id"].unique()) != {run_id}:
        raise ValueError("benchmark run_id does not match the expected run")
    if frame["config_sha256"].nunique() != 1:
        raise ValueError("benchmark contains multiple config_sha256 values")

    _require_exact_levels(frame, "N", cfg["candidate_sizes"])
    _require_exact_levels(frame, "m", cfg["criteria"])
    _require_exact_levels(frame, "geometry", cfg["geometries"])
    _require_exact_levels(frame, "replication", range(int(cfg["replications"])))
    actual_methods = set(frame["method"].unique())
    expected_methods = set(cfg["methods"])
    if actual_methods != expected_methods:
        raise ValueError(
            "benchmark method set mismatch: "
            f"expected {sorted(expected_methods)}, found {sorted(actual_methods)}"
        )

    duplicates = frame.duplicated(ROW_KEY_COLUMNS, keep=False)
    if duplicates.any():
        raise ValueError("duplicate benchmark cell/method rows found")

    method_sets = frame.groupby(CELL_COLUMNS, sort=False)["method"].agg(set)
    if any(methods != expected_methods for methods in method_sets):
        raise ValueError("at least one benchmark cell has an incomplete method set")

    expected_cells = expected_benchmark_cells(cfg)
    if len(method_sets) != expected_cells:
        raise ValueError(
            f"expected {expected_cells} benchmark cells, found {len(method_sets)}"
        )
    expected_rows = expected_cells * len(expected_methods)
    if len(frame) != expected_rows:
        raise ValueError(f"expected {expected_rows} benchmark rows, found {len(frame)}")

    scopes = cfg.get("family_scopes", {})
    allowed_scopes = set(scopes.values())
    if not allowed_scopes or not set(frame["utility_scope"]).issubset(allowed_scopes):
        raise ValueError("benchmark contains an unknown utility_scope")
    expected_scope = frame["worst_family"].map(scopes)
    if expected_scope.isna().any() or not expected_scope.equals(frame["utility_scope"]):
        raise ValueError("utility_scope does not match worst_family")

    metrics = frame[["mean_loss", "tail_loss", "worst_family_loss"]].to_numpy(
        dtype=float
    )
    if not np.isfinite(metrics).all():
        raise ValueError("benchmark loss metrics must be finite")
    if ((metrics < -1e-12) | (metrics > 1.0 + 1e-12)).any():
        raise ValueError("benchmark loss metrics must lie in [0, 1]")

    selected = frame["selected_index"].to_numpy(dtype=int)
    sizes = frame["N"].to_numpy(dtype=int)
    if ((selected < 0) | (selected >= sizes)).any():
        raise ValueError("selected_index lies outside its candidate set")


def load_validated_chunks(
    paths: list[str | Path], cfg: dict, run_id: str
) -> pd.DataFrame:
    if not paths:
        raise ValueError("no benchmark chunks were provided")
    frames = [pd.read_parquet(Path(path)) for path in sorted(map(Path, paths))]
    frame = pd.concat(frames, ignore_index=True)
    if frame.duplicated(ROW_KEY_COLUMNS, keep=False).any():
        raise ValueError("duplicate benchmark cell/method rows found across chunks")
    validate_benchmark_frame(frame, cfg, run_id)
    return frame.sort_values(ROW_KEY_COLUMNS, kind="stable").reset_index(drop=True)
