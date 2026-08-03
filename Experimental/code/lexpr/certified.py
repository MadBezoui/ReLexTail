"""Certified (deterministic) stability analysis for finite LexPR.

Interval branch-and-bound over a box of admissible ideal/nadir bounds that
returns *certified* inner and outer approximations of the possible- and
necessary-winner sets, an unresolved-volume bound, and a certified stability
radius around the nominal bounds.

Soundness.  Every enclosure below is conservative:
  * r_i(x;b)=(f_i(x)-ideal_i)/(nadir_i-ideal_i) is continuous and monotone in
    ideal_i and nadir_i separately while the denominator stays positive, so its
    range over a bound sub-box is attained at the box corners (evaluated
    exactly).
  * Each canonical probe q is monotone nondecreasing in r, so the enclosure of
    q(r) follows coordinatewise from the r enclosures.
  * The disappointment D_q(x)=(q_x-q*)/(q^w-q*) is enclosed with q*,q^w replaced
    by their own min/max enclosures over all candidates (numerator and
    denominator pushed to their extreme feasible values).
  * Pairwise test: x beats y for ALL b in the sub-box if
    sort_desc(D^hi(x)) <_lex sort_desc(D^lo(y)).  This is sound because
    D(x)<=D^hi(x) and D(y)>=D^lo(y) coordinatewise imply, by monotonicity of
    order statistics and of the lexicographic order, that
    sort_desc(D(x)) <=_lex sort_desc(D^hi(x)) <_lex sort_desc(D^lo(y))
    <=_lex sort_desc(D(y)).
Hence any set reported as certified is correct; unresolved boxes are reported
explicitly and only shrink the guarantees, never violate them.
"""
from __future__ import annotations
import numpy as np

EPS = 1e-12


def canonical_supplier_probes(cluster=None):
    """Supplier probe family. Each probe maps an (n x m) r-matrix to (n,).

    By default this returns the CANONICAL CORE Q_can (K = 9): the seven
    singletons plus the grand mean and grand maximum.  This is the declared
    headline family for the supplier case (see HEADLINE_PROBES in
    scripts/run_supplier_case.py); the name of this function refers to the
    canonical probes, not to a cluster-augmented family.

    Passing cluster=(3, 4) additionally declares the optional overlap-diagnostic
    cluster mean and maximum over the near-collinear environmental criteria
    (GHG, Energy), giving K = 11.  That layer is inert here: both families yield
    the same nominal winner, the same certified stability radius (0.0023), the
    same certified outer possible set, and the same box count, which is why the
    canonical core is the default.
    """
    probes, labels = [], []
    m = 7
    for i in range(m):
        probes.append(("single", (i,)))
        labels.append(f"f{i+1}")
    probes.append(("mean", tuple(range(m))))
    labels.append("mean(all)")
    probes.append(("max", tuple(range(m))))
    labels.append("max(all)")
    if cluster is not None:
        probes.append(("mean", cluster))
        labels.append("mean(GHG,Energy)")
        probes.append(("max", cluster))
        labels.append("max(GHG,Energy)")
    return probes, labels


def _r_enclosure(F, ideal_lo, ideal_hi, nadir_lo, nadir_hi):
    """Return (r_lo, r_hi), each (n x m), sound over the bound box."""
    n, m = F.shape
    los, his = [], []
    for I in (ideal_lo, ideal_hi):
        for N in (nadir_lo, nadir_hi):
            den_lo, den_hi = _dn(N - I), _up(N - I)
            if np.any(den_lo <= 0.0):
                # the box straddles a vanishing range on some criterion; the
                # caller falls back to the trivial enclosure
                raise ValueError("non-positive normalising denominator")
            num_lo, num_hi = _dn(F - I), _up(F - I)
            lo, hi = _idiv_pos(num_lo, num_hi, den_lo, den_hi)
            _check_finite(lo, hi)
            los.append(lo)
            his.append(hi)
    return np.stack(los, axis=0).min(axis=0), np.stack(his, axis=0).max(axis=0)


def _probe_enclosure(probe, r_lo, r_hi):
    kind, idx = probe
    idx = list(idx)
    if kind == "single":
        i = idx[0]
        return r_lo[:, i].copy(), r_hi[:, i].copy()
    if kind == "mean":
        return _imean(r_lo[:, idx], r_hi[:, idx], axis=1)
    if kind == "max":
        # max of interval endpoints is exact: it selects an existing value
        return r_lo[:, idx].max(axis=1), r_hi[:, idx].max(axis=1)
    raise ValueError(kind)


