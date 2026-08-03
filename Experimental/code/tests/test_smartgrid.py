import numpy as np
import pytest
import json
import re

from lexpr import smartgrid


def test_empty_efficient_set_raises_clear_error(monkeypatch):
    monkeypatch.setattr(
        smartgrid, "_nd_mask", lambda F: np.zeros(F.shape[0], dtype=bool)
    )
    with pytest.raises(RuntimeError, match="no non-dominated candidates"):
        smartgrid.build_candidates(n_candidates=5, n_scenarios=2, seed=3)


def test_certificate_plot_keeps_every_probe_with_semantic_labels(tmp_path):
    summary = smartgrid.run_case(outdir=tmp_path)
    metadata = json.loads(
        (tmp_path / "figures/certificate.pdf.json").read_text()
    )

    assert metadata["probe_count"] == len(summary["certificate"])
    assert metadata["omitted_probe_count"] == 0
    assert metadata["candidate_index"] == summary["chosen"]["LexPR"]
    raw_code = re.compile(r"^(?:f\d+|(?:mean|max)\([^)]*f\d+)")
    assert not any(raw_code.match(label) for label in metadata["display_labels"])
