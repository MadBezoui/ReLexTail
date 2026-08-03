"""Front-free continuous LexPR: the full sequential scheme of Theorem 9.

This implements Algorithm S2 of the online supplement in its entirety, i.e. all
K lexicographic stages with carried optimality constraints, over a polytope
X = {x : A x <= b, 0 <= x <= 1} with affine criteria f = C x and canonical
probes (nonnegative weighted sums and maxima over criterion subsets).

`lexpr.directopt` implements only the first, minimax-regret stage and states so
in its docstring; this module supersedes it for the purposes of Theorem 9.

Formulation (supplement S2.3).  After the criterion bounds and probe anchors are
fixed, each retained disappointment is represented by an epigraph variable v_q:

  * weighted-sum probe q:  v_q >= (w_q^T r(x) - q*) / R_q     (one row, affine)
  * maximum probe q_S:     v_q >= (r_i(x) - q*) / R_q  for every i in S

Using the top-p variational identity (Proposition 7; due to Rockafellar and
Uryasev 2000 and Ogryczak and Tamir 2003), stage p solves

    T*_p = min  p t_p + sum_q s_{p,q}
           s.t. x in X,  s_{p,q} >= v_q - t_p,  s_{p,q} >= 0,
                and, for every earlier stage p' < p,
                p' t_{p'} + sum_q s_{p',q} <= T*_{p'},
                s_{p',q} >= v_q - t_{p'},  s_{p',q} >= 0,

with fresh (t_{p'}, s_{p',.}) per carried stage.  The carried rows pin the sum
of the p' largest disappointments at its optimal value, which is exactly what
makes the sequence lexicographic rather than merely hierarchical.

Solver-call accounting (matching the O(Km) claim of Theorem 9):
    2m                      criterion-bound LPs
    2 per weighted-sum probe, |S| + 1 per maximum probe   anchor LPs
    K                       stage LPs
"""
from __future__ import annotations

import time

import numpy as np
from scipy.optimize import linprog

EPS = 1e-9


class SolverCounter:
    """Counts LP solves so the O(Km) accounting can be verified empirically."""

    def __init__(self):
        self.calls = 0
        self.bound_calls = 0
        self.anchor_calls = 0
        self.stage_calls = 0

    def solve(self, c, A_ub, b_ub, bounds, kind, integrality=None):
        res = linprog(
            c,
            A_ub=A_ub,
            b_ub=b_ub,
            bounds=bounds,
            method="highs",
            integrality=integrality,
        )
        if not res.success:
            raise RuntimeError(f"LP solve failed ({kind}): {res.message}")
        self.calls += 1
        setattr(self, f"{kind}_calls", getattr(self, f"{kind}_calls") + 1)
        return res


def make_probes(m, kind="canonical"):
    """Canonical probe family as (type, weights_or_indices) pairs.

    Returns the m singletons, the grand mean, and the grand maximum, i.e. the
    canonical core Q_can with K = m + 2.
    """
    probes = []
    for i in range(m):
        w = np.zeros(m)
        w[i] = 1.0
        probes.append(("sum", w))
    probes.append(("sum", np.ones(m) / m))
    probes.append(("max", tuple(range(m))))
    return probes


def _criterion_bounds(C, A, b, bounds, ctr):
    m = C.shape[0]
    lo = np.zeros(m)
    hi = np.zeros(m)
    for i in range(m):
        lo[i] = ctr.solve(C[i], A, b, bounds, "bound").fun
        hi[i] = -ctr.solve(-C[i], A, b, bounds, "bound").fun
    return lo, hi


def _probe_rows(probes, C, f_lo, rng_obj):
    """Affine representation of each probe's r-space ingredients.

    For a weighted-sum probe, q(r(x)) = a^T x + c with a = (w/range)^T C.
    For a maximum probe, r_i(x) = a_i^T x + c_i for each i in S.
    """
    rows = []
    for kind, spec in probes:
        if kind == "sum":
            w = np.asarray(spec, dtype=float)
            a = (w / rng_obj) @ C
            c = -float((w / rng_obj) @ f_lo)
            rows.append(("sum", [(a, c)]))
        else:
            comps = []
            for i in spec:
                a = C[i] / rng_obj[i]
                c = -float(f_lo[i] / rng_obj[i])
                comps.append((a, c))
            rows.append(("max", comps))
    return rows


