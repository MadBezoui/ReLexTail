"""Track A experiments: fixed-rule certification.

Every arm certifies the *same* declared rule on the *same* inputs with the
*same* box budget and arithmetic contract.  Only the certification machinery
changes, so any difference is attributable to it and not to a different
recommendation.

Ablation ladder (each row adds exactly one component to the row above):

    A0  global gate  + independent quotient + widest split   (current engine)
    A1  decision gate + independent quotient + widest split  (+ decision focus)
    A2  decision gate + joint quotient      + widest split   (+ dependency)
    A3  decision gate + joint quotient      + decision split (+ branching)

Experiments
    E0  correctness: exact-rational replay of certified leaves, plus exact
        oracle evaluation at bound vectors drawn from inside certified regions.
        Any disagreement is a false certificate and is reported as such.
    E1  mechanism: width of the decisive pairwise comparison at the root box.
    E2  fixed-budget certification: certified radius lower bound, certified
        volume and boxes/time to certificate at a matched budget.
    E7  anytime behaviour: certified volume as a function of the box budget.

Outputs are append-only CSV/JSON under ``enhanced/results/``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from certrelex import __version__, oracle, verify  # noqa: E402
from certrelex.benchmark import iter_instances  # noqa: E402
from certrelex.certify import certified_radius, certify_winner  # noqa: E402
from certrelex.enclosure import box_from_level, canonical_probes, d_enclosure  # noqa: E402
from certrelex.profile import coordinate_name, first_difference, profile  # noqa: E402

RESOLUTION = "0.02"
FOCAL_LEVEL = 0.02
ANYTIME_BUDGETS = (64, 256, 1024)

ARMS = {
    "A0_global_independent": dict(gate="global", mode="independent", split="widest"),
    "A1_decision_independent": dict(gate="decision", mode="independent", split="widest"),
    "A2_decision_joint": dict(gate="decision", mode="joint", split="widest"),
    "A3_decision_joint_relevant": dict(gate="decision", mode="joint", split="decision"),
}


# ---------------------------------------------------------------- E1 mechanism
def decisive_width(F, probes, box, winner, resolutions, mode):
    """Width of the decisive comparison at the root box, per enclosure mode.

    Returns the gap ``Psi(D_lo(y*)) - Psi(D_hi(x0))`` on the first coordinate
    at which the *nominal* profiles differ, expressed as the enclosure width of
    that coordinate.  A negative value means the enclosures overlap on the
    coordinate that decides the comparison, which is exactly when the box
    cannot be resolved without branching.
    """
    enc = d_enclosure(F, probes, box, mode=mode)
    if enc is None:
        return {"refused": True}
    D_lo, D_hi = enc
    nominal = oracle.disappointments(F, probes, F.min(axis=0), F.max(axis=0))
    profs = [profile(row, resolutions) for row in nominal]
    rival = min(
        (y for y in range(len(profs)) if y != winner), key=lambda y: profs[y]
    )
    diff = first_difference(profs[winner], profs[rival])
    if diff is None:
        return {"refused": False, "tied_nominal": True}
    coord = diff[0]
    from certrelex.enclosure import to_rational

    psi_hi_win = profile(to_rational(D_hi)[winner], resolutions)
    psi_lo_riv = profile(to_rational(D_lo)[rival], resolutions)
    psi_lo_win = profile(to_rational(D_lo)[winner], resolutions)
    psi_hi_riv = profile(to_rational(D_hi)[rival], resolutions)
    return {
        "refused": False,
        "tied_nominal": False,
        "rival": int(rival),
        "decisive_coordinate": coordinate_name(coord),
        "winner_enclosure_width": float(psi_hi_win[coord] - psi_lo_win[coord]),
        "rival_enclosure_width": float(psi_hi_riv[coord] - psi_lo_riv[coord]),
        "certified_at_root": bool(psi_hi_win < psi_lo_riv),
        "max_D_width": float(np.max(D_hi - D_lo)),
        "mean_D_width": float(np.mean(D_hi - D_lo)),
    }


# ------------------------------------------------------------- E0 correctness
def falsify(F, probes, cert, winner, resolutions, draws, seed):
    """Try to refute a certificate from inside its own certified leaves."""
    if not cert.certified_leaves:
        return {"checked": 0, "violations": 0, "replay_failures": 0}
    rng = np.random.default_rng(seed)
    violations = []
    checked = 0
    for _ in range(draws):
        leaf = cert.certified_leaves[rng.integers(len(cert.certified_leaves))]
        u = rng.random(len(leaf["ideal_lo"]))
        v = rng.random(len(leaf["nadir_lo"]))
        ideal = np.array(leaf["ideal_lo"]) + u * (
            np.array(leaf["ideal_hi"]) - np.array(leaf["ideal_lo"])
        )
        nadir = np.array(leaf["nadir_lo"]) + v * (
            np.array(leaf["nadir_hi"]) - np.array(leaf["nadir_lo"])
        )
        try:
            cls = oracle.winner_class(F, probes, ideal, nadir, resolutions)
        except ValueError:
            continue
        checked += 1
        if cls != [winner]:
            violations.append(
                {"ideal": ideal.tolist(), "nadir": nadir.tolist(), "winner_class": cls}
            )
    rep = verify.replay(F, probes, cert.certified_leaves, winner, resolutions)
    return {
        "checked": checked,
        "violations": len(violations),
        "violation_witnesses": violations[:3],
        "replay_leaves": rep["n_leaves"],
        "replay_failures": rep["n_failures"],
        "replay_failure_detail": rep["failures"][:3],
    }


# --------------------------------------------------------------------- driver
def run(args) -> int:
    out_dir = ROOT / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows, mech, checks, anytime = [], [], [], []
    started = time.time()

    instances = list(
        iter_instances(splits=None if args.splits == "all" else tuple(args.splits.split(",")))
    )
    if args.limit:
        instances = instances[: args.limit]

    for k, (iid, family, m, rep, split, F_full) in enumerate(instances, 1):
        F = np.asarray(F_full[: args.shortlist], dtype=float)
        probes = canonical_probes(m)
        try:
            cls = oracle.winner_class(F, probes, F.min(axis=0), F.max(axis=0), RESOLUTION)
        except ValueError as exc:
            print(f"[{k}/{len(instances)}] {iid}: skipped ({exc})", flush=True)
            continue
        if len(cls) > 1:
            # a tied nominal optimum needs a set-preservation contract, which
            # this engine does not claim; recorded, not silently resolved
            print(f"[{k}/{len(instances)}] {iid}: tied nominal optimum {cls}", flush=True)
            continue
        winner = cls[0]
        root = box_from_level(F, FOCAL_LEVEL)

        for mode in ("independent", "joint"):
            mech.append(
                dict(
                    instance=iid, family=family, m=m, data_split=split, mode=mode,
                    **decisive_width(F, probes, root, winner, RESOLUTION, mode),
                )
            )

        for arm, cfg in ARMS.items():
            t0 = time.perf_counter()
            cert = certify_winner(
                F, probes, root, winner, resolutions=RESOLUTION,
                max_boxes=args.budget, time_limit=args.time_limit,
                record_leaves=args.leaves, **cfg,
            )
            focal_seconds = time.perf_counter() - t0
            rho = certified_radius(
                F, probes, winner, resolutions=RESOLUTION,
                max_boxes=args.budget, tol=1e-3, p_hi=0.40, **cfg,
            )
            rows.append(
                dict(
                    instance=iid, family=family, m=m, replicate=rep, data_split=split,
                    arm=arm, **cfg, nominal_winner=winner,
                    focal_level=FOCAL_LEVEL,
                    focal_certified=bool(cert.certified),
                    focal_certified_volume=cert.certified_volume,
                    focal_boxes=cert.n_boxes,
                    focal_seconds=focal_seconds,
                    focal_budget_exhausted=bool(cert.budget_exhausted),
                    rho_lower=rho,
                    box_budget=args.budget,
                )
            )
            if arm == "A3_decision_joint_relevant" and args.leaves:
                checks.append(
                    dict(instance=iid, family=family, data_split=split,
                         **falsify(F, probes, cert, winner, RESOLUTION,
                                   args.falsify_draws, seed=_seed(iid)))
                )
            if arm in ("A0_global_independent", "A3_decision_joint_relevant"):
                for b in ANYTIME_BUDGETS:
                    c = certify_winner(
                        F, probes, root, winner, resolutions=RESOLUTION,
                        max_boxes=b, **cfg,
                    )
                    anytime.append(
                        dict(instance=iid, family=family, data_split=split, arm=arm,
                             budget=b, certified_volume=c.certified_volume,
                             certified=bool(c.certified), seconds=c.seconds)
                    )

        lvl, wit = oracle.witness_radius(
            F, probes, winner, resolutions=RESOLUTION,
            grid=(0.005, 0.01, 0.02, 0.05, 0.10, 0.20, 0.40),
            draws=args.witness_draws, seed=20260906,
        )
        for row in rows[-len(ARMS):]:
            row["witness_level"] = lvl
            row["witness_unique"] = None if wit is None else bool(wit["unique"])

        print(
            f"[{k}/{len(instances)}] {iid} ({split}) "
            + " ".join(
                f"{r['arm'].split('_')[0]}:rho={r['rho_lower']:.4f}" for r in rows[-len(ARMS):]
            )
            + f" witness<={lvl}",
            flush=True,
        )

    _write_csv(out_dir / "certification.csv", rows)
    _write_csv(out_dir / "mechanism.csv", mech)
    _write_csv(out_dir / "anytime.csv", anytime)
    (out_dir / "correctness.json").write_text(json.dumps(checks, indent=2))
    (out_dir / "run_environment.json").write_text(
        json.dumps(
            {
                "certrelex_version": __version__,
                "python": sys.version,
                "platform": platform.platform(),
                "machine": platform.machine(),
                "numpy": np.__version__,
                "resolution": RESOLUTION,
                "focal_level": FOCAL_LEVEL,
                "shortlist": args.shortlist,
                "box_budget": args.budget,
                "time_limit": args.time_limit,
                "n_instances": len(instances),
                "wall_seconds": time.time() - started,
            },
            indent=2,
        )
    )
    print(f"wrote {len(rows)} certification rows in {time.time() - started:.0f}s")
    return 0


def _seed(text: str) -> int:
    """Process-independent seed (``hash`` is randomised per interpreter)."""
    return int.from_bytes(hashlib.sha256(text.encode()).digest()[:4], "big")


def _write_csv(path: Path, rows) -> None:
    import csv

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
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--splits", default="all")
    ap.add_argument("--shortlist", type=int, default=10)
    ap.add_argument("--budget", type=int, default=300)
    ap.add_argument("--time-limit", type=float, default=20.0)
    ap.add_argument("--leaves", type=int, default=64)
    ap.add_argument("--falsify-draws", type=int, default=64)
    ap.add_argument("--witness-draws", type=int, default=192)
    ap.add_argument("--limit", type=int, default=0)
    return run(ap.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
