import numpy as np
import pandas as pd
import pytest

from lexpr.records import (
    expected_benchmark_cells,
    load_validated_chunks,
    validate_benchmark_frame,
)


def test_expected_full_protocol_count():
    cfg = {
        "candidate_sizes": [100, 300, 1000],
        "criteria": [3, 5, 8, 10, 15, 20],
        "geometries": ["a", "b", "c", "d", "e", "f", "g", "h"],
        "replications": 50,
    }
    assert expected_benchmark_cells(cfg) == 7200


def _config():
    return {
        "candidate_sizes": [10],
        "criteria": [3],
        "geometries": ["linear"],
        "replications": 1,
        "methods": ["A", "B"],
        "family_scopes": {"linear": "in_class"},
    }


def _complete_frame():
    return pd.DataFrame([
        {
            "run_id": "run-a",
            "config_sha256": "cfg-a",
            "seed": 1,
            "N": 10,
            "m": 3,
            "geometry": "linear",
            "replication": 0,
            "dirichlet_alpha": 1.0,
            "method": method,
            "utility_scope": "in_class",
            "mean_loss": 0.1,
            "tail_loss": 0.2,
            "worst_family": "linear",
            "worst_family_loss": 0.15,
            "selected_index": index,
        }
        for index, method in enumerate(["A", "B"])
    ])


def test_validation_accepts_complete_frame():
    validate_benchmark_frame(_complete_frame(), _config(), "run-a")


def test_validation_rejects_missing_method_in_one_cell():
    broken = _complete_frame().iloc[:-1]
    with pytest.raises(ValueError, match="method set"):
        validate_benchmark_frame(broken, _config(), "run-a")


def test_validation_rejects_mixed_run_ids():
    broken = _complete_frame()
    broken.loc[broken.index[-1], "run_id"] = "run-b"
    with pytest.raises(ValueError, match="run_id"):
        validate_benchmark_frame(broken, _config(), "run-a")


def test_validation_rejects_unknown_utility_scope():
    broken = _complete_frame()
    broken.loc[broken.index[0], "utility_scope"] = "unknown"
    with pytest.raises(ValueError, match="utility_scope"):
        validate_benchmark_frame(broken, _config(), "run-a")


def test_validation_rejects_non_finite_loss():
    broken = _complete_frame()
    broken.loc[broken.index[0], "tail_loss"] = np.nan
    with pytest.raises(ValueError, match="finite"):
        validate_benchmark_frame(broken, _config(), "run-a")


def test_chunk_loading_rejects_overlapping_cells(tmp_path):
    first = tmp_path / "first.parquet"
    second = tmp_path / "second.parquet"
    _complete_frame().to_parquet(first)
    _complete_frame().to_parquet(second)
    with pytest.raises(ValueError, match="duplicate"):
        load_validated_chunks([first, second], _config(), "run-a")
