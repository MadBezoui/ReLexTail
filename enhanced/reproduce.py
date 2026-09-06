"""One command that rebuilds every enhanced result from source.

    python enhanced/reproduce.py [--quick]

Stages, in order, each refusing to continue if the one before it failed:

  1. tests        soundness, numerical contract and frozen examples
  2. examples     recompute the three rational examples into results/
  3. experiments  Track A certification run over the locked benchmark
  4. report       tables, figures and the statistical contrasts
  5. macros       the LaTeX macro file the manuscript reads
  6. manifest     SHA-256 of every input and output

``--quick`` runs a reduced benchmark for smoke-testing the pipeline.  A quick
run writes to the same paths, so its numbers must never be used in the
manuscript; the environment file records the budget and instance count so a
reduced run is visible in the record rather than silent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


def env():
    e = dict(os.environ)
    e["PYTHONPATH"] = os.pathsep.join(
        [str(ROOT / "src"), str(REPO / "Experimental" / "code"), e.get("PYTHONPATH", "")]
    )
    return e


def run(label, cmd) -> None:
    print(f"\n=== {label} ===\n$ {' '.join(cmd)}", flush=True)
    r = subprocess.run(cmd, cwd=ROOT, env=env())
    if r.returncode != 0:
        raise SystemExit(f"stage failed: {label} (exit {r.returncode})")


def write_manifest() -> int:
    entries = {}
    for pattern in ("src/**/*.py", "analysis/*.py", "tests/*.py", "protocol/*",
                    "literature/*", "results/*", "analysis/tables/*",
                    "analysis/figures/*", "configs/*", "reproduce.py"):
        for p in sorted(ROOT.glob(pattern)):
            if p.is_file():
                entries[str(p.relative_to(ROOT))] = hashlib.sha256(
                    p.read_bytes()
                ).hexdigest()
    (ROOT / "MANIFEST.sha256").write_text(
        "\n".join(f"{h}  {n}" for n, h in sorted(entries.items())) + "\n"
    )
    return len(entries)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quick", action="store_true",
                    help="reduced benchmark; NOT for manuscript numbers")
    ap.add_argument("--skip-tests", action="store_true")
    args = ap.parse_args()
    py = sys.executable

    if not args.skip_tests:
        run("tests", [py, "-m", "pytest", "tests", "-q"])

    run("examples", [py, "-c",
                     "import json,pathlib;from certrelex import examples as e;"
                     "pathlib.Path('results').mkdir(exist_ok=True);"
                     "pathlib.Path('results/examples.json').write_text(json.dumps("
                     "{'boundary':e.check_boundary(),'slack':e.check_slack(),"
                     "'switch':e.check_switch()},indent=2))"])

    exp = [py, "analysis/run_experiments.py"]
    exp += (["--limit", "12", "--budget", "100", "--witness-draws", "32"]
            if args.quick else ["--budget", "300", "--witness-draws", "192"])
    run("experiments", exp)
    run("report", [py, "analysis/make_report.py"])
    run("macros", [py, "analysis/make_macros.py"])

    n = write_manifest()
    print(f"\n=== manifest ===\n{n} files hashed into MANIFEST.sha256")
    print("\nNext: rebuild the manuscript with\n"
          "  cd Manuscrit && latexmk -pdf main.tex")
    if args.quick:
        print("\nWARNING: --quick was used. These numbers are a smoke test, "
              "not manuscript results.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
