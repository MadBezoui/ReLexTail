"""Lexicographic Probe-Regret (LexPR) Core — reference implementation and experiments.

Modules:
    problems    : multi-objective Pareto-front candidate-set generators
    methods     : selection methods (LexPR + classical + robust-MCDA baselines)
    metrics     : out-of-class loss, worst-case regret, agreement, etc.
    stats       : Friedman / Nemenyi / Wilcoxon / Cliff's delta
    experiments : benchmark orchestration
    smartgrid   : 6-objective stochastic dispatch decision case study
"""
__all__ = [
    "analysis",
    "claim_gate",
    "directopt",
    "experiments",
    "extras_validation",
    "families",
    "gates",
    "manuscript",
    "methods",
    "metrics",
    "normalization",
    "probe_validation",
    "problems",
    "provenance",
    "records",
    "reporting",
    "smartgrid",
    "stats",
]
__version__ = "1.0.0"
