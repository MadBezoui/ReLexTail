"""Exact rational oracle for ReLexTail at a fixed bound vector.

This module answers "who wins at this exact ``b``?" with no floating-point step
anywhere: criteria, bounds, normalised values, probe values, anchors,
disappointments, tail means and categories are all :class:`fractions.Fraction`.
It is deliberately written the slow, obvious way.  Its two jobs are

* to falsify certificates (E0): a certificate claiming ``x0`` wins throughout a
  box is refuted by any ``b`` in that box at which the oracle names someone
  else;
* to bound the decision radius from above: the smallest level at which a
  verified switch exists is an upper witness for ``rho*``.

Operational versus exact rule.  The binary64 selector in
``Experimental/code/lexpr`` adds a guard ``EPS = 1e-9`` to the disappointment
denominator and snaps near-boundary categories.  Those are operational
numerical rules, not the mathematical object certified here.  The oracle
implements the exact rule; :func:`certrelex.oracle.agrees_with_float_selector`
reports where the two differ instead of assuming they cannot.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Sequence

import numpy as np

from .profile import profile


def _as_fraction_matrix(F) -> list:
    return [[Fraction(float(v)) for v in row] for row in np.asarray(F, dtype=float)]


def _as_fraction_vector(v) -> list:
    return [Fraction(float(x)) for x in np.asarray(v, dtype=float)]


def normalise(F_q, ideal_q, nadir_q):
    """Exact ``r_i(x) = (f_i(x) - I_i) / (N_i - I_i)``; refuses a zero range."""
    m = len(ideal_q)
    dens = [nadir_q[i] - ideal_q[i] for i in range(m)]
    if any(d <= 0 for d in dens):
        raise ValueError("non-positive normalising denominator")
    return [[(row[i] - ideal_q[i]) / dens[i] for i in range(m)] for row in F_q]


def probe_values(probe, r_q) -> list:
    kind, idx = probe
    idx = list(idx)
    if kind == "single":
        i = idx[0]
        return [row[i] for row in r_q]
    if kind == "mean":
        k = Fraction(len(idx))
        return [sum((row[i] for i in idx), Fraction(0)) / k for row in r_q]
    if kind == "max":
        return [max(row[i] for i in idx) for row in r_q]
    raise ValueError(f"unknown probe kind {kind!r}")


def disappointments(F, probes, ideal, nadir, *, retention_eps=Fraction(1, 10**9)):
    """Exact retained disappointment matrix as a list of rows of Fractions.

    A probe whose active range ``q^w - q^*`` is at most ``retention_eps`` is
    dropped, matching the retention rule of the declared method.  Nothing is
    ever added to a denominator.
    """
    F_q = _as_fraction_matrix(F)
    r_q = normalise(F_q, _as_fraction_vector(ideal), _as_fraction_vector(nadir))
    cols = []
    for q in probes:
        v = probe_values(q, r_q)
        lo, hi = min(v), max(v)
        if hi - lo <= retention_eps:
            continue
        span = hi - lo
        cols.append([(x - lo) / span for x in v])
    if not cols:
        raise ValueError("no probe retained at this bound vector")
    return [list(row) for row in zip(*cols)]


def winner_class(F, probes, ideal, nadir, resolutions=None) -> list:
    """Indices attaining the lexicographic minimum profile, exactly."""
    D = disappointments(F, probes, ideal, nadir)
    profiles = [profile(row, resolutions) for row in D]
    best = min(profiles)
    return [i for i, p in enumerate(profiles) if p == best]


def winner(F, probes, ideal, nadir, resolutions=None) -> int:
    """Declared point selection: lexicographic minimum, smallest index on ties."""
    return winner_class(F, probes, ideal, nadir, resolutions)[0]


def sample_bounds(F, p: float, rng: np.random.Generator, *, corner_bias: float = 0.5):
    """Draw one admissible bound vector from ``B(p)``.

    With probability ``corner_bias`` the draw is pushed onto a face of the box.
    Switches concentrate near the boundary of the decision region, and the
    boundary of ``B(p)`` is where the largest normalisation distortions live,
    so an unbiased interior sample is a weak falsifier.
    """
    lo = F.min(axis=0)
    hi = F.max(axis=0)
    span = hi - lo
    m = F.shape[1]
    z = rng.uniform(-1.0, 1.0, size=(2, m))
    if rng.random() < corner_bias:
        z = np.sign(z)
        z[z == 0] = 1.0
    return lo + p * span * z[0], hi + p * span * z[1]


def find_switch(
    F,
    probes,
    p: float,
    nominal: int,
    *,
    resolutions=None,
    draws: int = 512,
    seed: int = 20260906,
):
    """Search ``B(p)`` for a verified bound vector at which ``nominal`` loses.

    Returns the witness ``(ideal, nadir, winner_class)`` or ``None``.  A
    ``None`` result is the absence of a witness under this budget, never
    evidence that no witness exists.
    """
    F = np.asarray(F, dtype=float)
    rng = np.random.default_rng(seed)
    for _ in range(draws):
        ideal, nadir = sample_bounds(F, p, rng)
        try:
            cls = winner_class(F, probes, ideal, nadir, resolutions)
        except ValueError:
            continue
        if nominal not in cls or len(cls) > 1:
            return {
                "ideal": ideal.tolist(),
                "nadir": nadir.tolist(),
                "winner_class": cls,
                "unique": len(cls) == 1,
            }
    return None


def witness_radius(
    F,
    probes,
    nominal: int,
    *,
    resolutions=None,
    grid: Sequence[float] = (0.005, 0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.15, 0.25, 0.40),
    draws: int = 512,
    seed: int = 20260906,
):
    """Smallest grid level carrying a verified switch: an UPPER witness for rho*.

    Returns ``(level, witness)`` or ``(None, None)`` when no witness is found.
    """
    for p in grid:
        w = find_switch(
            F, probes, p, nominal, resolutions=resolutions, draws=draws, seed=seed
        )
        if w is not None:
            return p, w
    return None, None


def agrees_with_float_selector(F, probes, ideal, nadir, resolutions=None):
    """Compare the exact rule with the binary64 operational selector.

    Returns ``(exact_winner, float_winner, agree)``.  Disagreement is a fact
    about the operational rule, reported rather than tuned away.
    """
    from lexpr.disappointments import disappointment_matrix
    from lexpr.orders.relex_tail import relex_tail_winner_class

    exact = winner(F, probes, ideal, nadir, resolutions)
    callables = [_probe_callable(q) for q in probes]
    D = disappointment_matrix(np.asarray(F, dtype=float), callables, ideal, nadir)
    res = {k: str(v) for k, v in _float_resolution(resolutions).items()}
    flt = relex_tail_winner_class(D, res)[0]
    return exact, flt, exact == flt


def _probe_callable(probe):
    kind, idx = probe
    idx = np.array(list(idx))
    if kind == "single":
        i = int(idx[0])
        return lambda r, i=i: r[:, i]
    if kind == "mean":
        return lambda r, idx=idx: r[:, idx].mean(axis=1)
    if kind == "max":
        return lambda r, idx=idx: r[:, idx].max(axis=1)
    raise ValueError(f"unknown probe kind {kind!r}")


def _float_resolution(resolutions):
    from .profile import DEFAULT_RESOLUTION

    keys = ("maximum", "tail_025", "tail_050", "tail_100")
    if resolutions is None:
        return {k: DEFAULT_RESOLUTION for k in keys}
    if isinstance(resolutions, (str, Fraction, int)):
        return {k: Fraction(str(resolutions)) for k in keys}
    return {k: Fraction(str(resolutions.get(k, DEFAULT_RESOLUTION))) for k in keys}
