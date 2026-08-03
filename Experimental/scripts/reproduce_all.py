#!/usr/bin/env python3
"""Master runner: regenerates every table and figure used in the paper.

Run all stages at once (may be slow):
    python run_all.py
Or run stage-by-stage (recommended; each stage persists to results/):
    python run_all.py --stage benchmark
    python run_all.py --stage redundancy
    python run_all.py --stage tables
    python run_all.py --stage sensitivity
    python run_all.py --stage extras
    python run_all.py --stage smartgrid
    python run_all.py --stage phase6

Use --quick for a fast smoke test (reps=5).
Outputs land in ../results/{tables,figures}; numbers.json is updated incrementally.
"""
import argparse, json, os, sys, time
import numpy as np

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code")
    ),
)
from lexpr import experiments as ex
from lexpr import smartgrid as sg

OUT = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "manuscript", "generated"
    )
)
NUM = f"{OUT}/numbers.json"


def _load():
    try:
        with open(NUM) as f:
            return json.load(f)
    except Exception:
        return {}


def _save(d):
    os.makedirs(f"{OUT}/tables", exist_ok=True)
    with open(NUM, "w") as f:
        json.dump(d, f, indent=2, default=float)


def stage_benchmark(reps, ntest):
    df, mean_store, tail_store = ex.run_benchmark_clean(
        reps=reps, n_test=ntest, outdir=OUT
    )
    summ = ex.stats_summary(mean_store, tail_store, outdir=OUT)
    main = (
        df.groupby("method")[["mean", "tail_mean"]]
        .mean()
        .reindex(ex.METHOD_ORDER)
        .reset_index()
    )
    main.columns = ["method", "loss_mean", "tail_loss"]
    main.to_csv(f"{OUT}/tables/main_comparison.csv", index=False)
    n = _load()
    n["stats"] = summ
    n["main_comparison"] = main.to_dict(orient="records")
    _save(n)
    print(
        f"  tail Friedman p={summ['tail_loss']['friedman_p']:.2e}; "
        f"LexPR tail rank={summ['tail_loss']['avg_ranks']['LexPR']:.2f}"
    )


def stage_redundancy(reps, ntest):
    rd, rd_stats = ex.run_redundancy(reps=reps, n_test=ntest, outdir=OUT)
    n = _load()
    n["redundancy"] = rd.to_dict(orient="records")
    n["redundancy_stats"] = rd_stats
    _save(n)
    print(rd.to_string(index=False))


def stage_tables(reps, ntest):
    n = _load()
    n["per_family"] = ex.per_family_table(reps=reps, n_test=ntest, outdir=OUT).to_dict(
        "records"
    )
    n["worstcase"] = ex.worstcase_table(reps=reps, outdir=OUT).to_dict("records")
    n["ablation"] = ex.ablation_table(reps=reps, n_test=ntest, outdir=OUT).to_dict(
        "records"
    )
    n["probe_reduction"] = ex.probe_reduction_table(outdir=OUT).to_dict("records")
    _save(n)


def stage_sensitivity(reps, ntest):
    ex.sensitivity_theta(reps=max(10, reps // 2), n_test=ntest, outdir=OUT)
    ex.sensitivity_nadir(reps=max(20, reps), n_test=ntest, outdir=OUT)
    df = ex.stochastic_demo(reps=max(40, reps), outdir=OUT)
    n = _load()
    n["stochastic"] = df.to_dict("records")
    _save(n)


def stage_extras(reps, ntest):
    n = _load()
    n["agreement_smaa"] = ex.agreement_with_smaa(
        reps=max(40, reps), outdir=OUT
    ).to_dict("records")
    n["dominated_exclusion"] = ex.dominated_exclusion_check()
    _save(n)
    print("  dominated-exclusion:", n["dominated_exclusion"])


def stage_smartgrid(reps, ntest):
    n = _load()
    n["smartgrid"] = sg.run_case(outdir=OUT)
    _save(n)
    print("  smart-grid held-out loss:", n["smartgrid"]["held_out_loss"])


def stage_phase6(reps, ntest):
    print("  Running Phase 6 experiments...")
    n = _load()
    n["phase6_frontier"] = ex.run_quality_stability_frontier(
        reps=reps, outdir=OUT
    ).to_dict("records")
    n["phase6_class"] = ex.run_class_evaluation(reps=reps, outdir=OUT).to_dict(
        "records"
    )
    ex.plot_relex_decision_profile(outdir=OUT)
    n["phase6_real_case"] = ex.run_real_case_study(outdir=OUT)
    _save(n)


STAGES = {
    "benchmark": stage_benchmark,
    "redundancy": stage_redundancy,
    "tables": stage_tables,
    "sensitivity": stage_sensitivity,
    "extras": stage_extras,
    "smartgrid": stage_smartgrid,
    "phase6": stage_phase6,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--stage", choices=list(STAGES) + ["all"], default="all")
    args = ap.parse_args()
    reps = 5 if args.quick else 30
    ntest = 60 if args.quick else 300
    os.makedirs(f"{OUT}/figures", exist_ok=True)
    t0 = time.time()
    todo = list(STAGES) if args.stage == "all" else [args.stage]
    for s in todo:
        print(f"[stage: {s}] ...", flush=True)
        STAGES[s](reps, ntest)
    print(f"DONE ({args.stage}) in {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
