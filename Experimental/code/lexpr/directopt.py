"""Direct computation of LexPR without enumerating the efficient set.

Two exploratory settings:
  (A) Continuous linear MOP: the first, minimax-regret coordinate of LexPR over
      linear probes is solved by LP and compared with generate-then-select.
      Later lexicographic coordinates are not implemented here.
  (B) Mixed-integer facility location: a four-solve anchor proxy is compared
      with a sampled weighted-sum front. This is not an exact direct LexPR MILP.

For linear probes q_k(r)=w_k^T r the regret D_k(x) is affine in x up to the
constant anchors q_k^*, q_k^w, so stage-1 LexPR is the LP
    min_{x in X, rho} rho   s.t.  (w_k^T r(x) - q_k^*)/(q_k^w-q_k^*) <= rho  for all k.
The anchors q_k^*, q_k^w are obtained by 2K scalar LPs/MILPs.
"""
from __future__ import annotations
import time
import numpy as np
from scipy.optimize import linprog

EPS = 1e-9


# --------------------------------------------------------------------------- #
# (A) continuous linear MOP
# --------------------------------------------------------------------------- #
def random_linear_mop(m, n=8, n_constr=5, rng=None):
    """min C x  s.t. A x <= b, 0<=x<=1, with m conflicting objectives over n
    variables. We impose *demand* constraints D x >= d (returned in <= form as
    A=-D, b=-d) so that x=0 is infeasible and the objectives genuinely trade off:
    each objective prefers cheap-for-it variables, but demand forces a mix."""
    rng = np.random.default_rng(0) if rng is None else rng
    C = rng.uniform(0.2, 1.0, size=(m, n))  # objective rows (costs)
    # make objectives conflict: each objective is cheap on a different variable block
    for i in range(m):
        C[i, i % n] *= 0.1
    D = rng.uniform(0.3, 1.0, size=(n_constr, n))  # demand coefficients
    d = rng.uniform(0.6, 1.0, size=n_constr) * (n / 3.0)
    A = -D
    b = -d  # D x >= d  <=>  -D x <= -d
    return C, A, b


def _solve_lp(c, A_ub, b_ub, bounds):
    res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")
    if not res.success:
        raise RuntimeError(f"LP solve failed: {res.message}")
    return res


def direct_lexpr_linear(C, A, b, probe_weights, tol=1e-6):
    """Stage-1 minimax-regret LexPR with linear probes via one LP (plus 2K anchor
    LPs). Returns (x, info)."""
    m, n = C.shape
    bounds = [(0, 1)] * n
    calls = 0
    # ideal/nadir per objective (for normalisation of r)
    f_ideal = np.zeros(m)
    f_nadir = np.zeros(m)
    for i in range(m):
        f_ideal[i] = _solve_lp(C[i], A, b, bounds).fun
        calls += 1
        f_nadir[i] = -_solve_lp(-C[i], A, b, bounds).fun
        calls += 1
    rng_obj = np.maximum(f_nadir - f_ideal, EPS)
    # probe anchors q* and q^w over X (each a scalar LP, since probe is linear in C x)
    K = probe_weights.shape[0]
    qstar = np.zeros(K)
    qworst = np.zeros(K)
    # probe value q_k(x) = w_k . r(x) = w_k . ((Cx - ideal)/range) = (w_k/range . C) x + const
    Crow = np.array([(probe_weights[k] / rng_obj) @ C for k in range(K)])  # K x n
    const = np.array([-(probe_weights[k] / rng_obj) @ f_ideal for k in range(K)])
    for k in range(K):
        qstar[k] = _solve_lp(Crow[k], A, b, bounds).fun + const[k]
        calls += 1
        qworst[k] = -_solve_lp(-Crow[k], A, b, bounds).fun + const[k]
        calls += 1
    qden = np.maximum(qworst - qstar, EPS)
    # stage-1 LP: min rho s.t. (Crow_k x + const_k - qstar_k)/qden_k <= rho
    # vars: [x (n), rho (1)]
    c = np.zeros(n + 1)
    c[-1] = 1.0
    Aub = np.zeros((A.shape[0] + K, n + 1))
    bub = np.zeros(A.shape[0] + K)
    Aub[: A.shape[0], :n] = A
    bub[: A.shape[0]] = b
    for k in range(K):
        Aub[A.shape[0] + k, :n] = Crow[k] / qden[k]
        Aub[A.shape[0] + k, -1] = -1.0
        bub[A.shape[0] + k] = (qstar[k] - const[k]) / qden[k]
    res = _solve_lp(c, Aub, bub, bounds + [(0, None)])
    calls += 1
    x = res.x[:n]
    return x, dict(
        solver_calls=calls,
        points_generated=0,
        rho1=float(res.x[-1]),
        f_ideal=f_ideal,
        f_nadir=f_nadir,
    )


def enumerate_then_select(C, A, b, n_weights=200, rng=None):
    """Two-stage baseline: generate a weighted-sum Pareto approximation, then
    post-process. Returns (candidate objective matrix F, info)."""
    rng = np.random.default_rng(0) if rng is None else rng
    m, n = C.shape
    bounds = [(0, 1)] * n
    W = rng.dirichlet(np.ones(m), size=n_weights)
    pts = []
    calls = 0
    for w in W:
        res = _solve_lp(w @ C, A, b, bounds)
        calls += 1
        pts.append(C @ res.x)
    F = np.unique(np.round(np.array(pts), 6), axis=0)
    return F, dict(solver_calls=calls, points_generated=len(F))


