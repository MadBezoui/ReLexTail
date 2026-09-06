"""Turn the raw result files into the manuscript's tables, figures and registry.

Every number the manuscript prints about the enhanced engine is produced here
from ``enhanced/results/``.  The script fails loudly on missing or empty inputs
rather than emitting a partial report, so a stale figure cannot survive a
failed run.

Statistics.  The independent unit is the instance.  Contrasts are paired within
instance; intervals are percentile bootstrap over instances (10,000 resamples,
fixed seed); the Wilcoxon signed-rank test accompanies them.  Holm correction is
applied within the prespecified family {P1, P2} only, and every other contrast
is labelled exploratory.  Because the study was not preregistered with a third
party, p-values are descriptive.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
TABLES = ROOT / "analysis" / "tables"
FIGURES = ROOT / "analysis" / "figures"
sys.path.insert(0, str(ROOT / "src"))

BOOTSTRAP = 10_000
SEED = 20260906

ARM_LABEL = {
    "A0_global_independent": "A0 retention gate, independent quotient",
    "A1_decision_independent": "A1 decision gate, independent quotient",
    "A2_decision_joint": "A2 decision gate, joint quotient",
    "A3_decision_joint_relevant": "A3 + decision-relevant branching",
}
ARM_ORDER = list(ARM_LABEL)


def read_csv(path: Path) -> list:
    if not path.exists() or not path.read_text().strip():
        raise SystemExit(f"missing or empty result file: {path}")
    with path.open() as fh:
        return list(csv.DictReader(fh))


def _f(x):
    return float(x) if x not in ("", None, "None") else float("nan")


def _b(x):
    return str(x).lower() == "true"


# ------------------------------------------------------------------ statistics
def paired_effect(a, b, rng):
    """Mean paired difference ``a - b`` with a percentile bootstrap interval."""
    d = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    d = d[np.isfinite(d)]
    if d.size == 0:
        return None
    idx = rng.integers(0, d.size, size=(BOOTSTRAP, d.size))
    boot = d[idx].mean(axis=1)
    wins = int(np.sum(d > 0))
    losses = int(np.sum(d < 0))
    out = {
        "n": int(d.size),
        "mean_difference": float(d.mean()),
        "median_difference": float(np.median(d)),
        "ci_low": float(np.percentile(boot, 2.5)),
        "ci_high": float(np.percentile(boot, 97.5)),
        "wins": wins,
        "losses": losses,
        "ties": int(d.size - wins - losses),
        "prob_superiority": float((wins + 0.5 * (d.size - wins - losses)) / d.size),
    }
    try:
        from scipy.stats import wilcoxon

        if wins + losses > 0:
            out["wilcoxon_p"] = float(wilcoxon(d, zero_method="wilcox").pvalue)
        else:
            out["wilcoxon_p"] = 1.0
    except Exception:
        out["wilcoxon_p"] = float("nan")
    return out


def holm(pvalues: dict) -> dict:
    """Holm step-down adjustment within a declared family."""
    items = sorted(pvalues.items(), key=lambda kv: kv[1])
    n = len(items)
    adjusted, running = {}, 0.0
    for i, (key, p) in enumerate(items):
        running = max(running, min(1.0, (n - i) * p))
        adjusted[key] = running
    return adjusted


# ---------------------------------------------------------------------- tables
def build_tables(cert, mech, anytime):
    TABLES.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    by_instance = {}
    for r in cert:
        by_instance.setdefault(r["instance"], {})[r["arm"]] = r

    report = {"splits": {}, "families": {}, "primary": {}, "exploratory": {}}

    # --- per-arm summary, per split ---------------------------------------
    summary_rows = []
    for split in ("development", "calibration", "test", "stress"):
        rows = [r for r in cert if r["data_split"] == split]
        if not rows:
            continue
        for arm in ARM_ORDER:
            a = [r for r in rows if r["arm"] == arm]
            if not a:
                continue
            rho = np.array([_f(r["rho_lower"]) for r in a])
            vol = np.array([_f(r["focal_certified_volume"]) for r in a])
            cflag = np.array([_b(r["focal_certified"]) for r in a])
            boxes = np.array([_f(r["focal_boxes"]) for r in a])
            summary_rows.append(
                {
                    "split": split,
                    "arm": arm,
                    "label": ARM_LABEL[arm],
                    "n_instances": len(a),
                    "mean_rho_lower": float(rho.mean()),
                    "median_rho_lower": float(np.median(rho)),
                    "share_rho_positive": float((rho > 0).mean()),
                    "mean_focal_certified_volume": float(vol.mean()),
                    "share_focal_certified": float(cflag.mean()),
                    "median_focal_boxes": float(np.median(boxes)),
                }
            )
    _write(TABLES / "arm_summary.csv", summary_rows)
    report["splits"] = summary_rows

    # --- primary contrasts on the locked test split -----------------------
    contrasts = {
        "P1_decision_focus": ("A1_decision_independent", "A0_global_independent"),
        "P2_dependency": ("A2_decision_joint", "A1_decision_independent"),
    }
    exploratory = {
        "E1_branching": ("A3_decision_joint_relevant", "A2_decision_joint"),
        "E2_full_vs_baseline": ("A3_decision_joint_relevant", "A0_global_independent"),
    }

    def contrast_rows(pairs, split, label):
        out, pvals = [], {}
        for name, (hi, lo) in pairs.items():
            ids = [
                i for i, d in by_instance.items()
                if hi in d and lo in d and d[hi]["data_split"] == split
            ]
            if not ids:
                continue
            eff = paired_effect(
                [_f(by_instance[i][hi]["rho_lower"]) for i in ids],
                [_f(by_instance[i][lo]["rho_lower"]) for i in ids],
                rng,
            )
            volume = paired_effect(
                [_f(by_instance[i][hi]["focal_certified_volume"]) for i in ids],
                [_f(by_instance[i][lo]["focal_certified_volume"]) for i in ids],
                rng,
            )
            row = {
                "contrast": name, "family": label, "split": split,
                "outcome": "rho_lower", **eff,
                "volume_mean_difference": volume["mean_difference"],
                "volume_ci_low": volume["ci_low"],
                "volume_ci_high": volume["ci_high"],
            }
            out.append(row)
            pvals[name] = eff["wilcoxon_p"]
        if label == "primary" and pvals:
            adj = holm(pvals)
            for row in out:
                row["holm_adjusted_p"] = adj[row["contrast"]]
        return out

    primary = contrast_rows(contrasts, "test", "primary")
    expl = contrast_rows(exploratory, "test", "exploratory")
    stress = contrast_rows({**contrasts, **exploratory}, "stress", "exploratory")
    _write(TABLES / "contrasts.csv", primary + expl + stress)
    report["primary"] = primary
    report["exploratory"] = expl + stress

    # --- per-family effects (reported before aggregation) -----------------
    fam_rows = []
    families = sorted({r["family"] for r in cert})
    for fam in families:
        ids = [i for i, d in by_instance.items()
               if any(r["family"] == fam for r in d.values())]
        for name, (hi, lo) in {**contrasts, **exploratory}.items():
            sel = [i for i in ids if hi in by_instance[i] and lo in by_instance[i]]
            if not sel:
                continue
            eff = paired_effect(
                [_f(by_instance[i][hi]["rho_lower"]) for i in sel],
                [_f(by_instance[i][lo]["rho_lower"]) for i in sel],
                rng,
            )
            fam_rows.append({"family": fam, "contrast": name, **eff})
    _write(TABLES / "family_effects.csv", fam_rows)
    report["families"] = fam_rows

    # --- E1 mechanism -----------------------------------------------------
    mech_rows = []
    CATEGORICAL = {"C_M", "C_25", "C_50", "C_100"}
    for m in ("independent", "joint"):
        rows = [r for r in mech if r["mode"] == m and not _b(r["refused"])
                and not _b(r.get("tied_nominal", "False"))]
        if not rows:
            continue
        # The decisive coordinate is a category count on some instances and a
        # tail mean on others; the two are not in the same units, so the
        # coordinate-width statistic is reported over categorical decisive
        # coordinates only, with its own denominator.
        cat = [r for r in rows if r.get("decisive_coordinate") in CATEGORICAL]
        mech_rows.append(
            {
                "mode": m,
                "n": len(rows),
                "n_categorical_decisive": len(cat),
                "mean_max_D_width": float(np.mean([_f(r["max_D_width"]) for r in rows])),
                "mean_mean_D_width": float(np.mean([_f(r["mean_D_width"]) for r in rows])),
                "median_winner_coordinate_width": float(
                    np.median([_f(r["winner_enclosure_width"]) for r in cat])
                ) if cat else float("nan"),
                "median_rival_coordinate_width": float(
                    np.median([_f(r["rival_enclosure_width"]) for r in cat])
                ) if cat else float("nan"),
                "share_certified_at_root": float(
                    np.mean([_b(r["certified_at_root"]) for r in rows])
                ),
            }
        )
    _write(TABLES / "mechanism_summary.csv", mech_rows)
    report["mechanism"] = mech_rows

    # --- decisive coordinate distribution ---------------------------------
    counts = {}
    for r in mech:
        if r["mode"] != "joint" or _b(r["refused"]):
            continue
        c = r.get("decisive_coordinate") or "tied"
        counts[c] = counts.get(c, 0) + 1
    _write(
        TABLES / "decisive_coordinates.csv",
        [{"coordinate": k, "count": v} for k, v in sorted(counts.items())],
    )

    # --- E7 anytime -------------------------------------------------------
    any_rows = []
    for arm in ("A0_global_independent", "A3_decision_joint_relevant"):
        for b in sorted({int(_f(r["budget"])) for r in anytime}):
            rows = [r for r in anytime if r["arm"] == arm and int(_f(r["budget"])) == b]
            if not rows:
                continue
            any_rows.append(
                {
                    "arm": arm, "budget": b, "n": len(rows),
                    "mean_certified_volume": float(
                        np.mean([_f(r["certified_volume"]) for r in rows])
                    ),
                    "share_certified": float(np.mean([_b(r["certified"]) for r in rows])),
                    "mean_seconds": float(np.mean([_f(r["seconds"]) for r in rows])),
                }
            )
    _write(TABLES / "anytime.csv", any_rows)
    report["anytime"] = any_rows

    # --- bracket ----------------------------------------------------------
    bracket = []
    for r in cert:
        if r["arm"] != "A3_decision_joint_relevant":
            continue
        w = r.get("witness_level")
        bracket.append(
            {
                "instance": r["instance"], "family": r["family"],
                "split": r["data_split"], "rho_lower": _f(r["rho_lower"]),
                "witness_level": _f(w) if w not in ("", "None", None) else None,
            }
        )
    _write(TABLES / "radius_bracket.csv", bracket)
    valid = [b for b in bracket if b["witness_level"] is not None]
    report["bracket"] = {
        "n_with_witness": len(valid),
        "n_total": len(bracket),
        "any_inversion": any(b["rho_lower"] > b["witness_level"] for b in valid),
        "median_bracket_width": (
            float(np.median([b["witness_level"] - b["rho_lower"] for b in valid]))
            if valid else None
        ),
    }
    return report


# --------------------------------------------------------------------- figures
def build_figures(cert, mech, anytime):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    FIGURES.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 8, "axes.grid": True, "grid.alpha": 0.3,
                         "figure.dpi": 200, "savefig.bbox": "tight"})
    # colourblind-safe, ordered light to dark
    C = ["#999999", "#0072B2", "#D55E00", "#009E73"]

    by_instance = {}
    for r in cert:
        by_instance.setdefault(r["instance"], {})[r["arm"]] = r

    # --- F1 certification ladder -----------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.6))
    for ax, split in zip(axes, ("test", "stress")):
        data = [
            [_f(d[a]["rho_lower"]) for d in by_instance.values()
             if a in d and d[a]["data_split"] == split]
            for a in ARM_ORDER
        ]
        parts = ax.boxplot(data, patch_artist=True, widths=0.6,
                           medianprops=dict(color="black"), showfliers=False)
        for patch, c in zip(parts["boxes"], C):
            patch.set_facecolor(c)
            patch.set_alpha(0.75)
        for i, d in enumerate(data, 1):
            ax.scatter(np.full(len(d), i) + np.random.default_rng(i).normal(0, .05, len(d)),
                       d, s=3, color="black", alpha=0.35, zorder=3)
        ax.set_xticks(range(1, len(ARM_ORDER) + 1))
        ax.set_xticklabels(["A0", "A1", "A2", "A3"])
        ax.set_title(f"{split} split (n={len(data[0])})")
    axes[0].set_ylabel(r"certified radius lower bound $\rho^{\mathrm{lo}}$")
    fig.suptitle("Certified decision radius at a matched box budget", y=1.02)
    fig.tight_layout()
    fig.savefig(FIGURES / "fig_certification_ladder.pdf")
    plt.close(fig)

    # --- F2 mechanism: enclosure width ------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.6))
    per = {}
    for r in mech:
        if _b(r["refused"]):
            continue
        per.setdefault(r["instance"], {})[r["mode"]] = r
    pairs = [(v["independent"], v["joint"]) for v in per.values()
             if "independent" in v and "joint" in v]
    x = [_f(a["max_D_width"]) for a, _ in pairs]
    y = [_f(b["max_D_width"]) for _, b in pairs]
    axes[0].scatter(x, y, s=6, color=C[1], alpha=0.6)
    lim = [0, max(max(x, default=1), max(y, default=1)) * 1.05]
    axes[0].plot(lim, lim, color="black", lw=0.8, ls="--")
    axes[0].set_xlim(lim); axes[0].set_ylim(lim)
    axes[0].set_xlabel("independent quotient"); axes[0].set_ylabel("joint quotient")
    axes[0].set_title("widest disappointment enclosure")
    xi = [_f(a["winner_enclosure_width"]) for a, _ in pairs]
    yi = [_f(b["winner_enclosure_width"]) for _, b in pairs]
    finite = [(a, b) for a, b in zip(xi, yi) if np.isfinite(a) and np.isfinite(b)]
    if finite:
        a_, b_ = zip(*finite)
        axes[1].scatter(a_, b_, s=6, color=C[2], alpha=0.6)
        lim = [0, max(max(a_), max(b_)) * 1.05 + 1e-9]
        axes[1].plot(lim, lim, color="black", lw=0.8, ls="--")
        axes[1].set_xlim(lim); axes[1].set_ylim(lim)
    axes[1].set_xlabel("independent quotient"); axes[1].set_ylabel("joint quotient")
    axes[1].set_title("width of the decisive coordinate")
    fig.suptitle("Dependency preservation tightens the comparison that decides", y=1.02)
    fig.tight_layout()
    fig.savefig(FIGURES / "fig_mechanism.pdf")
    plt.close(fig)

    # --- F3 anytime progression and radius bracket, one composite figure ---
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.6),
                             gridspec_kw={"width_ratios": [1, 1.7]})
    ax = axes[0]
    for arm, c, lab in (("A0_global_independent", C[0], "A0 retention gate"),
                        ("A3_decision_joint_relevant", C[3], "A3 enhanced")):
        budgets = sorted({int(_f(r["budget"])) for r in anytime})
        ys = [
            np.mean([_f(r["certified_volume"]) for r in anytime
                     if r["arm"] == arm and int(_f(r["budget"])) == b] or [np.nan])
            for b in budgets
        ]
        ax.plot(budgets, ys, marker="o", ms=3, color=c, label=lab)
    ax.set_xscale("log", base=2)
    ax.set_xlabel("processed boxes")
    ax.set_ylabel(r"mean certified volume of $\mathcal{B}(0.02)$")
    ax.set_ylim(bottom=0.0)
    ax.legend(frameon=False, loc="center left", fontsize=7)
    ax.set_title("A. Anytime progression")

    ax = axes[1]
    rows = [r for r in cert if r["arm"] == "A3_decision_joint_relevant"]
    rows = [r for r in rows if r.get("witness_level") not in ("", "None", None)
            and _f(r["rho_lower"]) > 0]
    rows.sort(key=lambda r: _f(r["rho_lower"]))
    if rows:
        xs = np.arange(len(rows))
        lo = [_f(r["rho_lower"]) for r in rows]
        hi = [_f(r["witness_level"]) for r in rows]
        ax.vlines(xs, lo, hi, color=C[1], lw=0.8, alpha=0.6)
        ax.scatter(xs, lo, s=5, color=C[3], label="certified lower bound", zorder=3)
        ax.scatter(xs, hi, s=5, color=C[2], marker="v",
                   label="verified switch witness", zorder=3)
        ax.set_yscale("log")
        ax.set_xlabel("instances with a witness, ordered by certified lower bound")
        ax.set_ylabel(r"level $p$")
        ax.set_ylim(top=max(hi) * 3.0)
        ax.legend(frameon=False, ncol=2, loc="upper center", fontsize=7)
    ax.set_title("B. Two-sided bracket on the decision radius")
    fig.tight_layout()
    fig.savefig(FIGURES / "fig_certification_progress.pdf")
    plt.close(fig)
    return sorted(p.name for p in FIGURES.glob("*.pdf"))


def _write(path: Path, rows) -> None:
    if not rows:
        path.write_text("")
        return
    keys, seen = [], set()
    for r in rows:
        for k in r:
            if k not in seen:
                seen.add(k)
                keys.append(k)
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main() -> int:
    cert = read_csv(RESULTS / "certification.csv")
    mech = read_csv(RESULTS / "mechanism.csv")
    anytime = read_csv(RESULTS / "anytime.csv")
    report = build_tables(cert, mech, anytime)
    report["figures"] = build_figures(cert, mech, anytime)
    correctness = json.loads((RESULTS / "correctness.json").read_text())
    report["correctness"] = {
        "instances_checked": len(correctness),
        "oracle_draws": sum(c["checked"] for c in correctness),
        "oracle_violations": sum(c["violations"] for c in correctness),
        "leaves_replayed": sum(c.get("replay_leaves", 0) for c in correctness),
        "replay_failures": sum(c.get("replay_failures", 0) for c in correctness),
    }
    (ROOT / "analysis" / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report["correctness"], indent=2))
    print(json.dumps(report["primary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
