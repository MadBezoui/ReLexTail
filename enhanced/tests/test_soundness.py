"""Soundness and tightness tests for the CertReLex enclosures and engine.

These tests are adversarial by design: they try to catch a certificate that is
wrong, not to confirm that the happy path runs.
"""
from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from certrelex import oracle, verify  # noqa: E402
from certrelex.benchmark import sample_family  # noqa: E402
from certrelex.certify import certified_radius, certify_winner, certified_sets  # noqa: E402
from certrelex.enclosure import box_from_level, canonical_probes, d_enclosure  # noqa: E402
from certrelex.interval import quotient_range, quotient_range_independent  # noqa: E402
from certrelex.profile import category, profile, tail_mean  # noqa: E402

RES = "0.02"


def _instances():
    for family in ("simplex", "spherical", "correlated", "narrow", "asymmetric"):
        for m in (3, 6):
            yield family, m, sample_family(family, m, 0)[:8]


# ---------------------------------------------------------------- primitives
def test_quotient_range_encloses_brute_force():
    """The corner formula must contain every feasible value of (v-a)/(c-a)."""
    rng = np.random.default_rng(0)
    for _ in range(300):
        a_lo = rng.uniform(0.0, 0.3)
        a_hi = a_lo + rng.uniform(0.0, 0.2)
        c_lo = a_hi + rng.uniform(0.05, 0.5)
        c_hi = c_lo + rng.uniform(0.0, 0.3)
        v_lo = rng.uniform(a_lo - 0.1, c_hi)
        v_hi = v_lo + rng.uniform(0.0, 0.2)
        lo, hi = quotient_range(
            np.array([v_lo]), np.array([v_hi]), a_lo, a_hi, c_lo, c_hi
        )
        vs = np.linspace(v_lo, v_hi, 13)
        a_s = np.linspace(a_lo, a_hi, 13)
        c_s = np.linspace(c_lo, c_hi, 13)
        V, A, C = np.meshgrid(vs, a_s, c_s, indexing="ij")
        g = (V - A) / (C - A)
        assert lo[0] <= g.min() + 1e-12
        assert hi[0] >= g.max() - 1e-12


def test_joint_quotient_is_never_wider_than_independent():
    """Dependency preservation may only tighten, never loosen."""
    rng = np.random.default_rng(1)
    strictly_tighter = 0
    for _ in range(400):
        a_lo = rng.uniform(0.0, 0.3)
        a_hi = a_lo + rng.uniform(0.0, 0.2)
        c_lo = a_hi + rng.uniform(0.05, 0.5)
        c_hi = c_lo + rng.uniform(0.0, 0.3)
        v_lo = rng.uniform(a_lo, c_hi)
        v_hi = v_lo + rng.uniform(0.0, 0.2)
        v = (np.array([v_lo]), np.array([v_hi]))
        jl, jh = quotient_range(*v, a_lo, a_hi, c_lo, c_hi)
        il, ih = quotient_range_independent(*v, a_lo, a_hi, c_lo, c_hi)
        assert jl[0] >= il[0] - 1e-15
        assert jh[0] <= ih[0] + 1e-15
        if (jh[0] - jl[0]) < (ih[0] - il[0]) - 1e-12:
            strictly_tighter += 1
    assert strictly_tighter > 300, "the joint bound should usually be strictly tighter"


def test_profile_is_coordinatewise_monotone():
    """The soundness proof needs Psi to be nondecreasing in D componentwise."""
    rng = np.random.default_rng(2)
    for _ in range(200):
        K = int(rng.integers(3, 9))
        d = np.sort(rng.random(K))
        d2 = d + rng.random(K) * 0.1
        p1 = profile([Fraction(float(x)) for x in d], RES)
        p2 = profile([Fraction(float(x)) for x in d2], RES)
        assert all(a <= b for a, b in zip(p1, p2))
        assert p1 <= p2


def test_tail_mean_and_category_edge_cases():
    vals = [Fraction(1, 2), Fraction(1, 4), Fraction(1, 8)]
    assert tail_mean(vals, Fraction(1)) == sum(vals) / 3
    assert tail_mean(vals, Fraction(1, 4)) == vals[0]  # h <= 1 -> the maximum
    assert tail_mean([], Fraction(1)) == 0
    # exact cell endpoints: ceil is closed on the right, so z = k*delta stays
    # in cell k rather than opening cell k+1
    assert category(Fraction("0.02"), Fraction("0.02")) == 1
    assert category(Fraction("0.020000001"), Fraction("0.02")) == 2
    assert category(Fraction(0), Fraction("0.02")) == 0


# ------------------------------------------------------------- the enclosure
@pytest.mark.parametrize("family,m,F", list(_instances()))
def test_enclosure_contains_sampled_disappointments(family, m, F):
    """Sampled exact disappointments must lie inside the enclosure."""
    probes = canonical_probes(m)
    box = box_from_level(F, 0.05)
    enc = d_enclosure(F, probes, box, mode="joint")
    if enc is None:
        pytest.skip("box refused")
    D_lo, D_hi = enc
    rng = np.random.default_rng(3)
    for _ in range(24):
        ideal, nadir = oracle.sample_bounds(F, 0.05, rng)
        try:
            D = oracle.disappointments(F, probes, ideal, nadir)
        except ValueError:
            continue
        if len(D[0]) != D_lo.shape[1]:
            continue  # a probe dropped out by retention at this b
        for i, row in enumerate(D):
            for k, v in enumerate(row):
                assert Fraction(float(D_lo[i, k])) <= v <= Fraction(float(D_hi[i, k]))


