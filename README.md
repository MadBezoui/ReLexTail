# ReLexTail: Resolution-Aware Lexicographic Preorder

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21771786.svg)](https://doi.org/10.5281/zenodo.21771786)

This repository contains the official code, data, and reproduction scripts for the paper:
**"ReLexTail: Resolution-Aware Lexicographic Preorder for Auditable Multicriteria Selection under Uncertain Bounds"**

## Overview
A multicriteria model usually ends with a set of efficient alternatives, not with a recommendation. Turning that set into one choice requires preference modeling that is often fragile. Existing robust and lexicographic methods fail to combine resolution-aware limits with complete transitive upper-tail sorting, often falling into non-transitive pairwise tolerances or giving infinite priority to microscopic worst-case differences. 

We introduce **ReLexTail**, a deterministic resolution-aware lexicographic preorder that integrates active-range probe regrets, discretised maximum and upper-tail empirical CVaR summaries, and exact numerical refinement. 

## Experimental Results
Our empirical benchmarking on 500 candidate sets (up to 500 points and 15 criteria, evaluating against knapsack, job-shop instances, WFG2, DTLZ, Energy, and Concrete surrogate matrices) demonstrates that ReLexTail successfully:
- Preserves the stability benefits of active-range normalisation.
- Defines a complete and transitive preorder (eliminating the 82% nontransitive indifference cycles observed in standard pairwise $\delta$-tolerances on exact leximax).
- Significantly improves hidden-preference tail regret.
- Allows fully auditable resolution through category assignment and numerical refinement.

## Requirements and Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/MadBezoui/ReLexTail.git
   cd ReLexTail
   ```
2. Create and activate a Conda environment:
   ```bash
   conda env create -f environment.yml
   conda activate lexpr_env
   ```

## Reproducibility (v2.0.0)
To regenerate all results, figures, and tables exactly as they appear in the manuscript, run the master reproduction script from the root directory:
```bash
python Experimental/scripts/reproduce_all.py
```
This script sequentially executes all six phases of the experimental pipeline:
1. **P1 (Combinatorial)**: Generates random knapsack and job-shop multicriteria sets.
2. **P2 (Continuous)**: Samples WFG/DTLZ test functions.
3. **P3 (Surrogates)**: Fits neural networks on UCI Energy and Concrete datasets and generates candidate points.
4. **P4 (Sensitivity)**: Tests interval bounds against perturbations.
5. **P5 (Certification)**: Validates ReLexTail enclosures via interval branch-and-bound against exact brute-force enumerations.
6. **P6 (Benchmarking)**: Evaluates ReLexTail against exact LexPR, Leximax, SMAA, TOPSIS, MMR, and random weights to construct the final quality-stability frontier.

The fully generated tables and figures (e.g. `quality_stability_frontier.pdf`, `fig_supplier_interval.pdf`, and the CSV tables) are written directly into `Experimental/manuscript/generated/`.

## Structure
- `Experimental/code/lexpr/`: Core library implementing ReLexTail and exact LexPR structures.
- `Experimental/scripts/`: Top-level reproduction and runner scripts.
- `Experimental/manuscript/generated/`: Output directory where reproduction scripts save CSV metrics and PDF graphics.

## License & Citation
If you use this code in your work, please cite the Zenodo archive:

```bibtex
@misc{bezoui2026archive,
  author = {Bezoui, Madani},
  title = {ReLexTail: Resolution-Aware Lexicographic Preorder},
  year = {2026},
  publisher = {Zenodo},
  doi = {10.5281/zenodo.21771786},
  url = {https://doi.org/10.5281/zenodo.21771786},
  version = {v2.0.0}
}
```

This project is licensed under the MIT License.
