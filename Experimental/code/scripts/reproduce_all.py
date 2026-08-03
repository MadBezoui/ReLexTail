#!/usr/bin/env python3
"""One documented command that regenerates every number in the manuscript.

    python scripts/reproduce_all.py            # everything, ~35 min
    python scripts/reproduce_all.py --quick    # smoke test, ~3 min
    python scripts/reproduce_all.py --list     # show the stages and stop

The manuscript states that a single command reproduces its outputs.  This is
that command.  Each stage is one of the study scripts, run in dependency order:
the multi-seed and symmetrised batteries must exist before the hierarchical
bootstrap can resample them, and the supplier case must exist before the
certified analysis of it.

Every stage is seeded and idempotent, so rerunning reproduces the archived
output.  A stage that fails stops the run with a non-zero exit status and names
the script, rather than leaving a half-regenerated set of artefacts behind.

ENVIRONMENT.  The archived artefacts in this repository were produced under the
versions pinned in requirements.txt.  Running under different NumPy or SciPy
versions may change low-order digits; the CI workflow diffs the regenerated
JSON against the archived copies and will say so.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# (script, approximate full runtime, runs in --quick)
STAGES = [
    ("run_real_experiments.py",        "~1 min",   True),
    ("run_supplier_case.py",           "~1 min",   True),
    ("run_certified_stability.py",     "~2 min",   True),
    ("run_witness_bounds.py",          "~10 s",    True),
    ("run_certified_bench.py",         "~3 min",   False),
    ("run_certified_truth.py",         "~5 min",   False),
    ("run_multiseed.py",               "~12 min",  False),
    ("run_symmetrised.py",             "~8 min",   False),
    ("run_hierarchical_bootstrap.py",  "~1 min",   False),
    ("run_difficulty.py",              "~1 min",   False),
    ("run_continuous_study.py",        "~2 min",   False),
    ("make_paper_figures_v2.py",       "~30 s",    True),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quick", action="store_true",
                    help="run only the fast stages, for a smoke test")
    ap.add_argument("--list", action="store_true", help="list the stages and exit")
    ap.add_argument("--from", dest="start", metavar="SCRIPT",
                    help="resume at this stage")
    args = ap.parse_args()

    stages = [s for s in STAGES if s[2] or not args.quick]
    if args.start:
        names = [s[0] for s in stages]
        if args.start not in names:
            print(f"unknown stage {args.start!r}; use --list", file=sys.stderr)
            return 2
        stages = stages[names.index(args.start):]

    if args.list:
        for name, cost, quick in STAGES:
            print(f"  {name:34s} {cost:9s} {'quick' if quick else ''}")
        return 0

    t0 = time.time()
    for i, (name, cost, _) in enumerate(stages, 1):
        path = os.path.join(HERE, name)
        if not os.path.exists(path):
            print(f"FAIL  stage {i}/{len(stages)}: {name} not found")
            return 1
        print(f"\n=== [{i}/{len(stages)}] {name}  ({cost}) ===", flush=True)
        cmd = [sys.executable, "-u", path]
        if args.quick and name == "run_certified_truth.py":
            cmd.append("--quick")
        rc = subprocess.call(cmd, cwd=ROOT)
        if rc != 0:
            print(f"\nFAIL  {name} exited with status {rc}; stopping.")
            return rc

    print(f"\nok    all {len(stages)} stages completed in "
          f"{(time.time() - t0) / 60:.1f} min")
    print("      JSON outputs: code/scripts/real_results/")
    print("      LaTeX tables: manuscript/generated/")
    print("      Rebuild the PDFs with:  cd manuscript && make submission")
    return 0


if __name__ == "__main__":
    sys.exit(main())