@pytest.mark.parametrize("family,m,F", list(_instances()))
def test_joint_enclosure_is_contained_in_independent(family, m, F):
    probes = canonical_probes(m)
    box = box_from_level(F, 0.05)
    a = d_enclosure(F, probes, box, mode="joint")
    b = d_enclosure(F, probes, box, mode="independent")
    if a is None or b is None:
        pytest.skip("box refused")
    assert np.all(a[0] >= b[0] - 1e-15)
    assert np.all(a[1] <= b[1] + 1e-15)


# ------------------------------------------------------------------- engine
@pytest.mark.parametrize("family,m,F", list(_instances()))
def test_certificates_survive_exact_oracle(family, m, F):
    """No bound vector inside a certified leaf may name another winner."""
    probes = canonical_probes(m)
    w = oracle.winner(F, probes, F.min(axis=0), F.max(axis=0), RES)
    cert = certify_winner(
        F, probes, box_from_level(F, 0.02), w, resolutions=RES,
        max_boxes=400, record_leaves=32,
    )
    if not cert.certified_leaves:
        pytest.skip("nothing certified within the budget")
    rng = np.random.default_rng(4)
    for leaf in cert.certified_leaves:
        for _ in range(6):
            lo_i, hi_i = np.array(leaf["ideal_lo"]), np.array(leaf["ideal_hi"])
            lo_n, hi_n = np.array(leaf["nadir_lo"]), np.array(leaf["nadir_hi"])
            ideal = lo_i + rng.random(lo_i.size) * (hi_i - lo_i)
            nadir = lo_n + rng.random(lo_n.size) * (hi_n - lo_n)
            assert oracle.winner_class(F, probes, ideal, nadir, RES) == [w]


@pytest.mark.parametrize("family,m,F", list(_instances()))
def test_independent_replay_accepts_every_certified_leaf(family, m, F):
    probes = canonical_probes(m)
    w = oracle.winner(F, probes, F.min(axis=0), F.max(axis=0), RES)
    cert = certify_winner(
        F, probes, box_from_level(F, 0.02), w, resolutions=RES,
        max_boxes=400, record_leaves=32,
    )
    if not cert.certified_leaves:
        pytest.skip("nothing certified within the budget")
    assert verify.replay(F, probes, cert.certified_leaves, w, RES)["ok"]


@pytest.mark.parametrize("family,m,F", list(_instances()))
def test_decision_gate_dominates_global_gate(family, m, F):
    """The global gate can never certify volume the decision gate cannot."""
    probes = canonical_probes(m)
    w = oracle.winner(F, probes, F.min(axis=0), F.max(axis=0), RES)
    box = box_from_level(F, 0.02)
    kw = dict(resolutions=RES, max_boxes=400, mode="independent", split="widest")
    g = certify_winner(F, probes, box, w, gate="global", **kw)
    d = certify_winner(F, probes, box, w, gate="decision", **kw)
    assert d.certified_volume >= g.certified_volume - 1e-12


@pytest.mark.parametrize("family,m,F", list(_instances()))
def test_certified_radius_below_witness_radius(family, m, F):
    """A certified lower radius may never exceed a verified switch level."""
    probes = canonical_probes(m)
    w = oracle.winner(F, probes, F.min(axis=0), F.max(axis=0), RES)
    rho = certified_radius(F, probes, w, resolutions=RES, max_boxes=300, p_hi=0.40)
    level, wit = oracle.witness_radius(
        F, probes, w, resolutions=RES,
        grid=(0.005, 0.01, 0.02, 0.05, 0.10, 0.20, 0.40), draws=128,
    )
    if wit is None:
        pytest.skip("no witness found under this budget")
    assert rho <= level


def test_anytime_certified_volume_is_monotone_in_budget():
    F = sample_family("spherical", 3, 0)[:8]
    probes = canonical_probes(3)
    w = oracle.winner(F, probes, F.min(axis=0), F.max(axis=0), RES)
    box = box_from_level(F, 0.05)
    vols = [
        certify_winner(F, probes, box, w, resolutions=RES, max_boxes=b).certified_volume
        for b in (32, 128, 512)
    ]
    assert vols[0] <= vols[1] + 1e-12 <= vols[2] + 2e-12


def test_certified_sets_bracket_the_sampled_winners():
    F = sample_family("spherical", 3, 0)[:6]
    probes = canonical_probes(3)
    out = certified_sets(F, probes, box_from_level(F, 0.05), resolutions=RES, max_boxes=800)
    assert set(out["inner_possible"]) <= set(out["outer_possible"])
    rng = np.random.default_rng(5)
    for _ in range(64):
        ideal, nadir = oracle.sample_bounds(F, 0.05, rng)
        try:
            cls = oracle.winner_class(F, probes, ideal, nadir, RES)
        except ValueError:
            continue
        assert set(cls) <= set(out["outer_possible"])


def test_engine_does_not_change_the_declared_winner():
    """The certificate engine must not move the recommendation itself."""
    for family, m, F in _instances():
        probes = canonical_probes(m)
        nominal = oracle.winner(F, probes, F.min(axis=0), F.max(axis=0), RES)
        out = certified_sets(
            F, probes, box_from_level(F, 0.0001), resolutions=RES, max_boxes=200
        )
        if out["inner_possible"]:
            assert out["inner_possible"] == [nominal]