def _anchors(rows, A, b, bounds, ctr):
    """Anchors q* and q^w over X, by LP. Maxima use the epigraph trick for q*."""
    qstar, qworst = [], []
    for kind, comps in rows:
        if kind == "sum":
            a, c = comps[0]
            qstar.append(ctr.solve(a, A, b, bounds, "anchor").fun + c)
            qworst.append(-ctr.solve(-a, A, b, bounds, "anchor").fun + c)
        else:
            # q^w = max_i max_x r_i(x): |S| LPs
            hi = -np.inf
            for a, c in comps:
                hi = max(hi, -ctr.solve(-a, A, b, bounds, "anchor").fun + c)
            qworst.append(hi)
            # q* = min_x max_i r_i(x): one LP with an epigraph variable
            n = comps[0][0].size
            nc = A.shape[0]
            cvec = np.zeros(n + 1)
            cvec[-1] = 1.0
            Aub = np.zeros((nc + len(comps), n + 1))
            bub = np.zeros(nc + len(comps))
            Aub[:nc, :n] = A
            bub[:nc] = b
            for j, (a, c) in enumerate(comps):
                Aub[nc + j, :n] = a
                Aub[nc + j, -1] = -1.0
                bub[nc + j] = -c
            res = ctr.solve(cvec, Aub, bub, bounds + [(None, None)], "anchor")
            qstar.append(float(res.x[-1]))
    return np.asarray(qstar), np.asarray(qworst)


def continuous_lexpr(C, A, b, probes=None, tol=1e-6, return_profile=False):
    """Full sequential front-free LexPR over the polytope {Ax <= b, 0 <= x <= 1}.

    Returns (x, info) where info records the per-stage optima T*_p, the sorted
    disappointment profile at the returned point, and the LP-call breakdown.
    """
    m, n = C.shape
    probes = make_probes(m) if probes is None else probes
    bounds = [(0.0, 1.0)] * n
    ctr = SolverCounter()
    t0 = time.perf_counter()

    f_lo, f_hi = _criterion_bounds(C, A, b, bounds, ctr)
    rng_obj = np.maximum(f_hi - f_lo, EPS)
    rows = _probe_rows(probes, C, f_lo, rng_obj)
    qstar, qworst = _anchors(rows, A, b, bounds, ctr)

    # Drop degenerate probes exactly as the finite algorithm does.
    R = qworst - qstar
    keep = [k for k in range(len(rows)) if R[k] > 1e-9]
    rows = [rows[k] for k in keep]
    qstar, R = qstar[keep], R[keep]
    K = len(rows)
    if K == 0:
        raise ValueError("every probe is degenerate over X")

    # Variable layout: x (n) | v (K) | then per stage p: t_p (1), s_p (K)
    n_v = n + K

    def stage_block_offset(p_index):
        return n_v + p_index * (1 + K)

    n_stages_total = K
    n_var = n_v + n_stages_total * (1 + K)

    # Static rows: polytope, and the epigraph rows v_q >= d_q(x).
    static_A, static_b = [], []
    for j in range(A.shape[0]):
        row = np.zeros(n_var)
        row[:n] = A[j]
        static_A.append(row)
        static_b.append(b[j])
    for k, (kind, comps) in enumerate(rows):
        for a, c in comps:
            # (a^T x + c - q*) / R <= v_k   ->   (a/R)^T x - v_k <= (q* - c)/R
            row = np.zeros(n_var)
            row[:n] = a / R[k]
            row[n + k] = -1.0
            static_A.append(row)
            static_b.append((qstar[k] - c) / R[k])

    Ts = []
    x = None
    for p in range(1, K + 1):
        rowsA = [r.copy() for r in static_A]
        rowsb = list(static_b)
        # Current stage p uses block p-1; carried stages use their own blocks.
        for pp in range(1, p + 1):
            off = stage_block_offset(pp - 1)
            for k in range(K):
                # s_{pp,k} >= v_k - t_pp  ->  v_k - t_pp - s_{pp,k} <= 0
                row = np.zeros(n_var)
                row[n + k] = 1.0
                row[off] = -1.0
                row[off + 1 + k] = -1.0
                rowsA.append(row)
                rowsb.append(0.0)
            if pp < p:
                # carried optimality: pp*t_pp + sum_k s_{pp,k} <= T*_pp
                row = np.zeros(n_var)
                row[off] = float(pp)
                row[off + 1 : off + 1 + K] = 1.0
                rowsA.append(row)
                # Relative slack. The carried bound must be loose enough to stay
                # feasible under the LP solver's own optimality tolerance -- an
                # absolute epsilon becomes too tight as T* grows with p, which
                # shows up as a spurious "infeasible" at a late stage.
                rowsb.append(Ts[pp - 1] + tol * (1.0 + abs(Ts[pp - 1])))

        c_obj = np.zeros(n_var)
        off_p = stage_block_offset(p - 1)
        c_obj[off_p] = float(p)
        c_obj[off_p + 1 : off_p + 1 + K] = 1.0

        var_bounds = (
            bounds
            + [(0.0, 1.0)] * K  # v_q in [0,1]
            + [(None, None), *([(0.0, None)] * K)] * n_stages_total
        )
        res = ctr.solve(c_obj, np.array(rowsA), np.array(rowsb), var_bounds, "stage")
        Ts.append(float(res.fun))
        x = res.x[:n]

    elapsed = time.perf_counter() - t0
    d = _disappointments_at(x, rows, qstar, R)
    info = dict(
        stage_optima=Ts,
        profile_sorted=np.sort(d)[::-1],
        solver_calls=ctr.calls,
        bound_calls=ctr.bound_calls,
        anchor_calls=ctr.anchor_calls,
        stage_calls=ctr.stage_calls,
        K=K,
        m=m,
        elapsed_sec=elapsed,
    )
    return (x, info) if not return_profile else (x, info, d)


