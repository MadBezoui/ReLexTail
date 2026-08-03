"""Acceptance gates and paired statistics for the Validation protocol.

Gates (each returns a dict with a boolean `pass` and the supporting numbers):
    gate_dominated_injection : LexPR never selects a dominated alternative.
    gate_affine_invariance   : LexPR choice is invariant to positive affine rescaling.
    gate_nadir_error         : quality stable / choice-change reported under nadir error.
    noninferiority           : paired non-inferiority of LexPR vs a control on tail loss.
"""
from __future__ import annotations
import numpy as np
from scipy import stats as sps
from . import problems, methods, families, stats
from .methods import normalize


# --------------------------------------------------------------------------- #
def gate_dominated_injection(ratios, trials=150, n=200, seed=5):
    """Inject dominated alternatives at several ratios; LexPR must never pick one,
    and we also report how often the chosen non-dominated solution changes when
    bounds are recomputed after injection."""
    rng = np.random.default_rng(seed)
    geoms = problems.GEOMETRIES
    violations = 0
    change = {r: 0 for r in ratios}
    total = 0
    for _ in range(trials):
        m = int(rng.integers(3, 9))
        g = geoms[int(rng.integers(0, len(geoms)))]
        F0 = problems.make_candidate_set(g, n, m, rng)
        base_idx = methods.lexpr(F0)
        base_choice = F0[base_idx].copy()
        total += 1
        for r in ratios:
            k = int(r * n)
            if k == 0:
                continue
            anchors = F0[rng.integers(0, F0.shape[0], size=k)]
            dom = anchors + rng.uniform(0.05, 0.4, size=anchors.shape)  # strictly worse
            F = np.vstack([F0, dom])
            idx = methods.lexpr(F)
            # dominated-selection check
            f = F[idx]
            dommask = np.all(F <= f, axis=1) & np.any(F < f, axis=1)
            dommask[idx] = False
            if dommask.any():
                violations += 1
            # choice-change among non-dominated (bounds recomputed on F)
            if not np.allclose(F[idx], base_choice):
                change[r] += 1
    return dict(
        name="dominated_injection",
        violations=int(violations),
        trials=int(total),
        **{f"change_rate_{r}": round(change[r] / total, 3) for r in ratios if r > 0},
        **{"pass": violations == 0},
    )


def gate_affine_invariance(tests=3000, n=150, seed=9, tol=0):
    """Random positive affine rescaling f_i' = a_i f_i + b_i (a_i>0). With bounds
    recomputed consistently, LexPR must select the SAME alternative."""
    rng = np.random.default_rng(seed)
    geoms = problems.GEOMETRIES
    same = 0
    for _ in range(tests):
        m = int(rng.integers(3, 9))
        g = geoms[int(rng.integers(0, len(geoms)))]
        F = problems.make_candidate_set(g, n, m, rng)
        i0 = methods.lexpr(F)
        actual_m = F.shape[1]
        a = rng.uniform(0.2, 5.0, size=actual_m)
        b = rng.uniform(-2.0, 2.0, size=actual_m)
        i1 = methods.lexpr(F * a + b)
        same += int(i0 == i1)
    rate = same / tests
    return dict(
        name="affine_invariance",
        identical_rate=round(rate, 4),
        tests=int(tests),
        **{"pass": rate >= 0.999},
    )


def gate_nadir_error(errors, reps=30, n=250, m=8, seed=37, n_test=300):
    """Paired quality and choice-change diagnostics under relative nadir error."""
    rng = np.random.default_rng(seed)
    aggregates = {
        float(error): {"loss": [], "flip": [], "degradation": []} for error in errors
    }
    records = []
    for replication in range(reps):
        geometry = problems.GEOMETRIES[int(rng.integers(0, 4))]
        F = problems.make_candidate_set(geometry, n, m, rng)
        ideal = F.min(0)
        nadir = F.max(0)
        baseline_index = methods.lexpr(F, ideal=ideal, nadir=nadir)
        cache_seed = int(rng.integers(0, 2**31))
        cache = families.loss_cache(
            F, normalize, np.random.default_rng(cache_seed), n_per_family=n_test
        )
        baseline_loss = families.losses_from(cache, baseline_index)[1]
        perturbation = rng.standard_normal(F.shape[1])
        for error_value in errors:
            error = float(error_value)
            perturbed_nadir = np.maximum(
                nadir * (1 + error * perturbation), ideal + 1e-3
            )
            index = methods.lexpr(F, ideal=ideal, nadir=perturbed_nadir)
            loss = families.losses_from(cache, index)[1]
            flip = float(index != baseline_index)
            degradation = float(loss - baseline_loss)
            aggregates[error]["loss"].append(loss)
            aggregates[error]["flip"].append(flip)
            aggregates[error]["degradation"].append(degradation)
            records.append(
                {
                    "replication": replication,
                    "geometry": geometry,
                    "error": error,
                    "baseline_index": int(baseline_index),
                    "selected_index": int(index),
                    "baseline_loss": float(baseline_loss),
                    "tail_loss": float(loss),
                    "loss_degradation": degradation,
                    "flipped": bool(flip),
                }
            )
    out = {
        error: {
            "loss": float(np.mean(values["loss"])),
            "flip": float(np.mean(values["flip"])),
            "degradation": float(np.mean(values["degradation"])),
        }
        for error, values in aggregates.items()
    }
    worst_degradation = max(value["degradation"] for value in out.values())
    return dict(
        name="nadir_error",
        loss_by_error={str(e): round(v["loss"], 4) for e, v in out.items()},
        flip_by_error={str(e): round(v["flip"], 3) for e, v in out.items()},
        degradation_by_error={
            str(e): round(v["degradation"], 4) for e, v in out.items()
        },
        max_quality_degradation=round(worst_degradation, 4),
        records=records,
        **{"pass": worst_degradation <= 0.05},
    )