def _singleton_disappointment(F, i):
    """Exact, bound-invariant disappointment of a singleton probe q_i(r)=r_i.
    The ideal/nadir cancel in D_i(x)=(f_i-min f_i)/(max f_i-min f_i)."""
    col = F[:, i]
    lo, hi = col.min(), col.max()
    return (col - lo) / (hi - lo + EPS)


# --- validated interval arithmetic -----------------------------------------
# Every elementary operation below is evaluated in binary64 round-to-nearest and
# then pushed outward to the next representable value with np.nextafter. Since
# round-to-nearest commits an error strictly smaller than one ulp, one nextafter
# step per operation dominates that error, and the property is maintained
# inductively along the whole evaluation. This replaces the earlier scheme, which
# widened only the final result by a fixed number of ulps; that argument does not
# survive cancellation, is not valid across magnitude ranges, and does not cover
# the minima and maxima taken over candidates.
_INF = np.inf


def _dn(x):
    """Next representable value below x (downward directed rounding)."""
    return np.nextafter(x, -_INF)


def _up(x):
    """Next representable value above x (upward directed rounding)."""
    return np.nextafter(x, _INF)


def _isub(alo, ahi, blo, bhi):
    """Interval subtraction [alo,ahi] - [blo,bhi], outward rounded."""
    return _dn(alo - bhi), _up(ahi - blo)


def _idiv_pos(alo, ahi, blo, bhi):
    """Interval division by a denominator interval that excludes zero.

    Requires blo > 0, which the caller guarantees through the positivity test;
    division is refused rather than approximated when it does not hold."""
    if np.any(np.asarray(blo) <= 0.0):
        raise ValueError("interval division requires a strictly positive denominator")
    cands_lo = np.minimum(_dn(alo / bhi), _dn(alo / blo))
    cands_hi = np.maximum(_up(ahi / blo), _up(ahi / bhi))
    return cands_lo, cands_hi


def _imean(vlo, vhi, axis):
    """Interval mean along `axis`, outward rounded at every elementary operation.

    The accumulation is an explicit loop in ascending criterion index, with an
    outward step after each addition. numpy's `sum` is deliberately NOT used
    here: it applies pairwise summation, whose association order depends on the
    array length and on the build, so it would contradict the fixed-evaluation-
    order clause of the numerical contract. The loop is over the probe's
    criteria only, so it costs at most m iterations of vectorised work per
    probe.
    """
    assert axis == 1, "accumulation order is defined for axis=1"
    k = vlo.shape[1]
    slo = vlo[:, 0].copy()
    shi = vhi[:, 0].copy()
    for j in range(1, k):
        slo = _dn(slo + vlo[:, j])
        shi = _up(shi + vhi[:, j])
    return _dn(slo / k), _up(shi / k)


def _check_finite(*arrays):
    """Refuse to certify past an overflow or a NaN.

    Subnormal intermediates are deliberately NOT rejected. The soundness
    argument here does not use the relative error model (1 + delta), which is
    what fails in the subnormal range; it uses only the fact that
    round-to-nearest lands within half the local spacing of the exact value,
    and that np.nextafter steps by exactly one local spacing. Both hold for
    subnormals, where the spacing is the constant 2^-1074. Gradual underflow is
    therefore safe. Flush-to-zero would not be, but IEEE-754 binary64 as used
    by numpy does not flush. Overflow to infinity is a genuine failure of the
    enclosure and is raised."""
    for a in arrays:
        if not np.isfinite(np.asarray(a)).all():
            raise FloatingPointError("non-finite intermediate in interval evaluation")


