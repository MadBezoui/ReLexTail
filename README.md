# ReLexTail: Resolution-Aware Lexicographic Preorder

ReLexTail is a deterministic, resolution-aware lexicographic preorder designed for multicriteria decision making under uncertain normalisation bounds. It integrates active-range probe regrets, discretised maximum and upper-tail empirical CVaR summaries, and exact numerical refinement to provide robust out-of-sample recommendations without relying on hidden preference assumptions.

This repository contains the official Python implementation of the ReLexTail algorithm, along with the complete experimental protocol and scripts used to reproduce the results (tables and figures) presented in the associated manuscript.

## Repository Structure

The repository is organized into the following main directories:

- **`Experimental/code/lexpr/`**: The core Python package implementing the ReLexTail algorithm. It includes:
  - Interval branch-and-bound certification for robust inner/outer enclosures.
  - Continuous exact refinement via Mixed-Integer Linear Programming (MILP).
  - Implementation of empirical baseline methods (SMAA, Random Weights, TOPSIS, MMR, Compromise Programming, etc.).

- **`Experimental/scripts/`**: Contains the scripts for running the full evaluation suite.
  - `reproduce_all.py`: The main orchestration script that runs the experiments and generates all tables and figures (including paired 95% CIs) from the manuscript.

- **`Experimental/manuscript/generated/`**: The output directory where the experimental pipeline dumps its artifacts.
  - `tables/`: Contains the generated `.csv` and `.json` data tables (e.g., `main_comparison.csv`, `stats_summary.json`).
  - `figures/`: Contains the generated PDF plots (e.g., `fig_divergence.pdf`, `fig_certified_decay.pdf`) used directly in the manuscript.

## Reproducing the Experiments

The experiments depend on standard scientific Python libraries (such as `numpy`, `pandas`, `scipy`) and solvers for the MILP continuous formulations.

### 1. Installation

It is recommended to use a virtual environment. You can install the package and its dependencies by running:

```bash
cd Experimental/code
pip install -r requirements.txt
pip install -e .
```

### 2. Running the Full Protocol

To regenerate the tables and figures found in the manuscript, simply run the orchestration script. Note that the full protocol includes computationally intensive simulations (such as the branch-and-bound certification and SMAA $10,000$-draw runs) and may take several minutes to complete.

```bash
cd Experimental/scripts
python3 reproduce_all.py
```

The script will automatically execute:
- **Baseline Evaluation**: Compares ReLexTail against exact LexPR, exact leximax, and standard scalarizations across diverse generator families (e.g., WFG2, DTLZ, knapsack, job-shop).
- **Certification Tests**: Runs interval branch-and-bound tracking unresolved volume decay over budgets.
- **Sensitivity & Ablation**: Tests the impact of varying the retention threshold ($\delta$) and structural normalisation choices.
- **Table/Figure Generation**: Dumps the formatted outputs directly into `Experimental/manuscript/generated/`.

## Interpreting the Output Data

The `Experimental/manuscript/generated/tables/` directory contains the raw and aggregated metrics:
- **`benchmark_raw.csv`**: The unaggregated results of all candidate sets and perturbations.
- **`main_comparison.csv`**: The aggregated population-level metrics (Mean Loss and Tail Regret).
- **`stats_summary.json`**: Contains rigorous statistical evaluations, including Friedman ranks, Wilcoxon signed-rank tests with Holm corrections, Cliff's delta effect sizes, and paired 95% confidence intervals against exact LexPR.

The `Experimental/manuscript/generated/figures/` directory contains standard visual outputs:
- **`fig_divergence.pdf`**: Shows the proportion of instances where ReLexTail's recommendation diverges from exact LexPR across different candidate set generators.
- **`fig_certified_decay.pdf`**: Visualizes the shrinkage of the unresolved interval volume as the branch-and-bound certification budget increases.

## License

This software is released under the MIT License. Please see the `.zenodo.json` file for automation metadata associated with our V1.0.0 release.
