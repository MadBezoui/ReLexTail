"""Regenerate the ReLexTail supplier decision-profile figure (Fig. relex_profile)
directly from the archived supplier diagnostics, so that the figure, the
generated \\supReLex* macros, and the rewritten section 7.8 all agree:
seven criteria, nine canonical probes, winner S7, decisive coordinate C_M.

This is a deterministic re-plot of ALREADY-ARCHIVED numbers
(Resultats/results/supplier/supplier_case.json). It does not re-run any
experiment; reported numbers are unchanged.
"""
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "Resultats" / "results" / "supplier" / "supplier_case.json"
OUT = ROOT / "Manuscrit" / "generated" / "figures" / "relex_decision_profile.pdf"

data = json.load(open(SRC))
cert = data["certificate"]            # 9 canonical probes for S7
diag = data["relex_diagnostics"]

# ----- Panel A data: labelled probe disappointments (sorted worst-first) -----
labels = [c["probe"] for c in cert]
vals = [float(c["regret"]) for c in cert]
order = np.argsort(vals)              # ascending -> plot so largest on top
labels = [labels[i] for i in order]
vals = [vals[i] for i in order]

# ----- Panel B data: tail spectrum T_alpha from the sorted disappointments ----
Ddesc = np.sort(np.array([float(c["regret"]) for c in cert]))[::-1]
K = len(Ddesc)


def T_alpha(alpha):
    h = alpha * K
    if h < 1:
        return Ddesc[0]
    k = int(math.floor(h))
    theta = h - k
    S = Ddesc[:k].sum()
    if theta > 0 and k < K:
        S += theta * Ddesc[k]
    return S / h


alphas = np.linspace(1.0 / K, 1.0, 200)
Tcurve = np.array([T_alpha(a) for a in alphas])
mark_a = [0.25, 0.50, 1.00]
mark_T = [diag["S7_exact_T25"], diag["S7_exact_T50"], diag["S7_exact_T100"]]

# ----- Panel C data: resolution categories (stored integers) + exact values ---
cats = diag["S7_profile_cats"]        # [C_M, C_25, C_50, C_100]
exact = [diag["S7_exact_M"], diag["S7_exact_T25"],
         diag["S7_exact_T50"], diag["S7_exact_T100"]]
cat_labels = ["Maximum", "T_0.25", "T_0.50", "T_1.00"]

# ---------------------------------------------------------------------------- #
plt.rcParams.update({"font.size": 9})
fig, (axA, axB, axC) = plt.subplots(3, 1, figsize=(6.0, 8.0))

# Panel A
ypos = np.arange(len(vals))
axA.barh(ypos, vals, color="#2980B9")
axA.set_yticks(ypos)
axA.set_yticklabels(labels)
axA.set_xlabel("Disappointment")
axA.set_xlim(0, max(0.85, max(vals) * 1.05))
axA.set_title("Panel A: Probe Disappointments")

# Panel B
axB.plot(alphas, Tcurve, color="#C0392B", lw=1.6)
axB.plot(mark_a, mark_T, "o", color="#C0392B")
axB.set_xlabel(r"Tail fraction $\alpha$")
axB.set_ylabel(r"Tail Score $T_\alpha(x)$")
axB.set_title("Panel B: Tail Spectrum")
axB.set_ylim(0, max(Tcurve) * 1.08)

# Panel C
xpos = np.arange(len(cats))
axC.bar(xpos, cats, color="#BDBDBD", width=0.6)
axC.set_xticks(xpos)
axC.set_xticklabels(cat_labels)
axC.set_ylabel("Category Integer")
axC.set_title("Panel C: Resolution Categories")
axC2 = axC.twinx()
axC2.plot(xpos, exact, "o-", color="#C0392B", lw=1.6)
axC2.set_ylabel("Score Value")

fig.tight_layout()
fig.savefig(OUT)
print("wrote", OUT)
print("Panel A probes:", list(zip(labels, [round(v, 3) for v in vals])))
print("cats:", cats, "exact:", [round(e, 3) for e in exact])