def _disappointments_at(x, rows, qstar, R):
    d = np.zeros(len(rows))
    for k, (kind, comps) in enumerate(rows):
        vals = [float(a @ x + c) for a, c in comps]
        q = max(vals) if kind == "max" else vals[0]
        d[k] = (q - qstar[k]) / R[k]
    return np.clip(d, 0.0, 1.0)


def continuous_relextail(
    C, A, b, resolutions, probes=None, tol=1e-6, return_profile=False
):
    """Full sequential MILP formulation for ReLexTail."""
    m, n = C.shape
    probes = make_probes(m) if probes is None else probes
    bounds = [(0.0, 1.0)] * n
    ctr = SolverCounter()
    t0 = time.perf_counter()

    f_lo, f_hi = _criterion_bounds(C, A, b, bounds, ctr)
    rng_obj = np.maximum(f_hi - f_lo, EPS)
    rows = _probe_rows(probes, C, f_lo, rng_obj)
    qstar, qworst = _anchors(rows, A, b, bounds, ctr)

    # Drop degenerate probes exactly as the finite algorithm does.
    R = qworst - qstar
    keep = [k for k in range(len(rows)) if R[k] > 1e-9]
    rows = [rows[k] for k in keep]
    qstar, R = qstar[keep], R[keep]
    K = len(rows)
    if K == 0:
        raise ValueError("every probe is degenerate over X")

    # ReLexTail specific setup
    alphas = [0.25, 0.50, 1.00]

    # Variable layout:
    # x (n)
    # v (K)
    # M (1)
    # z_M, z_25, z_50, z_100 (4)
    # For each alpha: t_a (1), s_a (K) -> 3 * (1 + K)
    # For each LexPR stage p (1..K): t_p (1), s_p (K) -> K * (1 + K)

    n_v = n + K
    idx_M = n_v
    idx_z = idx_M + 1
    idx_T = idx_z + 4
    idx_L = idx_T + 3 * (1 + K)
    n_var = idx_L + K * (1 + K)

    def off_T(i):
        return idx_T + i * (1 + K)

    def off_L(p_idx):
        return idx_L + p_idx * (1 + K)

    static_A, static_b = [], []
    for j in range(A.shape[0]):
        row = np.zeros(n_var)
        row[:n] = A[j]
        static_A.append(row)
        static_b.append(b[j])

    for k, (kind, comps) in enumerate(rows):
        for a, c in comps:
            row = np.zeros(n_var)
            row[:n] = a / R[k]
            row[n + k] = -1.0
            static_A.append(row)
            static_b.append((qstar[k] - c) / R[k])

        # v_k <= M  =>  v_k - M <= 0
        row = np.zeros(n_var)
        row[n + k] = 1.0
        row[idx_M] = -1.0
        static_A.append(row)
        static_b.append(0.0)

    # Resolution constraints
    # M <= delta_M * z_M  =>  M - delta_M * z_M <= 0
    row = np.zeros(n_var)
    row[idx_M] = 1.0
    row[idx_z] = -float(resolutions.get("maximum", "0.01"))
    static_A.append(row)
    static_b.append(0.0)

    for i, alpha in enumerate(alphas):
        h = alpha * K
        coeff_s = 1.0 / h

        # s_a,k >= v_k - t_a  =>  v_k - t_a - s_a,k <= 0
        base_T = off_T(i)
        for k in range(K):
            row = np.zeros(n_var)
            row[n + k] = 1.0
            row[base_T] = -1.0
            row[base_T + 1 + k] = -1.0
            static_A.append(row)
            static_b.append(0.0)

        # T_a <= delta_a * z_a  =>  t_a + coeff_s * sum(s) - delta_a * z_a <= 0
        row = np.zeros(n_var)
        row[base_T] = 1.0
        row[base_T + 1 : base_T + 1 + K] = coeff_s
        res_key = {0.25: "tail_025", 0.50: "tail_050", 1.00: "tail_100"}[alpha]
        row[idx_z + 1 + i] = -float(resolutions.get(res_key, "0.01"))
        static_A.append(row)
        static_b.append(0.0)

    # Variables bounds
    var_bounds = [(0.0, 1.0)] * n
    var_bounds += [(0.0, 1.0)] * K  # v
    var_bounds += [(0.0, 1.0)]  # M
    var_bounds += [(0.0, None)] * 4  # z
    var_bounds += [(None, None), *([(0.0, None)] * K)] * 3  # T blocks
    var_bounds += [(None, None), *([(0.0, None)] * K)] * K  # L blocks

    integrality = np.zeros(n_var)
    integrality[idx_z : idx_z + 4] = 1

    # Run the 8 + K stages sequentially
    stage_names = ["z_M", "z_25", "z_50", "z_100", "T_25", "T_50", "T_100", "M"] + [
        f"L_{p}" for p in range(1, K + 1)
    ]

    rowsA = list(static_A)
    rowsb = list(static_b)

    stage_optima = {}
    x = None

    for stage_idx, name in enumerate(stage_names):
        c_obj = np.zeros(n_var)

        if name.startswith("z_"):
            if name == "z_M":
                z_i = 0
            elif name == "z_25":
                z_i = 1
            elif name == "z_50":
                z_i = 2
            elif name == "z_100":
                z_i = 3
            c_obj[idx_z + z_i] = 1.0

        elif name.startswith("T_"):
            if name == "T_25":
                i, alpha = 0, 0.25
            elif name == "T_50":
                i, alpha = 1, 0.50
            elif name == "T_100":
                i, alpha = 2, 1.00
            base_T = off_T(i)
            c_obj[base_T] = 1.0
            c_obj[base_T + 1 : base_T + 1 + K] = 1.0 / (alpha * K)

        elif name == "M":
            c_obj[idx_M] = 1.0

        elif name.startswith("L_"):
            p = int(name.split("_")[1])
            base_L = off_L(p - 1)
            c_obj[base_L] = float(p)
            c_obj[base_L + 1 : base_L + 1 + K] = 1.0

            # epigraph constraints for s_p
            for k in range(K):
                row = np.zeros(n_var)
                row[n + k] = 1.0
                row[base_L] = -1.0
                row[base_L + 1 + k] = -1.0
                rowsA.append(row)
                rowsb.append(0.0)

        # Solve
        res = ctr.solve(
            c_obj, np.array(rowsA), np.array(rowsb), var_bounds, "stage", integrality
        )
        stage_optima[name] = float(res.fun)
        x = res.x[:n]

        # Add optimality constraint
        opt_val = float(res.fun)
        row = np.zeros(n_var)
        if name.startswith("z_"):
            z_i = {"z_M": 0, "z_25": 1, "z_50": 2, "z_100": 3}[name]
            row[idx_z + z_i] = 1.0
            rowsA.append(row)
            rowsb.append(np.round(opt_val))
        elif name.startswith("T_"):
            i, alpha = {"T_25": (0, 0.25), "T_50": (1, 0.50), "T_100": (2, 1.00)}[name]
            base_T = off_T(i)
            row[base_T] = 1.0
            row[base_T + 1 : base_T + 1 + K] = 1.0 / (alpha * K)
            rowsA.append(row)
            rowsb.append(opt_val + tol * (1.0 + abs(opt_val)))
        elif name == "M":
            row[idx_M] = 1.0
            rowsA.append(row)
            rowsb.append(opt_val + tol * (1.0 + abs(opt_val)))
        elif name.startswith("L_"):
            p = int(name.split("_")[1])
            base_L = off_L(p - 1)
            row[base_L] = float(p)
            row[base_L + 1 : base_L + 1 + K] = 1.0
            rowsA.append(row)
            rowsb.append(opt_val + tol * (1.0 + abs(opt_val)))

    elapsed = time.perf_counter() - t0
    d = _disappointments_at(x, rows, qstar, R)
    info = dict(
        stage_optima=stage_optima,
        profile_sorted=np.sort(d)[::-1],
        solver_calls=ctr.calls,
        bound_calls=ctr.bound_calls,
        anchor_calls=ctr.anchor_calls,
        stage_calls=ctr.stage_calls,
        K=K,
        m=m,
        elapsed_sec=elapsed,
    )
    return (x, info) if not return_profile else (x, info, d)
