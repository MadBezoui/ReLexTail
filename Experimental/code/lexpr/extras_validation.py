"""Stochastic (train/test) and multi-stakeholder validation."""
from __future__ import annotations
import numpy as np
from . import problems, methods, families
from .methods import normalize, EPS


# --------------------------------------------------------------------------- #
# Stochastic: select on training scenarios, evaluate out-of-sample
# --------------------------------------------------------------------------- #
def _stochastic_lexpr(mu, sd, z, n_obs):
    """Alpha-confidence LexPR using uncertainty in the estimated mean."""
    F = mu + z * sd / np.sqrt(n_obs)
    return methods.lexpr(F)


def run_stochastic(
    train_scenarios=50,
    test_scenarios=3000,
    alphas=(0.5, 0.8, 0.95),
    reps=15,
    n=120,
    m=6,
    seed=71,
):
    rng = np.random.default_rng(seed)
    zmap = {0.5: 0.0, 0.8: 0.8416, 0.95: 1.6449}
    methods_list = ["det-LexPR"] + [f"LexPR-a{a}" for a in alphas] + ["TOPSIS", "SMAA"]
    acc = {nm: {"mean": [], "tail": [], "risk": []} for nm in methods_list}
    for _ in range(reps):
        g = problems.GEOMETRIES[int(rng.integers(0, 4))]
        mu = problems.make_candidate_set(g, n, m, rng)  # true means
        sd = (
            0.10
            * (mu.std(0, keepdims=True) + 1e-3)
            * (0.5 + rng.random((mu.shape[0], m)))
        )
        # training scenarios -> estimates
        tr = mu[None] + sd[None] * rng.standard_normal((train_scenarios, *mu.shape))
        mu_hat = tr.mean(0)
        sd_hat = tr.std(0)
        # held-out utilities defined on true means (out-of-class)
        cache = families.loss_cache(
            mu, normalize, np.random.default_rng(7), n_per_family=300
        )
        risk_thr = 0.8  # worst-criterion risk
        picks = {"det-LexPR": _stochastic_lexpr(mu_hat, sd_hat, 0.0, train_scenarios)}
        for a in alphas:
            picks[f"LexPR-a{a}"] = _stochastic_lexpr(
                mu_hat, sd_hat, zmap[a], train_scenarios
            )
        picks["TOPSIS"] = methods.topsis(mu_hat)
        picks["SMAA"] = methods.smaa(mu_hat, rng=np.random.default_rng(3))
        # out-of-sample test scenarios
        te = mu[None] + sd[None] * rng.standard_normal((test_scenarios, *mu.shape))
        rnorm = normalize(mu)
        for nm, idx in picks.items():
            ml, tl, _, _ = families.losses_from(cache, idx)
            acc[nm]["mean"].append(ml)
            acc[nm]["tail"].append(tl)
            worst_crit = normalize(mu)[idx].max()  # proxy; use realized exceedance
            exceed = (te[:, idx, :].max(axis=1) > (mu.max(0).max() * risk_thr)).mean()
            acc[nm]["risk"].append(float(exceed))
    import pandas as pd

    rows = [
        dict(
            method=nm,
            mean_loss=float(np.mean(acc[nm]["mean"])),
            tail_loss=float(np.mean(acc[nm]["tail"])),
            risk=float(np.mean(acc[nm]["risk"])),
        )
        for nm in methods_list
    ]
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Multi-stakeholder
# --------------------------------------------------------------------------- #
def _gini(x):
    x = np.sort(np.asarray(x))
    k = len(x)
    if x.sum() == 0:
        return 0.0
    return float((2 * np.arange(1, k + 1) - k - 1) @ x / (k * x.sum()))


def run_multistakeholder(stakeholders=(3, 5, 10, 20), reps=20, n=200, m=6, seed=83):
    rng = np.random.default_rng(seed)
    out = []
    for S in stakeholders:
        agg = {
            nm: {"worst": [], "mean": [], "gini": []}
            for nm in ["Rawls-LexPR", "AvgUtil", "Nash", "MaxMin"]
        }
        for _ in range(reps):
            g = problems.GEOMETRIES[int(rng.integers(0, 4))]
            F = problems.make_candidate_set(g, n, m, rng)
            r = normalize(F)
            Wt = rng.dirichlet(np.ones(m), size=S)  # stakeholder weights
            cost = r @ Wt.T  # N x S (lower better)
            # stakeholder regret = normalised cost gap to each stakeholder's best
            reg = (cost - cost.min(0)) / (cost.max(0) - cost.min(0) + EPS)
            picks = {
                "Rawls-LexPR": methods.leximax_argmin(
                    reg
                ),  # leximax over stakeholder regrets
                "AvgUtil": int(np.argmin(cost.mean(1))),
                "Nash": int(np.argmax(np.log(1 - reg + 1e-6).sum(1))),
                "MaxMin": int(np.argmin(cost.max(1))),
            }
            for nm, idx in picks.items():
                agg[nm]["worst"].append(float(reg[idx].max()))
                agg[nm]["mean"].append(float(reg[idx].mean()))
                agg[nm]["gini"].append(_gini(reg[idx]))
        for nm in agg:
            out.append(
                dict(
                    stakeholders=S,
                    method=nm,
                    worst_regret=float(np.mean(agg[nm]["worst"])),
                    mean_regret=float(np.mean(agg[nm]["mean"])),
                    gini=float(np.mean(agg[nm]["gini"])),
                )
            )
    import pandas as pd

    return pd.DataFrame(out)
