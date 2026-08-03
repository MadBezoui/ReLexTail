#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lexpr.manuscript import (  # noqa: E402
    check_manuscript,
    load_publication_evidence,
    write_generated_inputs,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate manuscript evidence inputs and reject stale claims"
    )
    parser.add_argument("--paper", required=True, type=Path)
    parser.add_argument(
        "--project-root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    parser.add_argument(
        "--results",
        type=Path,
        default=None,
        help="output directory for claim_status.json "
        "(default: <project-root>/results/protocol)",
    )
    parser.add_argument(
        "--claims",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "configs" / "claims.yaml",
    )
    args = parser.parse_args()

    # Evidence is pinned to the immutable authoritative run, never a mutable config.
    evidence = load_publication_evidence(args.project_root, args.claims)
    write_generated_inputs(evidence, args.paper / "generated")
    paths = sorted(args.paper.rglob("*.tex"))
    paths.extend(
        path
        for path in (
            args.project_root / "README.md",
            args.project_root / "PROTOCOL_COMPLIANCE.md",
            args.project_root / "COVER_LETTER.md",
        )
        if path.exists()
    )
    result = check_manuscript(paths, evidence)
    results_out = args.results or (args.project_root / "results" / "protocol")
    results_out.mkdir(parents=True, exist_ok=True)
    (results_out / "claim_status.json").write_text(
        json.dumps(evidence.claims, indent=2) + "\n", encoding="utf-8"
    )
    if result.errors:
        print("\n".join(result.errors), file=sys.stderr)
        return 1
    print(
        f"Manuscript evidence is consistent with run {evidence.run_id[:12]} "
        f"({evidence.instances:,} instances, {evidence.methods} methods)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
