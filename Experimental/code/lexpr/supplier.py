"""Sustainable supplier selection case study for LexPR.

A fully reproducible, literature-grounded MCDA instance used as the real-world
validation case (Work Package 2) and as the shared decision problem behind the
human-evaluation questionnaire (Work Package 4).

The criteria follow the consensus structure of the sustainable / green supplier
selection literature, which spans the three pillars of the triple bottom line
(economic, environmental, social) plus operational resilience:

    f1  Unit cost            (EUR/unit)         economic     -> minimise
    f2  Defect rate          (% rejected)       quality      -> minimise
    f3  Lead time            (days)             operational  -> minimise
    f4  GHG emissions        (kg CO2e/unit)     environment  -> minimise
    f5  Energy intensity     (kWh/unit)         environment  -> minimise
    f6  Social/labour risk   (0-100 index)      social       -> minimise
    f7  Supply resilience    (0-100 risk index) operational  -> minimise

All seven criteria are expressed as costs (smaller is better), so the matrix is
a pure minimisation problem and feeds directly into the LexPR core and the
baseline registry without sign flips.

f4 (GHG) and f5 (energy intensity) are deliberately redundant: both track the
same environmental footprint and are strongly positively correlated by
construction. This lets the case exercise the adaptive correlation-clustering
probe family on a *named*, interpretable redundancy rather than a synthetic one.

The data are a constructed but realistic institutional decision problem. They
are not field measurements; every value is fixed in source so the case is
exactly reproducible and auditable, consistent with the paper's scope policy.
"""
from __future__ import annotations
import numpy as np

# Criterion metadata ---------------------------------------------------------
CRITERIA = [
    ("Cost", "EUR/unit", "economic"),
    ("Defects", "% rejected", "quality"),
    ("LeadTime", "days", "operational"),
    ("GHG", "kg CO2e/unit", "environment"),
    ("Energy", "kWh/unit", "environment"),
    ("SocialRisk", "0-100 index", "social"),
    ("Resilience", "0-100 risk", "operational"),
]
CRIT_NAMES = [c[0] for c in CRITERIA]
CRIT_UNITS = [c[1] for c in CRITERIA]

# Candidate suppliers (rows) x criteria (cols), all to be minimised ----------
# Ten pre-screened suppliers. Values fixed for exact reproducibility.
SUPPLIERS = [
    "S1",
    "S2",
    "S3",
    "S4",
    "S5",
    "S6",
    "S7",
    "S8",
    "S9",
    "S10",
]

_RAW = np.array(
    [
        # Cost  Defect Lead  GHG  Energy Social Resil
        [55.9, 2.9, 22.0, 17.1, 32.2, 46.1, 36.5],  # S1  mid all-round
        [50.1, 3.3, 27.0, 11.5, 24.0, 65.7, 54.8],  # S2  cheap-green, weak social/resil
        [
            55.5,
            0.7,
            29.6,
            12.9,
            25.5,
            20.0,
            58.2,
        ],  # S3  top quality+social, slow+fragile
        [50.5, 1.1, 32.1, 9.9, 20.8, 62.8, 58.1],  # S4  clean+quality, social+resil gap
        [59.8, 0.7, 15.7, 11.8, 22.5, 31.2, 24.1],  # S5  fast+quality+resilient, pricey
        [
            50.7,
            3.3,
            29.3,
            8.5,
            17.1,
            16.3,
            23.2,
        ],  # S6  greenest+social+resilient, defects+slow
        [55.2, 3.3, 17.0, 7.4, 15.8, 23.0, 41.6],  # S7  green+social+fast, defects
        [
            48.8,
            4.0,
            33.2,
            20.6,
            37.4,
            41.8,
            24.6,
        ],  # S8  cheap+resilient, dirty+slow+defects
        [
            44.9,
            3.9,
            14.9,
            13.9,
            26.7,
            68.8,
            49.0,
        ],  # S9  cheapest+fast, dirty social+defects
        [55.1, 3.8, 20.1, 17.8, 31.5, 31.6, 52.1],  # S10 mid, fragile
    ],
    dtype=float,
)


def load_supplier_case() -> tuple[np.ndarray, list[str], list[str]]:
    """Return (F, supplier_names, criterion_names) for the case study."""
    return _RAW.copy(), list(SUPPLIERS), list(CRIT_NAMES)


def pareto_mask(F: np.ndarray) -> np.ndarray:
    """Boolean mask of Pareto-efficient rows (minimisation, weak dominance)."""
    n = F.shape[0]
    eff = np.ones(n, dtype=bool)
    for i in range(n):
        if not eff[i]:
            continue
        for j in range(n):
            if i == j:
                continue
            if np.all(F[j] <= F[i]) and np.any(F[j] < F[i]):
                eff[i] = False
                break
    return eff


def correlation_table(F: np.ndarray) -> np.ndarray:
    """Pearson correlation matrix across criteria (for the redundancy story)."""
    return np.corrcoef(F.T)


if __name__ == "__main__":
    F, sup, crit = load_supplier_case()
    print("Suppliers:", sup)
    print("Criteria :", crit)
    print("Pareto-efficient:", [sup[i] for i in np.where(pareto_mask(F))[0]])
    C = correlation_table(F)
    gi, ei = crit.index("GHG"), crit.index("Energy")
    print(f"Corr(GHG, Energy) = {C[gi, ei]:.3f}")
