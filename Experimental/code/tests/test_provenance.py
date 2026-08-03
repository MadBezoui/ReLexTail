import json
from pathlib import Path

from lexpr.provenance import build_manifest, sha256_file, source_fingerprint
from run_protocol import configure_output_root, publish_current_run


def test_manifest_contains_reproducibility_fields(tmp_path: Path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("seed: 17\n", encoding="utf-8")
    manifest = build_manifest(str(cfg), seed=17)
    assert manifest["seed"] == 17
    assert manifest["config_sha256"] == sha256_file(cfg)
    assert manifest["python"]
    assert manifest["packages"]["numpy"]
    assert "git_commit" in manifest


def test_manifest_round_trip(tmp_path: Path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("seed: 17\n", encoding="utf-8")
    payload = build_manifest(str(cfg), seed=17)
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert json.loads(path.read_text())["config_sha256"] == payload["config_sha256"]


def test_source_fingerprint_changes_when_scientific_code_changes(tmp_path: Path):
    root = tmp_path / "repo"
    source_dir = root / "code" / "lexpr"
    source_dir.mkdir(parents=True)
    source = source_dir / "methods.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")

    first = source_fingerprint(root)
    source.write_text("VALUE = 2\n", encoding="utf-8")

    assert source_fingerprint(root) != first


def test_manifest_run_id_binds_config_and_source(tmp_path: Path):
    root = tmp_path / "repo"
    source_dir = root / "code" / "lexpr"
    source_dir.mkdir(parents=True)
    (source_dir / "methods.py").write_text("VALUE = 1\n", encoding="utf-8")
    cfg = root / "code" / "config.yaml"
    cfg.write_text("seed: 17\n", encoding="utf-8")

    manifest = build_manifest(str(cfg), 17, source_root=root)

    assert len(manifest["run_id"]) == 64
    assert manifest["source_sha256"]
    assert manifest["created_utc"].endswith("Z")


def test_protocol_output_is_isolated_by_run_id(tmp_path: Path):
    paths = configure_output_root(tmp_path, "run-a")

    assert paths["root"] == tmp_path / "runs" / "run-a"
    assert paths["tables"] == paths["root"] / "tables"
    assert paths["figures"] == paths["root"] / "figures"
    assert paths["tmp"] == paths["root"] / "tmp"


def test_only_completed_run_is_published_as_current(tmp_path: Path):
    run_root = tmp_path / "runs" / "run-a"
    run_root.mkdir(parents=True)
    (run_root / "run_manifest.json").write_text("{}", encoding="utf-8")

    current = publish_current_run(run_root)

    assert current.is_symlink()
    assert current.resolve() == run_root.resolve()
