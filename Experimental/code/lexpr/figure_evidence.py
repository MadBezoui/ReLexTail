"""Immutable evidence and provenance helpers for publication figures."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from typing import Any

import pandas as pd


AUTHORITATIVE_RUN_ID = (
    "33e81af5a748796ef2103fc0dd280bb7cb3aff6758e86ac49877cc632f036749"
)


@dataclass(frozen=True)
class ProtocolFigureEvidence:
    run_id: str
    n_instances: int
    method_names: tuple[str, ...]
    nemenyi_cd: float
    average_ranks: dict[str, float]
    config_sha256: str
    raw_path: Path
    analysis_path: Path


def authoritative_run_dir(repo_root: str | Path) -> Path:
    return Path(repo_root) / "results" / "protocol" / "runs" / AUTHORITATIVE_RUN_ID


def load_protocol_evidence(repo_root: str | Path) -> ProtocolFigureEvidence:
    """Load Figure 7 evidence from the immutable, manuscript-approved run."""
    run_dir = authoritative_run_dir(repo_root)
    analysis_path = run_dir / "tables" / "benchmark_analysis.json"
    raw_path = run_dir / "raw" / "benchmark.parquet"
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))

    if analysis.get("run_id") != AUTHORITATIVE_RUN_ID:
        raise ValueError("benchmark analysis does not match authoritative run")

    raw_ids = set(pd.read_parquet(raw_path, columns=["run_id"])["run_id"].unique())
    if raw_ids != {AUTHORITATIVE_RUN_ID}:
        raise ValueError("benchmark parquet contains non-authoritative run IDs")

    manifest_path = run_dir / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    config_sha = str(manifest.get("config_sha256", ""))
    if not config_sha:
        config_values = pd.read_parquet(raw_path, columns=["config_sha256"])[
            "config_sha256"
        ].unique()
        if len(config_values) != 1:
            raise ValueError("benchmark parquet has ambiguous configuration hashes")
        config_sha = str(config_values[0])

    methods = tuple(str(value) for value in analysis["methods"])
    if int(analysis["n_methods"]) != len(methods):
        raise ValueError("method count does not match benchmark analysis")

    return ProtocolFigureEvidence(
        run_id=AUTHORITATIVE_RUN_ID,
        n_instances=int(analysis["n_instances"]),
        method_names=methods,
        nemenyi_cd=float(analysis["nemenyi_cd"]),
        average_ranks={
            str(name): float(rank) for name, rank in analysis["average_ranks"].items()
        },
        config_sha256=config_sha,
        raw_path=raw_path,
        analysis_path=analysis_path,
    )


def _git_value(cwd: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "unknown"


def figure_provenance(
    repo_root: str | Path,
    *,
    run_id: str | None,
    params: dict[str, Any],
) -> dict[str, Any]:
    repo_root = Path(repo_root)
    params_json = json.dumps(params, sort_keys=True, separators=(",", ":"))
    return {
        "run_id": run_id,
        "git_commit": _git_value(repo_root, "rev-parse", "HEAD"),
        "git_dirty": bool(_git_value(repo_root, "status", "--porcelain")),
        "params": params,
        "params_sha256": sha256(params_json.encode("utf-8")).hexdigest(),
    }


def write_sidecar(pdf_path: str | Path, metadata: dict[str, Any]) -> Path:
    sidecar = Path(f"{pdf_path}.json")
    sidecar.write_text(
        json.dumps(metadata, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return sidecar


def evidence_metadata(evidence: ProtocolFigureEvidence) -> dict[str, Any]:
    data = asdict(evidence)
    data["raw_path"] = str(evidence.raw_path)
    data["analysis_path"] = str(evidence.analysis_path)
    return data
