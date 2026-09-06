# Journal of Multi-Criteria Decision Analysis — submission revision

The manuscript is `Manuscrit/main.pdf`. It includes seven numbered sections, proofs, paired numerical comparisons, a claim-to-evidence register, declarations, APA author–date references and a complete figure-legends list. The original manuscript is preserved locally as `submission/original_main.pdf` and `submission/original_main.tex`.

Section 5, *Decision-focused certification*, and its three figures are produced by a separate tree, `enhanced/`, which implements Track A of `Plan_for_Enhanced_Version.md`. It does not change the decision rule: on fixed inputs its engine and `Experimental/code/lexpr/certified.py` select the same alternative. Every number that section prints is read from `submission/generated_certrelex.tex`, which `enhanced/analysis/make_macros.py` writes from `enhanced/results/`. If that file is missing or stale the LaTeX build fails on an undefined control sequence, by design.

```sh
python enhanced/reproduce.py     # tests, examples, experiments, tables, figures, macros
cd Manuscrit && latexmk -pdf main.tex
```

`enhanced/protocol/` holds the numerical contract, the preregistered splits, arms and contrasts, and the claim registry. `enhanced/literature/` holds the search log, evidence matrix and novelty memo, including an explicit record that full-text verification of the closest work is still outstanding.

## Reproduce this revision

From the repository root, with Python 3.10+ and NumPy, pandas, Matplotlib, SciPy, plus TeX Live (`latexmk`, `pdflatex`, BibTeX, apacite):

```sh
python Manuscrit/scripts/reproduce_submission.py
```

This command generates the 90-instance experiment, grid-origin and representation extensions, the UCI benchmark, the separate six-candidate interval illustration, all 12 figures, numerical tables, the PDF and the validation report. It requires no network access after the supplied CC BY 4.0 UCI file is present, commercial solver, trained surrogate or API credential. The authoring environment used Python 3.10 and TeX Live. All results have fixed seeds; bit-for-bit PDF equality is not expected across TeX/font versions.

For a fast rebuild from the supplied observations:

