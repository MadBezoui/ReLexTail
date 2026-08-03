from __future__ import annotations

import numpy as np
import pandas as pd

from . import stats as st
from .gates import noninferiority_cluster


CELL_COLUMNS = ["N", "m", "geometry", "replication"]


def analyze_benchmark(frame: pd.DataFrame, cfg: dict) -> dict:
    run_ids = frame["run_id"].unique()
    if len(run_ids) != 1:
        raise ValueError("benchmark analysis requires exactly one run_id")
    methods = list(cfg["methods"])
    pivot = frame.pivot(index=CELL_COLUMNS, columns="method", values="tail_loss")
    pivot = pivot.reindex(columns=methods)
    if pivot.isna().any().any():
        raise ValueError("benchmark analysis requires complete paired method cells")
    losses = pivot.to_numpy(dtype=float)
    ranks = st.average_ranks(losses)
    friedman_stat, friedman_p = st.friedman(losses)
    wilcoxon = st.wilcoxon_holm(losses, methods, control="LexPR")

    ni_cfg = cfg.get("noninferiority", {})
    noninferiority = {}
    for control in ni_cfg.get("controls", []):
        noninferiority[control] = noninferiority_cluster(
            frame,
            ctrl_name=control,
            lexpr_name="LexPR",
            ni_cfg=ni_cfg,
            seed=int(cfg.get("seed", 0)),
        )

    summary = (
        frame.groupby("method", sort=False)[["mean_loss", "tail_loss"]]
        .mean()
        .reindex(methods)
        .reset_index()
        .to_dict(orient="records")
    )
    return {
        "run_id": str(run_ids[0]),
        "n_instances": int(len(pivot)),
        "n_methods": int(len(methods)),
        "methods": methods,
        "summary": summary,
        "friedman": {"statistic": friedman_stat, "p_value": friedman_p},
        "nemenyi_cd": st.nemenyi_cd(len(methods), len(pivot)),
        "average_ranks": {name: float(rank) for name, rank in zip(methods, ranks)},
        "wilcoxon_vs_LexPR": {
            name: {"p_raw": raw, "p_holm": holm, "delta": delta}
            for name, (raw, holm, delta) in wilcoxon.items()
        },
        "noninferiority": noninferiority,
    }


def _row(run_id, gate, result, threshold=None, estimate=None, detail=""):
    return {
        "run_id": run_id,
        "gate": gate,
        "result": result,
        "threshold": threshold,
        "estimate": estimate,
        "detail": detail,
    }


def build_gate_report(artifacts: dict, cfg: dict, run_id: str) -> list[dict]:
    analysis = artifacts.get("benchmark_analysis")
    if analysis is None:
        return [
            _row(
                run_id,
                f"tail_noninferiority_{name.lower()}",
                "MISSING",
                detail="matching benchmark analysis is missing",
            )
            for name in ("ASF", "MMR")
        ]
    if analysis.get("run_id") != run_id:
        raise ValueError("benchmark analysis run_id does not match the report run_id")

    rows = []
    noninferiority = analysis.get("noninferiority", {})
    margin = cfg.get("noninferiority", {}).get("margin_absolute", 0.01)
    for control in ("ASF", "MMR"):
        result = noninferiority.get(control)
        gate = f"tail_noninferiority_{control.lower()}"
        if result is None:
            rows.append(
                _row(
                    run_id,
                    gate,
                    "MISSING",
                    margin,
                    detail="non-inferiority evidence is missing",
                )
            )
            continue
        ci = result.get("ci", result.get("ci95"))
        state = "PASS" if result.get("noninferior", False) else "CHECK"
        rows.append(
            _row(
                run_id,
                gate,
                state,
                margin,
                result.get("mean_diff"),
                f"mean LexPR-control difference {result.get('mean_diff')}; CI {ci}",
            )
        )

    practical = ["TOPSIS", "CP", "Knee", "RW", "SMAA"]
    comparisons = analysis.get("wilcoxon_vs_LexPR", {})
    available = [name for name in practical if name in comparisons]
    if len(available) != len(practical):
        rows.append(
            _row(
                run_id,
                "better_than_practical_baselines_tail",
                "MISSING",
                detail="one or more practical-baseline comparisons are missing",
            )
        )
    else:
        passed = all(
            comparisons[name]["p_holm"] < 0.05 and comparisons[name]["delta"] > 0
            for name in practical
        )
        rows.append(
            _row(
                run_id,
                "better_than_practical_baselines_tail",
                "PASS" if passed else "CHECK",
                "Holm p<0.05 and Cliff delta>0 for every registered baseline",
                {name: comparisons[name] for name in practical},
            )
        )
    adaptive = artifacts.get("adaptive")
    adaptive_specs = (
        (
            "probe_tail_gap",
            "predictive_quality",
            "worst_regret_gap",
            "max_worst_regret_gap",
        ),
        (
            "probe_certificate_gap",
            "certificate_approximation",
            "certificate_sup_norm_gap",
            "max_certificate_gap",
        ),
        (
            "probe_tolerance_overlap",
            "decision_set_agreement",
            "winner_agreement",
            "min_winner_agreement",
        ),
    )
    if adaptive is None:
        rows.extend(
            _row(run_id, gate, "MISSING", detail="adaptive-probe evidence is missing")
            for gate, _, _, _ in adaptive_specs
        )
    else:
        if adaptive.get("run_id") != run_id:
            raise ValueError("adaptive-probe run_id does not match the report run_id")
        thresholds = adaptive.get("thresholds", {})
        for gate, pass_key, estimate_key, threshold_key in adaptive_specs:
            passed = bool(adaptive.get(pass_key, False))
            estimate = adaptive.get(estimate_key)
            threshold = thresholds.get(threshold_key)
            rows.append(
                _row(
                    run_id,
                    gate,
                    "PASS" if passed else "CHECK",
                    threshold,
                    estimate,
                    f"{estimate_key}={estimate}; threshold={threshold}",
                )
            )
    return rows


def ensure_registered_gates(rows: list[dict], claims: dict, run_id: str) -> list[dict]:
    completed = list(rows)
    names = [row["gate"] for row in completed]
    if len(names) != len(set(names)):
        raise ValueError("gate report contains duplicate gate names")
    if any(row.get("run_id") != run_id for row in completed):
        raise ValueError("gate report contains a mismatched run_id")
    required = []
    for claim in claims.values():
        for gate in claim.get("gates", []):
            if gate not in required:
                required.append(gate)
    present = set(names)
    for gate in required:
        if gate not in present:
            completed.append(
                _row(
                    run_id,
                    gate,
                    "MISSING",
                    detail="required claim evidence is missing",
                )
            )
    return completed