def _D_enclosure(F, probes, box):
    """Return (D_lo, D_hi), each (n x K), sound over the bound box.

    Singleton disappointments are bound-invariant and enclosed exactly (their
    lower and upper bounds coincide); only aggregate probes carry width."""
    ideal_lo, ideal_hi, nadir_lo, nadir_hi = box
    n = F.shape[0]
    try:
        r_lo, r_hi = _r_enclosure(F, ideal_lo, ideal_hi, nadir_lo, nadir_hi)
    except (ValueError, FloatingPointError):
        # Some criterion range collapses somewhere in this box, or an
        # intermediate overflowed. Nothing can be certified here, so return the
        # trivial enclosure and let the caller subdivide. Refusing is sound;
        # continuing with a nan or an inf would not be.
        singles = {q[1][0] for q in probes if q[0] == "single"}
        Dlos, Dhis = [], []
        for q in probes:
            if q[0] == "single":
                d = _singleton_disappointment(F, q[1][0])
                Dlos.append(d)
                Dhis.append(d)
            else:
                Dlos.append(np.zeros(n))
                Dhis.append(np.ones(n))
        return np.column_stack(Dlos), np.column_stack(Dhis)
    Dlos, Dhis = [], []
    for q in probes:
        kind = q[0]
        if kind == "single":
            d = _singleton_disappointment(F, q[1][0])
            Dlos.append(d)
            Dhis.append(d)
            continue
        vlo, vhi = _probe_enclosure(q, r_lo, r_hi)
        qstar_lo, qstar_hi = vlo.min(), vhi.min()  # q* enclosure
        qw_lo, qw_hi = vlo.max(), vhi.max()  # q^w enclosure
        # denominator interval, outward rounded; certification is refused
        # unless it is bounded away from zero
        den_min, den_max = _isub(qw_lo, qw_hi, qstar_lo, qstar_hi)
        if np.any(den_min <= EPS):
            Dlos.append(np.zeros(n))
            Dhis.append(np.ones(n))
            continue
        num_lo, num_hi = _isub(vlo, vhi, qstar_lo, qstar_hi)
        Dlo, Dhi = _idiv_pos(num_lo, num_hi, den_min, den_max)
        _check_finite(Dlo, Dhi)
        # clipping to the theoretical range is applied to an already rigorous
        # enclosure, and selects existing values, so it introduces no error
        Dhi = np.clip(Dhi, 0.0, 1.0)
        Dlo = np.clip(Dlo, 0.0, 1.0)
        Dlos.append(Dlo)
        Dhis.append(Dhi)
    return np.column_stack(Dlos), np.column_stack(Dhis)


def _lex_less(a, b):
    """True if a <_lex b (strict) for 1-D arrays (already sorted descending)."""
    d = np.where(a != b)[0]
    return d.size > 0 and a[d[0]] < b[d[0]]


from lexpr.orders.relex_tail import compute_profile, compare_profiles


def _beats_always(Dhi_x, Dlo_y, method="lexpr", resolutions=None):
    """Sound: x beats y for all b in box if sort_desc(Dhi_x) <_lex sort_desc(Dlo_y)."""
    if method == "lexpr":
        return _lex_less(-np.sort(-Dhi_x), -np.sort(-Dlo_y))
    elif method == "relextail":
        Psi_hi_x = compute_profile(Dhi_x, resolutions)
        Psi_lo_y = compute_profile(Dlo_y, resolutions)
        return compare_profiles(Psi_hi_x, Psi_lo_y) < 0
    raise ValueError(f"Unknown method {method}")


def _classify_box(F, probes, box, method="lexpr", resolutions=None):
    """Return (sole_winner or None, not_eliminated_set)."""
    Dlo, Dhi = _D_enclosure(F, probes, box)
    n = F.shape[0]
    not_elim = set(range(n))
    for y in range(n):
        # y eliminated if some x beats y always
        for x in range(n):
            if x != y and _beats_always(Dhi[x], Dlo[y], method, resolutions):
                not_elim.discard(y)
                break
    sole = None
    if len(not_elim) == 1:
        cand = next(iter(not_elim))
        # verify cand beats every rival always
        if all(
            _beats_always(Dhi[cand], Dlo[y], method, resolutions)
            for y in range(n)
            if y != cand
        ):
            sole = cand
    return sole, not_elim


def _box_from_p(F, p):
    ideal0, nadir0 = F.min(axis=0), F.max(axis=0)
    return (ideal0 * (1 - p), ideal0 * 1.0, nadir0 * (1 - p), nadir0 * (1 + p))


def _split(box):
    ideal_lo, ideal_hi, nadir_lo, nadir_hi = box
    widths = np.concatenate([ideal_hi - ideal_lo, nadir_hi - nadir_lo])
    k = int(np.argmax(widths))
    m = ideal_lo.size
    b1 = [a.copy() for a in box]
    b2 = [a.copy() for a in box]
    if k < m:  # split an ideal coordinate
        mid = 0.5 * (ideal_lo[k] + ideal_hi[k])
        b1[1][k] = mid
        b2[0][k] = mid
    else:
        j = k - m
        mid = 0.5 * (nadir_lo[j] + nadir_hi[j])
        b1[3][j] = mid
        b2[2][j] = mid
    return tuple(b1), tuple(b2)


