#!/usr/bin/env python3
"""Validation protocol — config-driven, staged, reproducible.

Single-command reproduction:
    python run_protocol.py --config configs/pilot_config.yaml --stage all
Stage-by-stage (recommended in constrained environments):
    python run_protocol.py --config configs/pilot_config.yaml --stage benchmark
    ... redundancy | probes | gates | direct | stochastic | multistakeholder | report

Outputs -> ../results/protocol/{tables,figures}. Acceptance gates are summarised
in gates_report.{csv,json}.
"""
import argparse, hashlib, json, os, sys, time
from pathlib import Path
import numpy as np, pandas as pd, yaml
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lexpr import problems, methods, families, stats as st, gates, directopt, extras_validation
from lexpr.methods import normalize

DEFAULT_OUTPUT_ROOT = Path(__file__).resolve().parents[1] / "results" / "protocol"
ROOT = str(DEFAULT_OUTPUT_ROOT)
TAB = f"{ROOT}/tables"; FIG = f"{ROOT}/figures"
TMP = f"{ROOT}/tmp_v2"


def configure_output_root(output_root, run_id):
    """Configure all protocol paths for one immutable scientific run."""
    global ROOT, TAB, FIG, TMP
    root = Path(output_root).resolve() / "runs" / str(run_id)
    paths = {
        "root": root,
        "tables": root / "tables",
        "figures": root / "figures",
        "tmp": root / "tmp",
    }
    ROOT = str(paths["root"])
    TAB = str(paths["tables"])
    FIG = str(paths["figures"])
    TMP = str(paths["tmp"])
    return paths


def publish_current_run(run_root):
    """Atomically point <output-root>/current at a completed run directory."""
    run_root = Path(run_root).resolve()
    output_root = run_root.parents[1]
    current = output_root / "current"
    if current.exists() and not current.is_symlink():
        raise ValueError(f"refusing to replace non-symlink publication path: {current}")
    temporary = output_root / ".current.tmp"
    if temporary.is_symlink() or temporary.exists():
        temporary.unlink()
    temporary.symlink_to(Path("runs") / run_root.name, target_is_directory=True)
    os.replace(temporary, current)
    return current


_MCW = [1000]   # Monte-Carlo weight count for randomized methods (set per run)


def _select(name, F, rng):
    if name == "RW":
        return methods.select(name, F, rng=rng, n_weights=min(_MCW[0], 200))
    if name in methods.RANDOMIZED:
        return methods.select(name, F, rng=rng, n_weights=_MCW[0])
    return methods.select(name, F)


def _method_rng(seed, method):
    method_id = int.from_bytes(
        hashlib.sha256(method.encode("utf-8")).digest()[:8], "big"
    )
    return np.random.default_rng(np.random.SeedSequence([int(seed), method_id]))


def _load_json(p, d=None):
    try:
        with open(p) as f:
            return json.load(f)
    except Exception as e:
        import logging
        logging.warning(f"Error loading JSON from {p}: {e}")
        return {} if d is None else d