def run_linear_case(m=4, reps=10, seed=3):
    """Compare direct-LexPR vs enumerate-then-LexPR on random linear MOPs."""
    from . import methods, families
    from .methods import normalize

    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(reps):
        C, A, b = random_linear_mop(m, rng=rng)
        # probe weights: singletons + grand mean (linear monotone probes)
        pw = np.vstack([np.eye(m), np.ones(m) / m])
        t0 = time.time()
        x_dir, info_dir = direct_lexpr_linear(C, A, b, pw)
        t_dir = time.time() - t0
        f_dir = C @ x_dir
        t1 = time.time()
        F, info_enum = enumerate_then_select(C, A, b, n_weights=150, rng=rng)
        # post-process the enumerated front with full LexPR
        i_sel = methods.lexpr(F)
        f_enum = F[i_sel]
        t_enum = time.time() - t1
        # held-out quality: append both decisions to the enumerated front, score
        Fall = np.vstack([F, f_dir])
        cache = families.loss_cache(
            Fall, normalize, np.random.default_rng(11), n_per_family=300
        )
        tail_dir = families.losses_from(cache, Fall.shape[0] - 1)[1]
        tail_enum = families.losses_from(cache, i_sel)[1]
        rows.append(
            dict(
                direct_calls=info_dir["solver_calls"],
                direct_points=0,
                enum_calls=info_enum["solver_calls"],
                enum_points=info_enum["points_generated"],
                direct_time=t_dir,
                enum_time=t_enum,
                tail_direct=tail_dir,
                tail_enum=tail_enum,
            )
        )
    import pandas as pd

    df = pd.DataFrame(rows)
    return df.mean(numeric_only=True).to_dict()


# --------------------------------------------------------------------------- #
# (B) MILP facility location
# --------------------------------------------------------------------------- #
def run_facility_location(n_fac=8, n_cust=12, seed=4, n_weights=60):
    """Bi/tri-objective uncapacitated facility location (open cost, service
    distance, worst-case distance). Direct LexPR via repeated MILPs vs enumerate-
    then-select. Requires PuLP+CBC."""
    try:
        import pulp
    except Exception:
        return {"available": False}
    rng = np.random.default_rng(seed)
    open_cost = rng.uniform(10, 30, size=n_fac)
    dist = rng.uniform(1, 20, size=(n_cust, n_fac))

    def solve_weighted(w):
        prob = pulp.LpProblem("fl", pulp.LpMinimize)
        y = [pulp.LpVariable(f"y{j}", cat="Binary") for j in range(n_fac)]
        x = [
            [pulp.LpVariable(f"x{i}_{j}", cat="Binary") for j in range(n_fac)]
            for i in range(n_cust)
        ]
        dmax = pulp.LpVariable("dmax", lowBound=0)
        f_open = pulp.lpSum(open_cost[j] * y[j] for j in range(n_fac))
        f_serv = pulp.lpSum(
            dist[i][j] * x[i][j] for i in range(n_cust) for j in range(n_fac)
        )
        prob += w[0] * f_open + w[1] * f_serv + w[2] * dmax
        for i in range(n_cust):
            prob += pulp.lpSum(x[i][j] for j in range(n_fac)) == 1
            for j in range(n_fac):
                prob += x[i][j] <= y[j]
                prob += dmax >= dist[i][j] * x[i][j]
        prob.solve(pulp.PULP_CBC_CMD(msg=0))
        oc = sum(open_cost[j] * y[j].value() for j in range(n_fac))
        sv = sum(
            dist[i][j] * x[i][j].value() for i in range(n_cust) for j in range(n_fac)
        )
        dm = dmax.value()
        return np.array([oc, sv, dm])

    t0 = time.time()
    calls = 0
    pts = []
    W = rng.dirichlet(np.ones(3), size=n_weights)
    for w in W:
        pts.append(solve_weighted(w))
        calls += 1
    F = np.unique(np.round(np.array(pts), 4), axis=0)
    t_enum = time.time() - t0
    from . import methods

    i_sel = methods.lexpr(F)
    # "direct" proxy: scalarised minimax-regret weight found by a small search
    # over the same weight family but only K+1 solves (singletons + mean)
    t1 = time.time()
    dcalls = 0
    probe_w = np.vstack([np.eye(3), np.ones(3) / 3])
    anchor = []
    for w in probe_w:
        anchor.append(solve_weighted(w))
        dcalls += 1
    F_small = np.array(anchor)
    # pick the minimax-regret point among the few solves
    r = (F_small - F.min(0)) / (np.maximum(F.max(0) - F.min(0), EPS))
    i_dir = int(np.argmin(r.max(1)))
    t_dir = time.time() - t1
    return dict(
        available=True,
        enum_solver_calls=calls,
        enum_points=len(F),
        enum_time=round(t_enum, 2),
        direct_solver_calls=dcalls,
        direct_time=round(t_dir, 2),
        chosen_enum=F[i_sel].round(2).tolist(),
        chosen_direct=F_small[i_dir].round(2).tolist(),
    )
