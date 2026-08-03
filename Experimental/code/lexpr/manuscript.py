from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .claim_gate import summarize_claim


@dataclass(frozen=True)
class PublicationEvidence:
    run_id: str
    instances: int
    methods: int
    geometries: int
    families: int
    nemenyi_cd: float
    average_ranks: dict[str, float]
    noninferiority: dict
    gates: list[dict]
    claims: dict[str, str]


@dataclass
class ManuscriptCheck:
    errors: list[str] = field(default_factory=list)


def load_publication_evidence(
    repo_root: str | Path,
    claims_path: str | Path,
) -> PublicationEvidence:
    """Load manuscript evidence from the immutable, manuscript-approved run.

    Every protocol constant (instances, methods, geometries, Nemenyi CD, ranks,
    gates) is sourced from the frozen run ``figure_evidence.AUTHORITATIVE_RUN_ID``
    and the code-level family registry -- never from a mutable config file -- so
    that editing ``configs/full_config.yaml`` cannot silently change published
    numbers.
    """
    import pandas as pd

    from .families import ALL_FAMILIES
    from .figure_evidence import authoritative_run_dir, load_protocol_evidence

    repo_root = Path(repo_root)
    protocol = load_protocol_evidence(repo_root)
    run_dir = authoritative_run_dir(repo_root)
    analysis = json.loads(
        (run_dir / "tables" / "benchmark_analysis.json").read_text(encoding="utf-8")
    )
    gates = json.loads(
        (run_dir / "tables" / "gates_report.json").read_text(encoding="utf-8")
    )
    claims_cfg = yaml.safe_load(Path(claims_path).read_text())["claims"]

    run_id = protocol.run_id
    if any(row.get("run_id") != run_id for row in gates):
        raise ValueError("gate report run_id does not match authoritative run")

    geometries = int(
        pd.read_parquet(protocol.raw_path, columns=["geometry"])["geometry"].nunique()
    )

    gate_map = {
        row["gate"]: {
            "pass": row["result"] == "PASS",
            "result": row["result"],
        }
        for row in gates
    }
    claims = {
        claim_id: summarize_claim(claim, gate_map)
        for claim_id, claim in claims_cfg.items()
    }
    return PublicationEvidence(
        run_id=run_id,
        instances=protocol.n_instances,
        methods=len(protocol.method_names),
        geometries=geometries,
        families=len(ALL_FAMILIES),
        nemenyi_cd=protocol.nemenyi_cd,
        average_ranks=dict(protocol.average_ranks),
        noninferiority=analysis.get("noninferiority", {}),
        gates=gates,
        claims=claims,
    )


def check_manuscript(
    paths: list[str | Path], evidence: PublicationEvidence
) -> ManuscriptCheck:
    result = ManuscriptCheck()
    stale_patterns = []
    if evidence.instances != 2400:
        stale_patterns.append((re.compile(r"(?<!\d)2,?400(?!\d)"), "2,400"))
    if evidence.methods != 12:
        stale_patterns.append((re.compile(r"\b12\s+methods\b", re.I), "12 methods"))
    if evidence.geometries != 6:
        stale_patterns.append(
            (re.compile(r"\b6\s+geometr(?:y|ies)\b", re.I), "6 geometries")
        )

    for path_value in paths:
        path = Path(path_value)
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern, label in stale_patterns:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                result.errors.append(
                    f"{path}:{line}: stale protocol value {label}; "
                    f"current run {evidence.run_id[:12]} has "
                    f"{evidence.instances} instances, {evidence.methods} methods, "
                    f"and {evidence.geometries} geometries"
                )
    return result


def _latex_escape(value) -> str:
    text = str(value)
    for old, new in (
        ("\\", r"\textbackslash{}"),
        ("_", r"\_"),
        ("%", r"\%"),
        ("&", r"\&"),
        ("#", r"\#"),
    ):
        text = text.replace(old, new)
    return text


def write_generated_inputs(
    evidence: PublicationEvidence, generated_dir: str | Path
) -> None:
    generated_dir = Path(generated_dir)
    generated_dir.mkdir(parents=True, exist_ok=True)
    numbers = (
        "% Generated from validated ALexPR evidence. Do not edit.\n"
        f"\\newcommand{{\\protocolInstances}}{{{evidence.instances:,}}}\n"
        f"\\newcommand{{\\protocolMethods}}{{{evidence.methods}}}\n"
        f"\\newcommand{{\\protocolGeometries}}{{{evidence.geometries}}}\n"
        f"\\newcommand{{\\protocolFamilies}}{{{evidence.families}}}\n"
        f"\\newcommand{{\\protocolCD}}{{{evidence.nemenyi_cd:.3f}}}\n"
        f"\\newcommand{{\\protocolRunId}}{{{evidence.run_id[:12]}}}\n"
    )
    (generated_dir / "protocol_numbers.tex").write_text(numbers, encoding="utf-8")

    gate_lines = [
        r"\begin{tabular}{lll}",
        r"\toprule",
        r"Gate & Status & Evidence \\",
        r"\midrule",
    ]
    gate_lines.extend(
        f"{_latex_escape(row['gate'])} & {_latex_escape(row['result'])} & "
        f"{_latex_escape(row.get('detail', ''))} \\\\"
        for row in evidence.gates
    )
    gate_lines.extend([r"\bottomrule", r"\end{tabular}", ""])
    (generated_dir / "protocol_gates.tex").write_text(
        "\n".join(gate_lines), encoding="utf-8"
    )

    result_lines = ["% Generated from validated ALexPR evidence. Do not edit."]
    if "LexPR" in evidence.average_ranks:
        result_lines.append(
            f"\\newcommand{{\\protocolLexPRRank}}{{{evidence.average_ranks['LexPR']:.3f}}}"
        )
    (generated_dir / "protocol_results.tex").write_text(
        "\n".join(result_lines) + "\n", encoding="utf-8"
    )
