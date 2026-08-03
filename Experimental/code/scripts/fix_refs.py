import os

replacements = {
    "main.tex": [
        (r"Section~\ref{sec:exp-diverge} quantifies", r"Section~\ref{sec:exp-knapsack} quantifies"),
        (r"Sections~\ref{sec:exp-probe} and~\ref{sec:supplier-ablation}", r"Section~\ref{sec:supplier-ablation}"),
        (r"Section~\ref{sec:exp-diverge} and the runtime", r"Section~\ref{sec:exp-knapsack} and the runtime")
    ],
    "theory_core.tex": [
        (r"(Table~\ref{tab:reduction}), and reduces", r"and reduces")
    ],
    "experiments_new.tex": [
        (r"Table~\ref{tab:knapsack-classes} lists the instance classes and the resulting front sizes.", 
         r"The knapsack instances span dimensions 3 to 5 and sizes up to $N=300$.")
    ]
}

for filename, reps in replacements.items():
    path = os.path.join("../paper/build", filename)
    with open(path, "r") as f:
        text = f.read()
    for old, new in reps:
        text = text.replace(old, new)
    with open(path, "w") as f:
        f.write(text)

print("Fixed refs.")
