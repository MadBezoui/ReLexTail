from __future__ import annotations

import hashlib
import importlib.metadata
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path


PACKAGES = (
    "numpy",
    "scipy",
    "pandas",
    "scikit-learn",
    "matplotlib",
    "PyYAML",
    "PuLP",
    "statsmodels",
)
SCIENTIFIC_PATTERNS = (
    "code/lexpr/*.py",
    "code/run_protocol.py",
    "code/run_all.py",
    "code/configs/*.yaml",
    "code/pyproject.toml",
)


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_fingerprint(root: str | Path) -> str:
    root = Path(root).resolve()
    digest = hashlib.sha256()
    paths = sorted(
        {path for pattern in SCIENTIFIC_PATTERNS for path in root.glob(pattern)}
    )
    for path in paths:
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _git_commit(cwd: Path) -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=10,
    )
    return result.stdout.strip() or None


def _dirty_fingerprint(cwd: Path) -> str:
    result = subprocess.run(
        ["git", "diff", "--binary", "--", "code", ":!code/tests"],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=10,
    )
    return hashlib.sha256(result.stdout).hexdigest()


def build_manifest(
    config_path: str, seed: int, source_root: str | Path | None = None
) -> dict:
    config = Path(config_path).resolve()
    root = Path(source_root).resolve() if source_root else config.parents[2]
    config_sha256 = sha256_file(config)
    source_sha256 = source_fingerprint(root)
    dirty_sha256 = _dirty_fingerprint(root)
    identity = hashlib.sha256()
    for value in (config_sha256, source_sha256, dirty_sha256, str(int(seed))):
        identity.update(value.encode("ascii"))
        identity.update(b"\0")
    versions = {}
    for package in PACKAGES:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    return {
        "run_id": identity.hexdigest(),
        "seed": int(seed),
        "config_path": str(config),
        "config_sha256": config_sha256,
        "source_sha256": source_sha256,
        "dirty_sha256": dirty_sha256,
        "git_commit": _git_commit(root),
        "created_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": versions,
    }
