"""The numerical contract: which object is actually being certified.

The manuscript distinguishes four numerical quantities -- resolution, bound
level, retention guard and machine tolerance -- and the plan requires that the
operational binary64 rule and the exact rational rule be treated as two
different mathematical objects rather than assumed identical.  These tests
measure the gap instead of asserting it away.
"""
from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "Experimental" / "code"))

from certrelex import oracle  # noqa: E402
from certrelex.benchmark import sample_family  # noqa: E402
from certrelex.enclosure import canonical_probes  # noqa: E402
from certrelex.profile import profile  # noqa: E402

RES = "0.02"


def test_exact_profile_matches_float_profile_on_representable_input():
    """The reference semantics and the shipped selector must agree on Psi."""
    from lexpr.orders.relex_tail import compute_profile

    rng = np.random.default_rng(11)
    for _ in range(200):
        K = int(rng.integers(3, 12))
        # dyadic values are exactly representable, so any disagreement here is
        # a semantic difference and not a rounding artefact
        d = rng.integers(0, 257, size=K) / 256.0
        exact = profile([Fraction(float(v)) for v in d], RES)
        flt = compute_profile(np.asarray(d, dtype=float), {k: RES for k in
                              ("maximum", "tail_025", "tail_050", "tail_100")})
        assert exact[:4] == flt[:4], "categorical coordinates disagree"
        for a, b in zip(exact[4:8], flt[4:8]):
            assert abs(float(a) - b) < 1e-12


@pytest.mark.parametrize("family", ["simplex", "spherical", "correlated", "asymmetric"])
def test_exact_and_operational_selectors_agree_on_the_benchmark(family):
    """Report, rather than assume, agreement of the two selection routes.

    The operational route adds ``EPS = 1e-9`` to the disappointment denominator;
    the exact route does not.  On non-degenerate instances the two must pick the
    same candidate, and any instance where they do not is a fact about the
    operational rule that belongs in the record.
    """
    disagreements = []
    for m in (3, 6):
        for rep in range(4):
            F = sample_family(family, m, rep)[:10]
            probes = canonical_probes(m)
            exact, flt, agree = oracle.agrees_with_float_selector(
                F, probes, F.min(axis=0), F.max(axis=0), RES
            )
            if not agree:
                disagreements.append((family, m, rep, exact, flt))
    assert not disagreements, f"selector disagreement: {disagreements}"


def test_retention_guard_is_never_added_to_a_denominator():
    """A collapsed probe must be dropped, not rescued by an epsilon."""
    F = np.array([[1.0, 1.0], [1.0, 2.0], [1.0, 3.0]])
    probes = [("single", (0,)), ("single", (1,))]
    D = oracle.disappointments(F, probes, F.min(axis=0), np.array([2.0, 4.0]))
    assert len(D[0]) == 1, "the constant criterion must drop out entirely"


def test_all_probes_degenerate_is_refused_not_defaulted():
    F = np.array([[1.0, 1.0], [1.0, 1.0]])
    with pytest.raises(ValueError):
        oracle.disappointments(F, [("single", (0,))], np.array([0.0, 0.0]),
                               np.array([2.0, 2.0]))


def test_zero_range_bounds_are_refused():
    F = np.array([[0.0, 0.0], [1.0, 1.0]])
    with pytest.raises(ValueError):
        oracle.normalise(
            [[Fraction(0), Fraction(0)], [Fraction(1), Fraction(1)]],
            [Fraction(0), Fraction(0)],
            [Fraction(0), Fraction(1)],
        )


def test_exactly_representable_cell_endpoint_is_not_snapped():
    """A value sitting exactly on a cell endpoint keeps the lower cell.

    The operational engine snaps by eight machine epsilons for finite replay.
    The certified path must not: ``ceil`` at an exact endpoint is a decision of
    the declared rule, not a numerical accident to be smoothed over.
    """
    row = [Fraction("0.02")] + [Fraction(0)] * 3
    assert profile(row, RES)[0] == 1
    row2 = [Fraction("0.02") + Fraction(1, 10**18)] + [Fraction(0)] * 3
    assert profile(row2, RES)[0] == 2
