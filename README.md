# ReLexTail: resolution-aware lexicographic tail-regret selection

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22558690.svg)](https://doi.org/10.5281/zenodo.22558690)

Code, data and reproduction scripts for **"Resolution-Aware Lexicographic
Tail-Regret Selection under Uncertain Normalisation Bounds"** (M. Bezoui).

The current manuscript is `Manuscrit/main.pdf`. The Zenodo DOI above resolves to
an **earlier** archive; the experiments in the current manuscript are larger and
partly different and must not be attributed to that unchanged release.

## What the method is

A multicriteria model usually ends with a set of efficient alternatives, not
with a recommendation. ReLexTail turns that set into one choice by a declared,
auditable rule: it evaluates a declared multiset of monotone *probes*, converts
each probe value into an active-range *disappointment* in `[0,1]`, and compares
alternatives lexicographically on

```
Psi = ( C_M, C_25, C_50, C_100, T_25, T_50, T_100, M, sorted disappointments )
```

— fixed-resolution categories of the maximum and of the upper-tail means first,
then the exact tail means, then the full sorted profile. Fixed cells give a
*transitive* categorical equality, which pairwise indifference tolerances do
not. The building blocks — ordered aggregation, empirical CVaR, lexicographic
optimisation — are established tools and are not claimed as new.

## What is established, and what is not

| Claim | Status |
|---|---|
| Complete transitive preorder, exact refinement, boundary/tie conventions | proved |
| Conditional Pareto compatibility, replication invariance | proved, under stated assumptions |
| Category stability under a sup-norm perturbation | proved, sufficient only (can be vacuous) |
| Sound interval possible-winner elimination | proved |
| A decision certified with no candidate retaining any category | proved, with a rational example |
| Shared-anchor enclosures contained in independent ones | proved, with a rational example |
| No emitted certificate falsified by an exact oracle or independent replay | measured |
| Decision focus and dependency preservation raise the certified radius | measured on a locked split |
| Upper-tail regret differs from exact LexPR at delta = 0.02 | measured, small and metric-dependent |
| Point-stability gain at delta = 0.02 | **not supported** — the paired interval includes zero |
| Lower external regret at matched coverage; calibration guarantee | **unestablished** — not tested |
| Benefit on measured operational data | **unestablished** — no field data |
| Priority over the closest literature | **unestablished** — full-text verification pending |

The full register is `Manuscrit/submission/discussion.tex` (Table: claim-to-evidence)
and `enhanced/protocol/claim_registry.csv`. Earlier versions of this README
carried performance claims — a 500-instance benchmark, an 82% cycle rate, a
"significant" tail-regret improvement — that the current manuscript does not
support. They have been removed rather than restated.

## Layout

```
Manuscrit/          submission sources, figures, data and the built PDF
  submission/       one .tex per section, plus generated numbers and figures
  scripts/          the 90-instance study, extensions, figures, validation
Experimental/       the earlier full pipeline (P1-P6) and the lexpr library
enhanced/           decision-focused certification: Track A of the plan
Plan_for_Enhanced_Version.md   the research programme this work is scoped from
autoreview.md, autoreview_audit.md   self-review and its verifiable audit
```

## Reproduce

Python 3.10+ with `numpy`, `pandas`, `matplotlib`, `scipy`, `pytest`
(pinned in `Manuscrit/requirements.txt`), plus TeX Live for the PDF. There is no
`environment.yml` and no Conda environment is required.

```bash
pip install -r Manuscrit/requirements.txt
```

**The manuscript study** (90 instances, extensions, all figures, the PDF and the
validation report):

```bash
python Manuscrit/scripts/reproduce_submission.py
```

**The certification results** (Section 5 of the manuscript):

```bash
python enhanced/reproduce.py
cd Manuscrit && latexmk -pdf main.tex
```

`enhanced/reproduce.py` runs the tests, recomputes the three frozen rational
examples, runs the locked benchmark, builds the tables and figures, and writes
`Manuscrit/submission/generated_certrelex.tex`. The manuscript reads every
certification number from that file, so a missing or stale one fails the LaTeX
build rather than printing a stale figure. See `enhanced/README.md`.

**The earlier full pipeline**:

```bash
python Experimental/scripts/reproduce_all.py
```

Outputs land in `Experimental/manuscript/generated/`. Note that parts of the
legacy test suite still fail against the current API — several tests expect an
enclosure tuple where the engine now conservatively returns `None` for
unresolved retention, and one imports a removed symbol. That is recorded rather
than hidden; it is not a passing repository-wide suite.

## Licence

**No project-wide licence is currently declared.** The earlier README stated MIT,
but no `LICENSE` file exists in this repository, so that statement was not
effective. Choosing and adding a licence before public archival release is an
author-side action and is deliberately not made here. The bundled UCI Energy
Efficiency file keeps its separate CC BY 4.0 attribution and checksum
(`Manuscrit/submission/data/external/README.md`).

## Citation

```bibtex
@misc{bezoui2026archive,
  author    = {Bezoui, Madani},
  title     = {ReLexTail: Resolution-Aware Lexicographic Preorder},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.22558690},
  url       = {https://doi.org/10.5281/zenodo.22558690},
  version   = {v2.0.0},
  note      = {Earlier archive; the current manuscript supersedes its experiments}
}
```
