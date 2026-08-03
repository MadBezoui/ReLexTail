import sys

replacements_main = {
    r"In pathological tolerance cycles $W_\tau$ may be empty; the implementation then reports": r"In pathological tolerance cycles $W_\tau$ may be empty, and the implementation then reports",
    r"separated from the second worst by a positive gap; otherwise a positive reporting band": r"separated from the second worst by a positive gap. Otherwise, a positive reporting band",
    r"the sorted profiles; details are given in the online supplement.": r"the sorted profiles. Details are given in the online supplement.",
    r"requires pairwise comparisons; with naive probe evaluation": r"requires pairwise comparisons. With naive probe evaluation",
    r"two linear programs;": r"two linear programs,",
    r"one reproducible decision problem; the conclusions are illustrative": r"one reproducible decision problem. The conclusions are illustrative",
    r"remains weak or strong; they do not by themselves": r"remains weak or strong. They do not by themselves",
    r"comparison is guaranteed unchanged; the remaining removals": r"comparison is guaranteed unchanged. The remaining removals",
    r"Moreover, the interval experiment varies criterion bounds and recomputes probe anchors; it does not represent": r"Moreover, the interval experiment varies criterion bounds and recomputes probe anchors. It does not represent",
    r"bounded polyhedral feasible sets.": r"bounded polyhedral feasible sets.",
    r"families, and multiplicities; alternatives to anonymous": r"families, and multiplicities, alternatives to anonymous",
    r"institutional status; exact computation of stability": r"institutional status, exact computation of stability",
    r"structured probe families; and extensions": r"structured probe families, and extensions",
    r"S^{\mathrm{pos}}_\tau; when Monte Carlo": r"S^{\mathrm{pos}}_\tau. When Monte Carlo",
}

replacements_theory = {
    r"regret of every criterion;": r"regret of every criterion,",
    r"q_\mu(r)=m^{-1}\sum_i r_i;": r"q_\mu(r)=m^{-1}\sum_i r_i,",
    r"q_{\max}(r)=\max_i r_i;": r"q_{\max}(r)=\max_i r_i,",
    r"summarised by its cluster mean; the corresponding root-mean-square": r"summarised by its cluster mean. The corresponding root-mean-square",
}

with open("../paper/build/main.tex", "r") as f:
    text_main = f.read()

for k, v in replacements_main.items():
    text_main = text_main.replace(k, v)

with open("../paper/build/main.tex", "w") as f:
    f.write(text_main)

with open("../paper/build/theory_core.tex", "r") as f:
    text_theory = f.read()

for k, v in replacements_theory.items():
    text_theory = text_theory.replace(k, v)

with open("../paper/build/theory_core.tex", "w") as f:
    f.write(text_theory)

print("Done replacing semicolons.")