def _box_volume(box, vol0):
    ideal_lo, ideal_hi, nadir_lo, nadir_hi = box
    w = np.concatenate([ideal_hi - ideal_lo, nadir_hi - nadir_lo])
    w = w[w > 0]
    return float(np.prod(w)) if w.size else 0.0


def certified_sets(
    F, probes, p, method="lexpr", resolutions=None, max_boxes=40000, max_depth=60
):
    """Branch-and-bound certified possible/necessary winners over box(p).

    Terminal-leaf aggregation.  The outer possible set is the union of the
    surviving-candidate sets of TERMINAL leaves only: resolved boxes,
    depth-capped boxes, and budget-exhausted boxes (which contribute the sound
    survivor set inherited from their parent).  Provisional survivor sets of
    subdivided parent boxes are replaced by their children's, so the outer
    approximation tightens (weakly) under refinement.  Elimination is monotone
    under subdivision (a rival that certifiably beats x throughout a box does so
    throughout every sub-box), so a parent's survivor set is a sound superset
    for its children and the inherited set is a valid survivor set for
    unprocessed boxes.
    """
    root = _box_from_p(F, p)
    total_vol = _box_volume(root, None)
    n_cand = F.shape[0]
    inner_pos, outer_pos = set(), set()
    winners_resolved = []  # winners of resolved boxes
    unresolved_vol = 0.0
    stack = [(root, 0, frozenset(range(n_cand)))]
    nboxes = 0
    while stack and nboxes < max_boxes:
        box, depth, inherited = stack.pop()
        nboxes += 1
        sole, not_elim = _classify_box(F, probes, box, method, resolutions)
        survivors = frozenset(not_elim) & inherited
        if sole is not None:
            # resolved terminal leaf
            inner_pos.add(sole)
            outer_pos |= survivors
            winners_resolved.append((sole, _box_volume(box, total_vol)))
        elif depth < max_depth:
            # nonterminal: children replace the parent's contribution
            b1, b2 = _split(box)
            stack.append((b1, depth + 1, survivors))
            stack.append((b2, depth + 1, survivors))
        else:
            # depth-capped unresolved terminal leaf
            outer_pos |= survivors
            unresolved_vol += _box_volume(box, total_vol)
    # leftover on stack (budget exhausted): unresolved terminal leaves that
    # contribute their inherited sound survivor sets
    for box, _, inherited in stack:
        outer_pos |= inherited
        unresolved_vol += _box_volume(box, total_vol)
    resolved_vol = sum(v for _, v in winners_resolved)
    # certified necessary (inner): a candidate that wins on every resolved box
    # AND unresolved volume is zero
    nec_inner = set()
    if unresolved_vol <= 1e-15 and winners_resolved:
        wset = {w for w, _ in winners_resolved}
        if len(wset) == 1:
            nec_inner = wset
    return {
        "p": p,
        "n_boxes": nboxes + len(stack),
        "inner_possible": sorted(inner_pos),
        "outer_possible": sorted(outer_pos),
        "necessary_inner": sorted(nec_inner),
        "unresolved_vol_frac": unresolved_vol / total_vol if total_vol > 0 else 0.0,
    }


def certified_stability_radius(
    F,
    probes,
    nominal_winner,
    p_hi=0.6,
    method="lexpr",
    resolutions=None,
    tol=1e-3,
    max_boxes=40000,
):
    """Largest certified p such that `nominal_winner` is the sole winner over the
    whole box(p).  Returns a certified LOWER bound on the true radius."""

    def certified_unique(p):
        root = _box_from_p(F, p)
        stack = [(root, 0)]
        nb = 0
        while stack and nb < max_boxes:
            box, depth = stack.pop()
            nb += 1
            Dlo, Dhi = _D_enclosure(F, probes, box)
            # nominal winner must beat every rival over this box
            if all(
                _beats_always(Dhi[nominal_winner], Dlo[y], method, resolutions)
                for y in range(F.shape[0])
                if y != nominal_winner
            ):
                continue  # box certified for winner
            if depth < 60:
                b1, b2 = _split(box)
                stack.append((b1, depth + 1))
                stack.append((b2, depth + 1))
            else:
                return False  # a leaf could not be certified
        return len(stack) == 0  # all boxes certified

    # p=0 is a point and must certify
    lo, hi = 0.0, p_hi
    if not certified_unique(lo + tol):
        return 0.0
    if certified_unique(hi):
        return hi
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        if certified_unique(mid):
            lo = mid
        else:
            hi = mid
    return lo