def _save_json(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        json.dump(obj, f, indent=2, default=float)


# --------------------------------------------------------------------------- #
def _bench_block(cfg, csizes, crits, manifest):
    geoms_all = cfg["geometries"]
    sel = cfg.get("_geoms")
    geoms = [(gi, g) for gi, g in enumerate(geoms_all) if (sel is None or g in sel)]
    reps = cfg["replications"]
    nU = cfg["utilities_per_family"]; alphas = cfg["dirichlet_alphas"]
    fam = cfg["families"]; M = cfg["methods"]; tailq = cfg["tail_q"]
    base = cfg["seed"]
    scopes = cfg.get("family_scopes", {})
    records = []
    
    run_id = manifest.get("run_id", "unknown")
    
    for N in csizes:
        for m in crits:
            for gi, g in geoms:
                for rep in range(reps):
                    a = alphas[rep % len(alphas)]
                    s = (base * 1009 + N * 131 + m * 17 + gi * 7 + rep) & 0x7fffffff
                    rr = np.random.default_rng(s)
                    F = problems.make_candidate_set(g, N, m, rr)
                    cache = families.loss_cache(F, normalize, np.random.default_rng(s + 1),
                                                alpha=a, n_per_family=nU, family_list=fam)
                    for nm in M:
                        idx = _select(nm, F, rng=_method_rng(s + 2, nm))
                        ml, tl, worst_loss, per_family = families.losses_from(
                            cache, idx, q=tailq
                        )
                        worst_family = max(per_family, key=per_family.get)
                        
                        records.append({
                            "run_id": run_id,
                            "config_sha256": manifest.get("config_sha256", ""),
                            "seed": s,
                            "N": N,
                            "m": m,
                            "actual_N": F.shape[0],
                            "geometry": g,
                            "replication": rep,
                            "dirichlet_alpha": float(a),
                            "method": nm,
                            "utility_scope": scopes.get(worst_family, "unknown"),
                            "mean_loss": float(ml),
                            "tail_loss": float(tl),
                            "worst_family": worst_family,
                            "worst_family_loss": float(worst_loss),
                            "selected_index": int(idx),
                        })
    return records


def stage_benchmark(cfg):
    """Run one chunk (restricted by --csize/--crit) and persist it, OR, with no
    restriction, run the whole suite in-memory and finalise."""
    manifest_path = os.path.join(ROOT, "run_manifest.json")
    manifest = _load_json(manifest_path)
    M = cfg["methods"]
    csizes = [cfg["_csize"]] if cfg.get("_csize") else cfg["candidate_sizes"]
    crits = cfg["_crit"] if cfg.get("_crit") else cfg["criteria"]
    records = _bench_block(cfg, csizes, crits, manifest)
    
    if cfg.get("_csize") or cfg.get("_crit") or cfg.get("_geoms"):   # chunk mode
        os.makedirs(TMP, exist_ok=True)
        cs = csizes[0] if cfg.get("_csize") else "all"
        gtag = "-".join(g[:3] for g in cfg["_geoms"]) if cfg.get("_geoms") else "allg"
        tag = f"{cs}_{'-'.join(map(str,crits))}_{gtag}"
        import pandas as pd
        pd.DataFrame(records).to_parquet(f"{TMP}/bench_{tag}.parquet")
        print(f"  saved chunk {tag}: {len(records)} records")
        return
    _benchmark_finalize_from_records(cfg, records)


def stage_bfinalize(cfg):
    """Concatenate all persisted benchmark chunks and compute final stats."""
    import glob
    files = sorted(glob.glob(f"{TMP}/bench_*.parquet"))
    if not files:
        raise SystemExit("no benchmark chunks found in tmp/")

    from lexpr.records import load_validated_chunks
    manifest = _load_json(os.path.join(ROOT, "run_manifest.json"))
    combined = load_validated_chunks(files, cfg, manifest.get("run_id", ""))
    print(f"  combined {len(files)} chunks -> {len(combined)} records")
    _benchmark_finalize_from_records(cfg, combined)

def _benchmark_finalize_from_records(cfg, records):
    import pandas as pd
    from lexpr.records import validate_benchmark_frame
    from lexpr.analysis import cluster_bootstrap_difference
    from lexpr.reporting import analyze_benchmark
    
    df = records.copy() if isinstance(records, pd.DataFrame) else pd.DataFrame(records)
    
    raw_dir = os.path.join(ROOT, "raw")
    os.makedirs(raw_dir, exist_ok=True)
    df.to_parquet(os.path.join(raw_dir, "benchmark.parquet"))
    
    manifest = _load_json(os.path.join(ROOT, "run_manifest.json"))
    validate_benchmark_frame(df, cfg, manifest.get("run_id", ""))
    
    M = cfg["methods"]
    
    os.makedirs(TAB, exist_ok=True)
    
    # 1. Global benchmark stats table
    df_global = []
    for mtd in M:
        df_global.append({
            "method": mtd,
            "mean_loss": df[df.method==mtd]["mean_loss"].mean(),
            "tail_loss": df[df.method==mtd]["tail_loss"].mean()
        })
    pd.DataFrame(df_global).to_csv(f"{TAB}/benchmark.csv", index=False)

    # 2. Stratified analysis
    # utility_scope describes the selected alternative's worst family and can
    # differ by method, so it is not a paired experimental factor.
    strat_cols = {"geometry": "geometry", "m": "dimension", "N": "size"}
    for col, fname in strat_cols.items():
        out = []
        for val in df[col].unique():
            sub = df[df[col] == val]
            cells = sub[["N", "m", "geometry", "replication"]].drop_duplicates()
            n_cells = len(cells)
            for mtd in M:
                if mtd == "LexPR": continue
                md, ci_l, ci_u, rev = cluster_bootstrap_difference(
                    sub, control="LexPR", treatment=mtd,
                    cluster_columns=["N", "m", "geometry", "replication"],
                    seed=42, n_boot=1000
                )
                out.append({
                    "stratum_variable": col,
                    "stratum_value": val,
                    "method": mtd,
                    "n_cells": n_cells,
                    "mean_diff": md,
                    "ci_lower": ci_l,
                    "ci_upper": ci_u,
                    "reversal_fraction": rev
                })
        pd.DataFrame(out).to_csv(f"{TAB}/benchmark_by_{fname}.csv", index=False)
        
    analysis = analyze_benchmark(df, cfg)
    _save_json(f"{TAB}/benchmark_analysis.json", analysis)





def stage_redundancy(cfg):
    rc = cfg["redundancy"]; rng = np.random.default_rng(cfg["seed"] + 1)
    M = cfg["methods"]; nU = cfg["utilities_per_family"]; fam = cfg["families"]
    agg = {m_: {"grp": [], "tail": []} for m_ in M}
    cluster_recovery = []
    for c in rc["latent"]:
        for struct in rc["structures"]:
            if len(struct) != c:
                struct = (struct * c)[:c]
            for _ in range(rc["replications"]):
                g = problems.GEOMETRIES[int(rng.integers(0, 4))]
                F, groups, base = problems.make_redundant_set(g, 300, struct, rng)
                # cluster recovery: adjusted agreement of discovered vs true groups
                cl = methods.correlation_clusters(F, cfg["theta"])
                lab = np.zeros(F.shape[1], int)
                for k, comp in enumerate(cl):
                    for j in comp:
                        lab[j] = k
                cluster_recovery.append(_cluster_match(lab, groups))
                cb = families.loss_cache(base, normalize, np.random.default_rng(int(rng.integers(1<<31))),
                                         n_per_family=nU, family_list=fam)
                cf = families.loss_cache(F, normalize, np.random.default_rng(int(rng.integers(1<<31))),
                                         n_per_family=nU, family_list=fam)
                selrng = np.random.default_rng(int(rng.integers(1 << 31)))
                for nm in M:
                    idx = _select(nm, F, rng=selrng)
                    agg[nm]["grp"].append(families.losses_from(cb, idx)[0])
                    agg[nm]["tail"].append(families.losses_from(cf, idx)[1])
    manifest = _load_json(os.path.join(ROOT, "run_manifest.json"))
    run_id = manifest.get("run_id", "")
    df = pd.DataFrame([dict(method=nm, grouped_loss=np.mean(agg[nm]["grp"]),
                            tail_loss=np.mean(agg[nm]["tail"])) for nm in M])
    df.insert(0, "run_id", run_id)
    os.makedirs(TAB, exist_ok=True); df.to_csv(f"{TAB}/redundancy.csv", index=False)
    _save_json(f"{TAB}/redundancy_extra.json",
               dict(run_id=run_id,
                    mean_cluster_recovery=float(np.mean(cluster_recovery))))
    print(f"  cluster recovery={np.mean(cluster_recovery):.3f}; "
          f"LexPR grp={df.set_index('method').loc['LexPR','grouped_loss']:.3f}")
    return df


def _cluster_match(lab, truth):
    """fraction of criterion pairs whose same/different-group status agrees."""
    m = len(lab); agree = tot = 0
    for i in range(m):
        for j in range(i + 1, m):
            agree += int((lab[i] == lab[j]) == (truth[i] == truth[j])); tot += 1
    return agree / tot if tot else 1.0


def stage_probes(cfg):
    from lexpr.probe_validation import compare_probe_families

    rng = np.random.default_rng(cfg["seed"] + 2)
    probe_cfg = cfg["probe_validation"]
    n_reps = int(probe_cfg["replications"])
    candidate_size = int(probe_cfg["candidate_size"])
    m_vals = list(probe_cfg["criteria"])
    thetas = list(probe_cfg["thetas"])
    geoms = list(probe_cfg.get("geometries", cfg["geometries"]))

    records = []

    for m in m_vals:
        for g in geoms:
            for rep in range(n_reps):
                F = problems.make_candidate_set(g, candidate_size, m, rng)
                for th in thetas:
                    res = compare_probe_families(F, tolerance=1e-9, theta=th)
                    res["m"] = m
                    res["geometry"] = g
                    res["replication"] = rep
                    res["theta"] = th
                    records.append(res)
                    
    df = pd.DataFrame(records)
    os.makedirs(TAB, exist_ok=True)
    df.to_csv(f"{TAB}/probes.csv", index=False)
    
    worst_regret_mean = df["worst_regret_gap"].mean()
    cert_gap_mean = df["certificate_sup_norm_gap"].mean()
    winner_agree = df["winner_agreement"].mean()
    
    max_regret = float(probe_cfg["max_worst_regret_gap"])
    max_certificate = float(probe_cfg["max_certificate_gap"])
    min_agreement = float(probe_cfg["min_winner_agreement"])
    manifest = _load_json(os.path.join(ROOT, "run_manifest.json"))
    gate_res = {
        "run_id": manifest.get("run_id", ""),
        "predictive_quality": bool(worst_regret_mean < max_regret),
        "certificate_approximation": bool(cert_gap_mean < max_certificate),
        "decision_set_agreement": bool(winner_agree > min_agreement),
        "worst_regret_gap": worst_regret_mean,
        "certificate_sup_norm_gap": cert_gap_mean,
        "winner_agreement": winner_agree,
        "thresholds": {
            "max_worst_regret_gap": max_regret,
            "max_certificate_gap": max_certificate,
            "min_winner_agreement": min_agreement,
        },
        "pass": bool(
            worst_regret_mean < max_regret
            and cert_gap_mean < max_certificate
            and winner_agree > min_agreement
        ),
    }
    
    _save_json(f"{TAB}/gates_adaptive.json", gate_res)
    print(f"  Adaptive probes: pass={gate_res['pass']} (regret={worst_regret_mean:.3f}, cert={cert_gap_mean:.3f}, agree={winner_agree:.3f})")
    return df


def stage_gates(cfg):
    g = cfg["gates"]
    manifest = _load_json(os.path.join(ROOT, "run_manifest.json"))
    res = {"run_id": manifest.get("run_id", "")}
    res["dominated"] = gates.gate_dominated_injection(g["dominated_injection"])
    res["affine"] = gates.gate_affine_invariance(tests=g["affine_tests"])
    res["nadir"] = gates.gate_nadir_error(g["nadir_errors"])
    res["normalization"] = gates.gate_normalization_stability()

    _save_json(f"{TAB}/gates_invariance.json", res)
    print(f"  dominated pass={res['dominated']['pass']} "
          f"affine={res['affine']['identical_rate']} nadir_pass={res['nadir']['pass']}")
    return res


def stage_direct(cfg):
    lin = directopt.run_linear_case(m=4, reps=10)
    mil = directopt.run_facility_location()
    manifest = _load_json(os.path.join(ROOT, "run_manifest.json"))
    out = dict(run_id=manifest.get("run_id", ""), linear=lin, milp=mil)
    _save_json(f"{TAB}/direct.json", out)
    print("  linear:", {k: round(v, 3) for k, v in lin.items()})
    print("  milp:", mil)
    return out


def stage_stochastic(cfg):
    sc = cfg["stochastic"]
    df = extras_validation.run_stochastic(train_scenarios=sc["train_scenarios"],
                                          test_scenarios=sc["test_scenarios"],
                                          alphas=tuple(sc["alphas"]))
    manifest = _load_json(os.path.join(ROOT, "run_manifest.json"))
    df.insert(0, "run_id", manifest.get("run_id", ""))
    os.makedirs(TAB, exist_ok=True); df.to_csv(f"{TAB}/stochastic.csv", index=False)
    print(df.to_string(index=False))
    return df


def stage_multistakeholder(cfg):
    df = extras_validation.run_multistakeholder(stakeholders=tuple(cfg["multistakeholder"]["stakeholders"]))
    manifest = _load_json(os.path.join(ROOT, "run_manifest.json"))
    df.insert(0, "run_id", manifest.get("run_id", ""))
    os.makedirs(TAB, exist_ok=True); df.to_csv(f"{TAB}/multistakeholder.csv", index=False)
    print(df.groupby("method")[["worst_regret", "mean_regret", "gini"]].mean().to_string())
    return df


def stage_report(cfg):
    """Assemble the acceptance-gate table from persisted stage outputs."""
    from lexpr.reporting import build_gate_report, ensure_registered_gates

    manifest = _load_json(os.path.join(ROOT, "run_manifest.json"))
    run_id = manifest.get("run_id", "")
    analysis = _load_json(f"{TAB}/benchmark_analysis.json")
    adaptive = _load_json(f"{TAB}/gates_adaptive.json")
    gi = _load_json(f"{TAB}/gates_invariance.json")
    artifacts = {}
    if analysis:
        artifacts["benchmark_analysis"] = analysis
    if adaptive:
        artifacts["adaptive"] = adaptive
    rows = build_gate_report(artifacts, cfg, run_id)

    def add(gate, passed, detail):
        rows.append(dict(
            run_id=run_id,
            gate=gate,
            result="PASS" if passed else "CHECK",
            threshold=None,
            estimate=None,
            detail=detail,
        ))

    def add_check(gate, detail, estimate=None):
        rows.append(dict(
            run_id=run_id,
            gate=gate,
            result="CHECK",
            threshold=None,
            estimate=estimate,
            detail=detail,
        ))

    if gi:
        if gi.get("run_id") != run_id:
            raise ValueError("invariance evidence run_id does not match report")
        d = gi["dominated"]; add("dominated_injection",
            d["pass"], f"{d['violations']}/{d['trials']} violations")
        a = gi["affine"]; add("affine_invariance",
            a["pass"], f"identical rate {a['identical_rate']}")
        nd = gi["nadir"]; add("nadir_sensitivity",
            nd["pass"], f"max quality degradation {nd['max_quality_degradation']}")
    # redundancy
    try:
        rd = pd.read_csv(f"{TAB}/redundancy.csv").set_index("method")
        if set(rd["run_id"]) != {run_id}:
            raise ValueError("redundancy evidence run_id does not match report")
        avg = rd.loc[["TOPSIS", "SMAA", "RW"], "grouped_loss"].mean()
        add("redundancy_grouped_loss", rd.loc["LexPR", "grouped_loss"] < avg,
            f"LexPR {rd.loc['LexPR','grouped_loss']:.3f} vs avg {avg:.3f}")
        extra = _load_json(f"{TAB}/redundancy_extra.json")
        if extra.get("run_id") != run_id:
            raise ValueError("cluster evidence run_id does not match report")
        recovery = float(extra["mean_cluster_recovery"])
        add("cluster_recovery", recovery >= 0.8,
            f"mean pairwise group recovery {recovery:.3f}")
    except Exception as e:
        import logging
        logging.warning(f"Failed to load run manifest or stats: {e}")
    # direct
    try:
        dr = _load_json(f"{TAB}/direct.json")
        if dr.get("run_id") != run_id:
            raise ValueError("direct evidence run_id does not match report")
        lin = dr["linear"]
        add_check("direct_lp_exactness",
            "current LP experiment compares sampled-front tail quality, not exact certificates",
            {"direct_calls": lin["direct_calls"], "enum_calls": lin["enum_calls"]})
        milp = dr.get("milp", {})
        add_check("direct_milp_exactness",
            "current facility-location method is a four-solve proxy, not an exact direct MILP",
            {"available": milp.get("available", False),
             "same_choice": milp.get("chosen_enum") == milp.get("chosen_direct")})
    except Exception as e:
        import logging
        logging.warning(f"Failed to load direct.json: {e}")
    # stochastic
    try:
        sd = pd.read_csv(f"{TAB}/stochastic.csv").set_index("method")
        if set(sd["run_id"]) != {run_id}:
            raise ValueError("stochastic evidence run_id does not match report")
        best_alpha = sd.filter(like="LexPR-a", axis=0)["tail_loss"].min()
        add_check("stochastic_calibration",
            "train/test illustration lacks a registered confidence-coverage calibration test",
            {"best_alpha_tail": best_alpha,
             "deterministic_tail": sd.loc["det-LexPR", "tail_loss"]})
    except Exception as e:
        import logging
        logging.warning(f"Failed to load multi-stakeholder or stochastic CSV: {e}")
    try:
        ms = pd.read_csv(f"{TAB}/multistakeholder.csv")
        if set(ms["run_id"]) != {run_id}:
            raise ValueError("stakeholder evidence run_id does not match report")
        add_check("stakeholder_tradeoff",
            "current metrics overlap the optimized worst-regret objective; independent validation is required")
    except Exception as e:
        import logging
        logging.warning(f"Failed to load multi-stakeholder CSV: {e}")

    claims_path = Path(__file__).resolve().parent / "configs" / "claims.yaml"
    with claims_path.open() as handle:
        claims = yaml.safe_load(handle)["claims"]
    rows = ensure_registered_gates(rows, claims, run_id)
    rep = pd.DataFrame(rows)
    rep.to_csv(f"{TAB}/gates_report.csv", index=False)
    _save_json(f"{TAB}/gates_report.json", rows)
    publish_current_run(Path(ROOT))
    print(rep.to_string(index=False))
    return rep


STAGES = {"benchmark": stage_benchmark, "bfinalize": stage_bfinalize,
          "redundancy": stage_redundancy,
          "probes": stage_probes, "gates": stage_gates, "direct": stage_direct,
          "stochastic": stage_stochastic, "multistakeholder": stage_multistakeholder,
          "report": stage_report}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/pilot_config.yaml")
    ap.add_argument("--stage", default="all", choices=list(STAGES) + ["all"])
    ap.add_argument("--csize", type=int, default=None,
                    help="restrict benchmark to one candidate size (chunked run)")
    ap.add_argument("--crit", default=None,
                    help="comma list of criteria counts to restrict the benchmark chunk")
    ap.add_argument("--utils", type=int, default=None,
                    help="override utilities_per_family (for time-constrained runs)")
    ap.add_argument("--mcw", type=int, default=None,
                    help="Monte-Carlo weight count for randomized methods")
    ap.add_argument("--geoms", default=None,
                    help="comma list of geometries to restrict the benchmark chunk")
    ap.add_argument("--new-run-id", action="store_true", help="Force overwrite of manifest if config hashes differ")
    ap.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT),
                    help="base directory containing isolated protocol runs")
    args = ap.parse_args()
    if args.mcw:
        _MCW[0] = args.mcw
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           args.config)) as f:
        cfg = yaml.safe_load(f)
    cfg["_csize"] = args.csize
    cfg["_crit"] = [int(x) for x in args.crit.split(",")] if args.crit else None
    cfg["_geoms"] = [x.strip() for x in args.geoms.split(",")] if args.geoms else None
    if args.utils:
        cfg["utilities_per_family"] = args.utils
    from lexpr.provenance import build_manifest
    cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.config)
    manifest = build_manifest(cfg_path, seed=cfg.get("seed", 42))
    configure_output_root(args.output_root, manifest["run_id"])
    os.makedirs(TAB, exist_ok=True); os.makedirs(FIG, exist_ok=True)
    manifest_path = os.path.join(ROOT, "run_manifest.json")
    if os.path.exists(manifest_path):
        existing = _load_json(manifest_path)
        if existing.get("run_id") != manifest["run_id"] and not args.new_run_id:
            sys.exit("Error: run_id mismatch with existing run_manifest.json. Use --new-run-id to overwrite.")
    _save_json(manifest_path, manifest)

    # 'all' should not silently chunk-skip finalisation
    todo = [s for s in STAGES if s != "bfinalize"] if args.stage == "all" else [args.stage]
    for s in todo:
        t0 = time.time(); print(f"[protocol stage: {s}]", flush=True)
        STAGES[s](cfg); print(f"  ...{time.time()-t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
