import numpy as np
from dataclasses import dataclass
from typing import Literal
from .methods import lexpr_variant


@dataclass
class StabilityResult:
    status: Literal["recommend", "set", "abstain"]
    indices: list[int]
    frequencies: dict[int, float]


def lexpr_stable(
    F: np.ndarray,
    bounds: list[tuple[np.ndarray, np.ndarray]],
    min_identity_rate: float = 0.90,
    set_coverage_rate: float = 0.95,
    max_set_size: int = 3,
    **kwargs
) -> StabilityResult:
    n_samples = len(bounds)
    if n_samples == 0:
        return StabilityResult("abstain", [], {})

    counts = {}
    for ideal, nadir in bounds:
        idx = lexpr_variant(F, ideal=ideal, nadir=nadir, **kwargs)
        counts[idx] = counts.get(idx, 0) + 1

    frequencies = {idx: c / n_samples for idx, c in counts.items()}
    sorted_indices = sorted(
        frequencies.keys(), key=lambda i: frequencies[i], reverse=True
    )

    if frequencies[sorted_indices[0]] >= min_identity_rate:
        return StabilityResult("recommend", [sorted_indices[0]], frequencies)

    cum_freq = 0.0
    set_indices = []
    for idx in sorted_indices:
        cum_freq += frequencies[idx]
        set_indices.append(idx)
        if cum_freq >= set_coverage_rate and len(set_indices) <= max_set_size:
            return StabilityResult("set", set_indices, frequencies)

    return StabilityResult("abstain", set_indices[:max_set_size], frequencies)


def generate_bounds(
    F: np.ndarray, n_samples: int, mode: str, rng: np.random.Generator
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Generate realistic bound estimators."""
    m = F.shape[1]
    bounds = []
    obs_min = F.min(axis=0)
    obs_max = F.max(axis=0)
    obs_range = obs_max - obs_min

    for _ in range(n_samples):
        if mode == "minmax":
            jitter_nadir = rng.uniform(0.0, 0.05, size=m)
            jitter_ideal = rng.uniform(0.0, 0.02, size=m)
            bounds.append(
                (
                    obs_min - jitter_ideal * obs_range,
                    obs_max + jitter_nadir * obs_range,
                )
            )
        elif mode == "quantiles":
            bounds.append((np.percentile(F, 1, axis=0), np.percentile(F, 99, axis=0)))
        elif mode == "subset":
            idx = rng.choice(F.shape[0], size=max(1, F.shape[0] // 2), replace=False)
            sub_F = F[idx]
            bounds.append((sub_F.min(axis=0), sub_F.max(axis=0)))
        elif mode == "asymmetric_error":
            err_nadir = rng.uniform(0.0, 0.2, size=m)
            err_ideal = rng.uniform(0.0, 0.1, size=m)
            nadir = obs_max + err_nadir * obs_range
            ideal = obs_min - err_ideal * obs_range
            bounds.append((ideal, nadir))
        elif mode == "correlated_error":
            common = rng.uniform(0.0, 0.15)
            err_nadir = rng.uniform(0.0, 0.05, size=m) + common
            err_ideal = rng.uniform(0.0, 0.05, size=m) + common
            nadir = obs_max + err_nadir * obs_range
            ideal = obs_min - err_ideal * obs_range
            bounds.append((ideal, nadir))
        else:
            bounds.append((obs_min, obs_max))

    return bounds


def normalization_stability(
    F: np.ndarray,
    bound_samples: list[tuple[np.ndarray, np.ndarray]],
    tolerance: float = 1e-9,
) -> StabilityResult:
    return lexpr_stable(F, bound_samples)