```sh
python Manuscrit/scripts/submission_figures.py
cd Manuscrit
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

`submission/data/protocol.json` records the design and study-script hash. `study.csv` contains 10,800 instance/method/level summaries from 90 instances, 15 methods and eight perturbation levels; every summary averages 500 matched bound draws. `candidates.npz` contains all candidate matrices and perturbation directions. Held-out weights are regenerated from the specified instance streams. `grid_sensitivity.csv`, `ablation.csv` and `decisive_coordinates.csv` record the extensions. `uci_benchmark.json` records the public-data filtering and results; `data/external/README.md` records source, licence and checksum. `certification.json` records processed budgets, inner/outer sets and unresolved volume. `validation.json` records targeted checks. The comparison and effect tables are regenerated from the same observations as the figures.

## What changed scientifically

The initial manuscript mixed incompatible empirical populations and protocols. The revised paper replaces its unsupported 500-instance/ReLexTail performance claims with a new explicitly identified 90-instance controlled study. It does not relabel the old data as new results. It removes unsupported cycle frequencies, claims of zero category-set changes, and unverified continuous-MILP runtime/accuracy claims. The latter are replaced by a theoretical stage-count figure.

The supplier winner remains S7, but the nearest rival is S6. They tie at maximum category 40; the decisive upper-25% tail categories are 36 and 38. The previously reported 0.0121 is a one-sided distance for a single score, not the global category-stability margin. The global sufficient margin is zero on this instance. Fixed external criterion bounds alone do not eliminate candidate-set dependence of active probe anchors. LexPR is also correctly distinguished from merely removing the categorical prefix of ReLexTail.

All previous figures have been rebuilt or replaced with evidence-matched counterparts. Additional illustrations show resolution cells, the distinction between probe-tail and preference-tail risk, paired effects by generator family, grid-origin sensitivity, ablations, decisive coordinates and the public benchmark. Figure 1 also serves as the graphical abstract. `figure_manifest.csv` maps revised artwork to its numerical source.

## Files for submission

- Main manuscript: `Manuscrit/main.pdf`.
- LaTeX sources and bibliography: `Manuscrit/main.tex`, `Manuscrit/refs.bib`, and `Manuscrit/submission/*.tex`.
- Separate vector artwork: `Manuscrit/submission/figures/*.pdf`.
- Caption text for uploads: `Manuscrit/submission/figure_legends.txt`.
- Cover letter: `Manuscrit/submission/cover_letter.txt`.
- Complete source/data archive: `Manuscrit/JMCDA_submission.zip`.

## Author actions before transmission

Approve the revised scientific scope and the author contribution, funding, competing-interest and AI-assistance declarations. Confirm that the manuscript is original and not under consideration elsewhere before making those declarations in the journal portal. Publish the new source/data package through an appropriate repository and update the data-availability statement with the resulting version-specific DOI. The earlier DOI resolves to a prior archive, so the enlarged experiments must not be represented as part of that unchanged release. No article or message has been sent to the journal and no release has been published.

The repository does not currently declare a project-wide software/manuscript licence. Choose and add an appropriate licence before public archival release; this revision does not assign one on the author's behalf. The bundled UCI file retains its separate CC BY 4.0 attribution.

## Validation scope

The new submission pipeline has dedicated checks for dataset completeness, paired metrics, exact-rational profile comparison, exact-rational corner containment including singleton probes, certification budgets, grid and ablation designs, UCI checksum and Pareto counts, supplier ranking, figure count and LaTeX diagnostics. The dedicated numerical-convention tests also check boundary snapping, shifted origins, stable identifiers, paired effects, Holm adjustment and Pareto filtering. The existing legacy tests still expose a separate API mismatch: several expect an enclosure tuple where the legacy API conservatively returns `None` for unresolved retention, and one imports the removed `leximax_argmin` symbol. Those failures are not presented as a passing repository-wide suite. The submission interval driver handles unresolved boxes conservatively and additionally encloses singleton arithmetic and computes certification profiles in rational arithmetic.

## Journal requirements consulted

The journal's author guidelines are recorded verbatim in `guidlesJMCDA.md` at the repository root, and Wiley's LaTeX template guide is `WileyDesign/Author-guidelines for LaTex Template_Wiley (2026).pdf`. Both were used to build the submission package; the live Wiley page returns HTTP 403 to automated requests and was not re-fetched.

Requirements that shaped the package: Research Articles have **no word limit** and a **300-word unstructured abstract** with a **Data Availability Statement**; up to seven keywords; a short running title under 40 characters; **ORCID is required**; **CRediT is mandated**; references in **APA** style; figures and supporting information supplied as **separate files**, with figure legends both beneath each uploaded image and as a **complete list in the text**; funding listed **in the Acknowledgments**; and the journal expects **data sharing**, with data cited per Wiley's data citation policy. Peer review is **single-blind**, so the main document carries the author's name and affiliation and no anonymised variant is prepared. Open access is chosen **after acceptance**.

## Wiley template version

`python Manuscrit/scripts/build_wiley_version.py` recasts the manuscript into Wiley's own authoring template (`USG.cls`, `APA` option) and writes `Manuscrit/wiley/`, which compiles with XeLaTeX. That build drops the local page furniture the class owns, uses the class's theorem environments, expands the generated certification macros into literals, moves the declarations into the class's backmatter commands, and emits the in-text figure-legend list. It blanks two marks the class hardcodes — the specimen journal's cover strip and an OPEN ACCESS badge — because neither is true of this submission; the class file itself is not modified.

`python Manuscrit/scripts/build_jmcda_package.py` runs that recast, refreshes the reproducibility archive, and assembles `Manuscrit/JMCDA_package/` with one file per portal upload slot.