# --------------------------------------------------------------------------- #
# paired statistics
# --------------------------------------------------------------------------- #


def bootstrap_ci(diff, B=5000, seed=0):
    rng = np.random.default_rng(seed)
    n = len(diff)
    means = [diff[rng.integers(0, n, n)].mean() for _ in range(B)]
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def noninferiority(lexpr_loss, ctrl_loss, margin=0.01, margin_rel=0.02, name="ctrl"):
    """Paired non-inferiority of LexPR vs control on (tail) loss. Per the
    pre-registered protocol the margin is `0.01 normalized OR 2% relative`; we
    report both and declare non-inferiority if EITHER holds (upper 95% bootstrap
    bound of mean(LexPR-ctrl) below the margin)."""
    lexpr_loss = np.asarray(lexpr_loss)
    ctrl_loss = np.asarray(ctrl_loss)
    diff = lexpr_loss - ctrl_loss
    lo, hi = bootstrap_ci(diff)
    try:
        _, p = sps.wilcoxon(lexpr_loss, ctrl_loss)
    except ValueError:
        p = 1.0
    rel_margin = margin_rel * float(ctrl_loss.mean())
    eff_margin = max(margin, rel_margin)
    return dict(
        control=name,
        mean_diff=round(float(diff.mean()), 4),
        ci95=[round(lo, 4), round(hi, 4)],
        wilcoxon_p=float(p),
        delta=round(stats.cliffs_delta(lexpr_loss, ctrl_loss), 3),
        margin_abs=margin,
        margin_rel2pct=round(rel_margin, 4),
        noninferior_abs=bool(hi < margin),
        noninferior=bool(hi < eff_margin),
    )


def noninferiority_cluster(frame, ctrl_name, lexpr_name, ni_cfg, seed=0):
    from lexpr.analysis import cluster_bootstrap_difference

    metric = ni_cfg["metric"]
    margin = ni_cfg["margin_absolute"]
    conf = ni_cfg["confidence"]
    n_boot = ni_cfg["bootstrap_repetitions"]
    unit = ni_cfg["bootstrap_unit"]

    # In analysis, cluster_bootstrap_difference returns diffs = control - treatment.
    # We want diff = LexPR - control. So let treatment=LexPR, control=ctrl_name.
    # Then diffs = ctrl - LexPR. Wait, if we want LexPR - ctrl, we should pass control=LexPR, treatment=ctrl_name.
    # diffs = LexPR - ctrl.
    md, ci_l, ci_u, rev = cluster_bootstrap_difference(
        frame,
        control=lexpr_name,
        treatment=ctrl_name,
        cluster_columns=unit,
        seed=seed,
        n_boot=n_boot,
        alpha=1.0 - conf,
    )
    # Actually, cluster_bootstrap_difference:
    # diffs = pivot[control] - pivot[treatment]
    # So if control=lexpr_name, diffs = LexPR - ctrl.

    # Non-inferiority condition: upper confidence interval of LexPR - ctrl < margin
    noninferior = bool(ci_u < margin)

    return dict(
        control=ctrl_name,
        mean_diff=round(md, 4),
        ci=[round(ci_l, 4), round(ci_u, 4)],
        margin_abs=margin,
        noninferior_abs=noninferior,
        noninferior=noninferior,
    )


def gate_normalization_stability(
    reps=10, n_samples=20, n=250, m=8, seed=42, n_test=300
):
    from .normalization import generate_bounds, normalization_stability
    from .probe_validation import _tolerance_set

    rng = np.random.default_rng(seed)

    regimes = ["minmax", "quantiles", "subset", "asymmetric_error", "correlated_error"]

    out = {}
    for regime in regimes:
        identities, overlaps, degradations, cert_gaps = [], [], [], []

        for _ in range(reps):
            g = problems.GEOMETRIES[int(rng.integers(0, 4))]
            F = problems.make_candidate_set(g, n, m, rng)

            i_base, D_base, _, _ = methods.lexpr_variant(F, return_detail=True)
            cert_base = -np.sort(-D_base[i_base])
            set_base = _tolerance_set(D_base)

            cache = families.loss_cache(
                F, normalize, np.random.default_rng(1), n_per_family=n_test
            )
            loss_base = families.losses_from(cache, i_base)[1]

            bounds = generate_bounds(F, n_samples, regime, rng)

            # evaluate over bounds
            for ideal, nadir in bounds:
                i_b, D_b, _, _ = methods.lexpr_variant(
                    F, ideal=ideal, nadir=nadir, return_detail=True
                )
                identities.append(int(i_b == i_base))

                set_b = _tolerance_set(D_b)
                inter = set_base.intersection(set_b)
                union = set_base.union(set_b)
                overlaps.append(len(inter) / len(union) if union else 1.0)

                loss_b = families.losses_from(cache, i_b)[1]
                degradations.append(loss_b - loss_base)

                cert_b = -np.sort(-D_b[i_b])
                k = max(len(cert_base), len(cert_b))
                cb_pad = np.pad(cert_base, (0, k - len(cert_base)))
                cb_b_pad = np.pad(cert_b, (0, k - len(cert_b)))
                cert_gaps.append(float(np.max(np.abs(cb_pad - cb_b_pad))))

        out[regime] = {
            "identity_rate": round(float(np.mean(identities)), 4),
            "overlap": round(float(np.mean(overlaps)), 4),
            "quality_degradation": round(float(np.mean(degradations)), 4),
            "cert_gap": round(float(np.mean(cert_gaps)), 4),
        }

    return dict(
        name="normalization_stability", regimes=out, **{"pass": True}
    )  # Gate passing isn't explicitly defined for this step, just record outcomes
