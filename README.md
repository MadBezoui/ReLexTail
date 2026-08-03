# ReLexTail: Resolution-Aware Lexicographic Preorder

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21771786.svg)](https://doi.org/10.5281/zenodo.21771786)

ReLexTail is a deterministic, resolution-aware lexicographic preorder designed for multicriteria decision making under uncertain normalisation bounds. It integrates active-range probe regrets, discretised maximum and upper-tail empirical CVaR summaries, and exact numerical refinement to provide robust out-of-sample recommendations without relying on hidden preference assumptions.

This repository contains the official Python implementation of the ReLexTail algorithm, along with the complete experimental protocol and scripts used to reproduce the results, tables, and figures presented in the associated manuscript.

## Overview of Results

Our comprehensive evaluation on 500 instances across diverse synthetic and surrogate families demonstrates that exact LexPR and classical lexicographic minimax approaches are highly fragile to microscopic variations in normalization bounds. Specifically:
- **Point Flip Rate**: Exact LexPR experiences an 18.3% point flip rate under a 5% bound perturbation, owing to its infinite priority to microscopic differences in the absolute worst probe.
- **ReLexTail Stability**: By introducing a resolution parameter $\delta=0.01$, ReLexTail reduces this point flip rate to just 6.2%.
- **Category Stability**: The category-optimal set ($W_{\text{cat}}$) of ReLexTail achieved a 0.0% flip rate under the tested protocol, significantly improving structural stability before exact numerical refinement breaks ties.
- **Quality-Stability Trade-off**: ReLexTail improves upon both exact LexPR and standard scalarization baselines (like TOPSIS, MMR, and ASF) in the quality-stability trade-off, balancing hidden-preference tail regret and structural stability.
- **Certified Bounds**: Using interval branch-and-bound techniques, ReLexTail allows researchers to construct sound inner and outer possible-winner enclosures when normalisation denominators are bounded away from zero. 

## Repository Structure

- **`Experimental/code/lexpr/`**: Core Python package implementing the algorithm.
  - `robust_relex.py`: The ReLexTail implementation, sorting, and categorization mechanics.
  - `certified.py`: Interval branch-and-bound certification for robust inner/outer enclosures.
  - `metrics.py`: Regret definitions, evaluations, and caching logic.
  - `experiments.py` & `experiments_phase6.py`: Main logic for redundant instances, quality-stability frontiers, and ablation studies.
  
- **`Experimental/scripts/`**: Orchestration scripts.
  - `reproduce_all.py`: Master runner to regenerate all tables and figures.

- **`Experimental/manuscript/generated/`**: Output directory for generated artifacts.

## Reproducing the Experiments

The experiments rely on standard scientific Python libraries (such as `numpy`, `pandas`, `scipy`) and solvers for the continuous formulations.

### 1. Installation

Set up a virtual environment and install the package:

```bash
cd Experimental/code
pip install -r requirements.txt
pip install -e .
```

### 2. Running the Full Protocol

To regenerate the tables and figures, run the master orchestration script. **Note:** Full execution involves computationally intensive tasks (e.g., branch-and-bound certification and SMAA $10,000$-draw runs) and may take several minutes.

```bash
cd Experimental/scripts
python3 reproduce_all.py
```

Outputs will be saved in `Experimental/manuscript/generated/tables/` and `Experimental/manuscript/generated/figures/`.

## Interpreting the Output Data

- **`benchmark_raw.csv`**: Unaggregated results of all candidate sets and perturbations.
- **`main_comparison.csv`**: Aggregated population-level metrics (Mean Loss and Tail Regret).
- **`stats_summary.json`**: Rigorous statistical evaluations, including Friedman ranks, Wilcoxon signed-rank tests, and paired 95% confidence intervals against exact LexPR.
- **`fig_divergence.pdf`**: Shows the proportion of instances where ReLexTail's recommendation diverges from exact LexPR across different candidate set generators.
- **`fig_certified_decay.pdf`**: Visualizes the shrinkage of the unresolved interval volume as the branch-and-bound certification budget increases.

## Citation

If you use this code in your work, please cite the associated manuscript and use the Zenodo DOI: [10.5281/zenodo.21771786](https://doi.org/10.5281/zenodo.21771786).

## License

This software is released under the MIT License.
