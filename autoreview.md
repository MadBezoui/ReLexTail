
# Comprehensive Revision Plan for ReLexTail

## Executive recommendation

The paper already has a sound mathematical core. The strongest enhancement strategy is **not** to add more isolated theorems, but to strengthen four areas:

1. **Positioning:** demonstrate precisely how ReLexTail differs from threshold-based MCDA, OWA/CVaR aggregation, exact leximax, SMAA and robust ordinal regression.
2. **Resolution elicitation:** turn \(\delta\) from an externally selected experimental parameter into an auditable decision-modelling parameter.
3. **Empirical validation:** add ablations, uncertainty intervals, grid-origin sensitivity, runtime evidence and at least one non-synthetic benchmark/application.
4. **Reproducibility:** publish the exact manuscript-specific code and data under a versioned DOI.

I recommend the following structure and work packages.

---

# 1. Revised paper structure

## Proposed structure

### 1. Introduction

- Decision problem and motivation.
- Why exact lexicographic minimax can overreact to negligible differences.
- Why ordinary pairwise tolerances may be nontransitive.
- Main idea of fixed resolution cells followed by exact refinement.
- Explicit distinction between:
  - \(W_{\mathrm{cat}}\): resolution-level recommendation set;
  - \(W_{\mathrm{exact}}\): fully refined optimal class;
  - deterministic identifier tie-breaking.
- Contributions in bullet form.

### 2. Related work and positioning

- Preference-based multiobjective optimisation.
- Ordered aggregation, OWA, CVaR and leximax.
- Threshold-based MCDA.
- Robustness to uncertain inputs and normalisation.
- SMAA and robust ordinal regression.
- Explainability and auditability.
- Comparison table with checkmarks/crossmarks.

### 3. ReLexTail representation and decision rule

- Criteria and normalisation.
- Probe construction and retention.
- Active-range disappointment.
- Tail means.
- Resolution categories.
- Category-optimal and exact-optimal sets.
- Contrastive explanation records.

### 4. Resolution elicitation and sensitivity

A new full section should be introduced here:

- interpretation of \(\delta\);
- elicitation protocol;
- common versus coordinate-specific widths;
- grid-origin sensitivity;
- statistical or data-informed calibration;
- reporting requirements.

### 5. Mathematical properties

- Existence and complete preorder.
- Positional anonymity.
- Strict profile monotonicity.
- Pareto compatibility.
- Uniform replication invariance.
- Category stability.
- New short proposition on monotonic nesting of category partitions as \(\delta\) changes—if valid only under restricted grid alignment, state those restrictions.
- Exact-refinement fragility.

### 6. Finite computation and robustness under uncertain bounds

- Finite-set algorithm.
- Sampling interpretation.
- Possible and necessary winners.
- Interval elimination.
- Branch-and-bound algorithm.
- Soundness versus tightness.

### 7. Continuous polyhedral formulation

- Anchor computation.
- Four category stages.
- Exact tail refinements.
- Ordered-sum refinements.
- Solver tolerances.
- Explicit limitation: theoretical characterisation without a fully validated end-to-end implementation.

### 8. Experimental design

- Synthetic instances.
- Public real/engineering datasets.
- Compared methods.
- Ablation variants.
- Resolution and grid-shift design.
- Perturbation levels.
- Evaluation measures.
- Statistical analysis.
- Computational environment.

### 9. Results

- Quality–stability trade-off.
- Statistical uncertainty.
- Geometry- and dimension-specific results.
- Probe-family ablation.
- Grid-origin sensitivity.
- Real-data results.
- Runtime/scalability.
- Interval-certification performance.

### 10. Supplier decision and practical reporting

- Supplier data.
- Resolution elicitation example.
- Category and exact recommendation.
- Contrastive explanation.
- Uncertain-bound sensitivity.
- Decision dashboard.

### 11. Discussion, limitations and real-world validation roadmap

### 12. Conclusion

---

# 2. Revised contribution statement

The contribution statement should be concise and defensible. I recommend replacing broad novelty language with the following.

> This paper makes six contributions. First, it defines a complete and transitive preorder that prioritises fixed-resolution categories of maximum and upper-tail probe disappointments before applying exact refinements. Second, it distinguishes the resolution-level category-optimal set from the fully refined optimal class. Third, it establishes finite-set existence, strict profile monotonicity, conditional criterion-level Pareto compatibility and invariance to uniform replication of the declared probe multiset. Fourth, it provides a sufficient local condition for category stability while explicitly showing why this condition does not imply stability of the fully refined point. Fifth, it develops sound interval-based candidate elimination under fixed probe retention and positive normalisation denominators. Sixth, it evaluates the resulting quality–stability trade-off through matched perturbations, ablations and reproducible synthetic and application-oriented experiments.

## Recommended highlights with checkmarks

The journal highlights could be:

- ✓ Fixed resolution cells avoid nontransitive pairwise tolerance relations.
- ✓ Maximum and upper-tail probe disappointments are prioritised before exact refinement.
- ✓ Category-optimal and fully refined recommendations are reported separately.
- ✓ The preorder is complete, transitive and conditionally Pareto-compatible.
- ✓ Uniform replication of the complete probe multiset leaves comparisons unchanged.
- ✓ Uncertain normalisation bounds are studied through matched sampling and sound interval elimination.
- ✓ The quality–stability trade-off is evaluated with paired statistical comparisons.
- ✗ ReLexTail does not remove the need to elicit probes, multiplicities or resolution widths.
- ✗ Category stability does not imply stability of the fully refined recommendation.
- ✗ Sampling does not certify the complete possible-winner set.
- ✗ The present continuous MILP formulation is not yet an independently validated solver implementation.

The crossmarks are valuable: they show methodological honesty and prevent exaggerated claims.

---

# 3. New related-work section

## 3.1 Recommended comparison table

Use a table of methodological capabilities, not a claim that one method is universally superior.

### Table: Positioning of ReLexTail relative to related decision rules

| Family                           | Explicit preference model | Transitive fixed-resolution cells | Upper-tail aggregation across concerns | Complete final preorder | Uncertain-normalisation analysis | Possible/necessary winner analysis | LP/MILP characterisation | Contrastive audit record |
| -------------------------------- | ------------------------: | --------------------------------: | -------------------------------------: | ----------------------: | -------------------------------: | ---------------------------------: | -----------------------: | -----------------------: |
| Weighted sum                     |                        ✓ |                                ✗ |                                     ✗ |                     ✓* |                               ✗ |                                 ✗ |                       ✓ |                       △ |
| Reference-point/distance methods |                        ✓ |                                △ |                                     ✗ |                     ✓* |                               ✗ |                                 ✗ |                       △ |                       △ |
| OWA/ordered median               |                        ✓ |                                ✗ |                                     ✓ |                     ✓* |                               ✗ |                                 ✗ |                       ✓ |                       △ |
| Empirical CVaR minimisation      |                        ✓ |                                ✗ |                                     ✓ |                     ✓* |                               △ |                                 ✗ |                       ✓ |                       △ |
| Exact leximax/LexPR              |                        ✓ |                                ✗ |                                     ✗ |                      ✓ |                               △ |                                 ✗ |                       ✓ |                       ✓ |
| ELECTRE-type threshold methods   |                        ✓ |                              ✓** |                                     ✗ |                   ✗*** |                               △ |                                 ✗ |                       ✗ |                       ✓ |
| SMAA                             |                        ✓ |                                ✗ |                                     △ |                      ✗ |                               △ |                   ✓ probabilistic |                       ✗ |                       ✓ |
| Robust ordinal regression        |                        ✓ |                                ✗ |                                     ✗ |                      ✗ |                               △ |                         ✓ logical |                       △ |                       ✓ |
| ReLexTail                        |                        ✓ |                                ✓ |                                     ✓ |                      ✓ |                               ✓ |        ✓ under stated assumptions |           ✓ theoretical |                       ✓ |

**Legend**

- ✓: integral to the standard formulation;
- ✗: not generally provided;
- △: possible through an extension or implementation-dependent;
- \(*\): complete up to numerical ties;
- \(**\): thresholds are available, but they do not generally define the same fixed-cell equivalence relation;
- \(***\): outranking relations may be incomplete or nontransitive.

Add this caution below the table:

> The table describes structural capabilities, not empirical superiority. A checkmark does not imply that a method is preferable for every decision context.

## 3.2 Text explaining the gap

A suitable positioning paragraph is:

> ReLexTail lies between strict lexicographic optimisation and threshold-based decision aiding. Unlike exact leximax, it does not give every sub-resolution maximum difference immediate priority. Unlike pairwise indifference thresholds, its fixed cells induce a transitive category-equality relation. Unlike a pure OWA or CVaR score, it retains a declared noncompensatory hierarchy across the maximum and several tail levels. Unlike SMAA and robust ordinal regression, uncertainty is placed primarily on the normalisation bounds while the declared preference rule remains fixed. Exact refinement ultimately yields a complete preorder, but the category-optimal set remains available as the resolution-level decision output.

---

# 4. Practical elicitation of the resolution parameter

This must become a dedicated subsection, not only one paragraph in the conclusion.

## 4.1 Interpretation

Explain that \(\delta_\ell\) is:

- not a solver tolerance;
- not a confidence level;
- not an uncertainty radius;
- not directly a percentage of the physical criterion;
- a category width on the active-range disappointment scale.

For a probe \(q\), a width of \(0.02\) means 2% of the active probe range:

\[
R_q=q^w-q^\star.
\]

It does **not** necessarily mean 2% of price, delivery time or emissions.

## 4.2 Recommended elicitation protocol

### Step 1 — Present concrete candidate pairs

Show the decision-maker pairs differing by controlled amounts in:

- maximum disappointment;
- worst 25% tail;
- worst 50% tail;
- mean disappointment.

### Step 2 — Find a just-noticeable decision difference

For each risk coordinate \(R_\ell\), ask:

> What is the smallest difference in this summary that should be allowed to override all later coordinates?

Use a sequence such as:

\[
0.005,\ 0.01,\ 0.02,\ 0.03,\ 0.05,\ 0.075,\ 0.10.
\]

### Step 3 — Convert physical differences where possible

If a probe corresponds to a physical criterion, show the corresponding physical-scale change:

\[
\Delta q \approx \delta_\ell R_q.
\]

For aggregate probes, show several representative candidate-specific examples because the physical interpretation may not be unique.

### Step 4 — Check consistency

Repeat selected pairwise questions in reverse order and after a delay. Report:

- within-session consistency;
- test–retest agreement;
- width interval rather than only one point estimate.

### Step 5 — Choose a robust width region

Do not select one \(\delta\) only because it gives the most favourable experimental result. Identify a range in which:

- the nominal \(W_{\mathrm{cat}}\) is stable;
- the point recommendation is reasonably stable;
- external regret does not deteriorate materially;
- the recommendation remains interpretable.

### Step 6 — Conduct grid-shift sensitivity

For category origin \(o_\ell\), investigate:

\[
B_(z)
=====

\left\lceil \frac{z-o}{\delta}\right\rceil,
\]

with an explicit convention for \(z\le o\). Suggested offsets are:

\[
o\in\left\{0,\frac{\delta}{4},\frac{\delta}{2},
\frac{3\delta}{4}\right\}.
\]

The original zero-anchored grid remains the primary model; shifted grids are sensitivity diagnostics.

## 4.3 Practical guidance for choosing 0.02 versus 0.05

Add a table such as:

| Diagnostic                                                                     | Prefer\(\delta=0.02\) | Prefer\(\delta=0.05\) |
| ------------------------------------------------------------------------------ | --------------------- | --------------------- |
| Decision-maker discriminates small changes reliably                            | ✓                    | ✗                    |
| Measurement/normalisation precision is high                                    | ✓                    | ✗                    |
| Avoiding large category-optimal sets is important                              | ✓                    | ✗                    |
| Broader-tail compensation within maximum cells is desired                      | △                    | ✓                    |
| Small boundary movements are common                                            | ✓/△                 | △                    |
| Decision is high-stakes and exact refinement must remain informative           | ✓                    | △                    |
| Decision-maker explicitly regards 2–5% active-range differences as negligible | ✗                    | ✓                    |

The choice must ultimately be based on elicited meaning, not on whichever width gives the best benchmark result.

---

# 5. Additional figures

The paper already has 11 figures. Adding six or more without restructuring could make it excessively long. I recommend adding **eight new figures**, while moving some existing methodological illustrations to supplementary material.

## New Figure 12 — Resolution elicitation curve

**Content:** For each risk coordinate, plot the proportion of decision-maker judgments declaring two values meaningfully different against the active-range difference.

**Axes**

- \(x\): absolute difference in risk coordinate;
- \(y\): proportion of “meaningfully different” responses.

**Output:** Estimated transition region and proposed \(\delta_M,\delta_{25},\delta_{50},\delta_{100}\).

**Purpose:** Gives a practical basis for choosing \(\delta=0.02\) versus \(0.05\).

---

## New Figure 13 — Resolution–grid-origin sensitivity heatmap

**Content:** Heatmaps over:

- resolution width \(\delta\);
- grid shift \(o/\delta\).

Panels should report:

1. point-change rate;
2. category-set change rate;
3. upper-tail external regret;
4. mean size of \(W_{\mathrm{cat}}\).

**Purpose:** Directly addresses fixed-boundary sensitivity.

---

## New Figure 14 — Paired instance-level effect distributions

Use violin, box, or raincloud plots for:

\[
\Delta_}
========

\mathrm_}
---------

\mathrm{ChangeRate}_{\mathrm{LexPR}},
\]

and

\[
\Delta_}
========

\mathrm_}
---------

\mathrm{TailRegret}_{\mathrm{LexPR}}.
\]

Show:

- all 90 paired instance effects;
- pooled mean;
- median;
- 95% paired-bootstrap interval;
- zero reference line.

**Purpose:** Prevents the pooled average from hiding heterogeneous effects.

---

## New Figure 15 — Quality–stability Pareto map across all \(p\) and \(\delta\)

Each point represents one method–parameter combination.

- \(x\): point-change rate;
- \(y\): upper-tail regret;
- colour: perturbation level \(p\);
- symbol: method;
- line or hull: empirically nondominated configurations.

**Purpose:** Shows that no single resolution is universally best and identifies dominated settings.

---

## New Figure 16 — Probe influence and decisive-coordinate decomposition

For each method/instance, classify the decisive comparison as:

- maximum category;
- 25% tail category;
- 50% tail category;
- mean category;
- exact 25% tail;
- exact 50% tail;
- exact mean;
- exact maximum;
- terminal order statistic.

Display a stacked bar by:

- geometry;
- number of criteria;
- perturbation level.

Add a second panel reporting whether the decisive coordinate was driven by:

- an invariant singleton probe;
- the mean probe;
- the maximum probe.

**Purpose:** Explains how uncertain bounds actually influence the recommendation.

---

## New Figure 17 — Ablation study

Compare:

1. LexPR;
2. categories on maximum only;
3. categories on maximum and \(T_{25}\);
4. full four-category ReLexTail;
5. full categories without exact refinement—report \(W_{\mathrm{cat}}\);
6. full ReLexTail;
7. ReLexTail without singleton probes;
8. ReLexTail with rebalanced singleton/aggregate multiplicities.

Plot point changes, category-set changes, regret and set size.

**Purpose:** Demonstrates which components produce the observed trade-off.

---

## New Figure 18 — Interval-certification convergence

For each uncertainty level and multiple instances, plot against:

- processed boxes;
- wall-clock time.

Report:

- unresolved volume;
- outer possible-winner set size;
- inner possible-winner set size;
- fraction of instances completely resolved.

Use median curves and interquartile bands across instances.

**Purpose:** Converts the current one-instance illustration into a transparent computational assessment.

---

## New Figure 19 — Continuous-formulation runtime and verification

If the MILP implementation is completed, report:

- runtime versus \(m\);
- runtime versus number of constraints/variables;
- number of solver stages;
- agreement between direct finite enumeration and sequential optimisation on instances where both apply;
- effect of feasibility and integrality tolerances.

If the implementation is **not** completed, do not include simulated runtime data. Instead retain the theoretical stage-count figure and explicitly describe implementation as future work.

---

## New Figure 20 — Practical decision dashboard

For the supplier or real application, provide one dashboard containing:

- \(W_{\mathrm{cat}}\);
- \(W_{\mathrm{exact}}\);
- decisive coordinate against every rival;
- labelled probe disappointments;
- sampled winner frequencies;
- certified inner/outer sets;
- unresolved volume;
- sensitivity to \(\delta\);
- sensitivity to grid shift.

**Purpose:** Demonstrates the claimed auditability of ReLexTail.

---

# 6. Additional tables

## Table A — Related-work capability matrix

Use the checkmark/crossmark table proposed above.

## Table B — Resolution elicitation record

| Coordinate  | Physical interpretation    | Tested active-range differences | Elicited discrimination interval | Selected width | Rationale |
| ----------- | -------------------------- | ------------------------------: | -------------------------------: | -------------: | --------- |
| \(M\)       | Worst declared concern     |                              … |                               … |             … | …        |
| \(T_{25}\)  | Mean of worst 25% concerns |                              … |                               … |             … | …        |
| \(T_{50}\)  | Mean of worst 50% concerns |                              … |                               … |             … | …        |
| \(T_{100}\) | Overall mean concern       |                              … |                               … |             … | …        |

For the constructed supplier example, label these as analyst-declared, not stakeholder-elicited.

## Table C — Full paired statistical comparison

Add:

- mean and median regret;
- upper-tail regret;
- point-change rate;
- category-set change rate;
- category-set size;
- nominal-point retention;
- Jaccard overlap;
- paired differences from LexPR;
- 95% paired-bootstrap intervals;
- probability of superiority.

## Table D — Ablation results

Report the components listed for Figure 17.

## Table E — Real/public dataset description

| Dataset                 | Nature                  | Candidates | Criteria | Criterion direction                     | Bound uncertainty source     | Stakeholders        |
| ----------------------- | ----------------------- | ---------: | -------: | --------------------------------------- | ---------------------------- | ------------------- |
| Procurement case        | Operational             |         … |       … | …                                      | estimation/contract ranges   | procurement experts |
| Portfolio benchmark     | Historical market data  |         … |       … | risk/cost minimise, return maximise     | estimation window            | none                |
| Concrete mixtures       | Laboratory observations |         … |       … | cost/impact minimise, strength maximise | measurement/reference bounds | none                |
| Building energy designs | Engineering simulations |         … |       … | heating/cooling minimise                | reference-range uncertainty  | none                |

Do not label simulated building data as field data.

## Table F — Computational certification results

Include runtime, boxes, set sizes, unresolved volume and retention status.

---

# 7. Real comparison data

## 7.1 What can already be reported from the manuscript

The following comparisons are genuine calculations from the current Table 1. Relative percentages below are approximate because they are calculated from rounded published values.

| Method                     | Tail regret | Difference from LexPR | Relative tail-regret difference | Point changes | Point-change difference from LexPR |
| -------------------------- | ----------: | --------------------: | ------------------------------: | ------------: | ---------------------------------: |
| LexPR                      |      0.5430 |                     0 |                              0% |        21.11% |                               0 pp |
| Leximax                    |      0.5337 |              −0.0093 |                         −1.71% |        35.59% |                          +14.48 pp |
| Mean-D                     |      0.5490 |               +0.0060 |                          +1.10% |        29.78% |                           +8.67 pp |
| ReLexTail,\(\delta=0.001\) |      0.5430 |                0.0000 |                           0.00% |        20.96% |                          −0.15 pp |
| ReLexTail,\(\delta=0.01\)  |      0.5421 |              −0.0009 |                         −0.17% |        20.11% |                          −1.00 pp |
| ReLexTail,\(\delta=0.02\)  |      0.5414 |              −0.0016 |                         −0.29% |        19.07% |                          −2.04 pp |
| ReLexTail,\(\delta=0.05\)  |      0.5408 |              −0.0022 |                         −0.41% |        21.22% |                           +0.11 pp |
| ReLexTail,\(\delta=0.10\)  |      0.5406 |              −0.0024 |                         −0.44% |        24.22% |                           +3.11 pp |

A careful interpretation is:

- \(\delta=0.02\) reduces point changes by approximately **2.04 percentage points**, or **9.7% relative to the LexPR change rate**.
- Its external upper-tail regret decreases by approximately **0.0016**, or **0.29% relative**.
- Larger \(\delta\) values continue to reduce the reported tail regret but lose the point-stability advantage.
- Leximax gives the strongest tail-regret result but substantially worse point stability.
- Mean-D optimises a different aspect: it has the best mean regret but worse upper-tail regret than LexPR.

These are real manuscript results, but the new paper should compute all differences from the unrounded per-instance files.

## 7.2 Required new comparison data

Increase the perturbation draws from 30 to at least **500 per instance and uncertainty level**. Thirty draws are sufficient for an exploratory population average but weak for estimating instance-specific switching probabilities.

Recommended design:

- 90 original synthetic instances;
- at least 500 matched perturbations per \(p\);
- \(p\in\{0.01,0.025,0.05,0.10,0.15,0.20,0.30,0.40\}\);
- \(\delta\in\{0.001,0.005,0.01,0.02,0.03,0.05,0.075,0.10\}\);
- grid offsets \(o/\delta\in\{0,0.25,0.50,0.75\}\);
- at least 10,000 held-out preference vectors;
- all random draws shared across methods.

## 7.3 Baselines to add

At minimum compare against:

1. exact LexPR;
2. exact leximax on normalised criteria;
3. Mean-D;
4. minimisation of \(T_{25}\) alone;
5. minimisation of \(T_{50}\) alone;
6. an OWA profile approximating the selected tail priorities;
7. weighted sum under the mean elicited/evaluation weights;
8. reference-point or achievement-scalarising method;
9. category-only selection reporting \(W_{\mathrm{cat}}\);
10. a threshold-based outranking method, if a defensible threshold specification is available.

Do not force a comparison with methods operating under fundamentally different preference information unless the modelling assumptions are made equivalent.

## 7.4 Statistical analysis

For each paired comparison report:

- paired mean difference;
- paired median difference;
- 95% percentile or BCa bootstrap interval;
- probability that ReLexTail improves the metric;
- Wilcoxon signed-rank test as supplementary information;
- Holm correction across the predeclared primary comparisons;
- geometry and criterion-count interaction;
- number of wins, losses and ties.

Define two primary endpoints before rerunning:

1. point-change-rate difference versus LexPR;
2. upper-tail external-regret difference versus LexPR.

Treat all other resolutions and subgroup analyses as secondary or exploratory.

---

# 8. Real-world validation strategy

## 8.1 Minimum publication enhancement

If a true operational study cannot be completed before publication, add one public-data experiment and clearly label it as an application-oriented benchmark rather than stakeholder validation.

Possible public-data domains include:

- portfolio selection using real historical asset returns;
- experimental concrete-mixture designs;
- vehicle or transport alternatives with observed cost/emission/performance data;
- energy-system technology alternatives;
- published supplier-selection data with explicit reuse permission.

For benefit criteria, transform them to minimisation form transparently, for example:

\[
f_i(x)=-g_i(x),
\]

or use a declared monotone decreasing conversion. Do not silently invert criteria.

## 8.2 Stronger prospective validation

A proper real procurement validation should involve:

- one or more procurement organisations;
- 15–30 actual suppliers or bids;
- 6–12 operational criteria;
- explicit documentation of measurement uncertainty;
- 5–15 stakeholders;
- elicitation of probes and \(\delta\);
- comparison with the organisation’s current decision process;
- repeated elicitation to assess stability;
- qualitative evaluation of explanation usefulness.

Suggested endpoints:

- recommendation agreement;
- top-set overlap;
- stakeholder acceptance;
- confidence in the recommendation;
- explanation time;
- number of preference revisions;
- test–retest stability;
- disagreement resolution;
- integration effort with procurement software.

Because this involves human participants and potentially commercially sensitive data, the study may require informed consent, data governance and an ethics determination.

---

# 9. New 2025–2026 references

The following recent records were verified through publisher/Crossref metadata. They should be cited only where substantively discussed.

## Robustness and stability in MCDA

1. **Paradowski, B., Wątróbski, J., & Sałabun, W. (2025).** “Novel coefficients for improved robustness in multi-criteria decision analysis.” *Artificial Intelligence Review*.https://doi.org/10.1007/s10462-025-11307-6**Use:** robustness measures and sensitivity reporting.
2. **Jangid, P., Kumar, T., Jahnvi, Dhanuk, K., & Sharma, M. K. (2025).** “A stability and robustness analysis of multi-criteria decision methods in logistics.” *Decision Analytics Journal*, article 100618.https://doi.org/10.1016/j.dajour.2025.100618**Use:** stability comparisons in application-oriented MCDA.
3. **Patel, G., Das, S., & Das, R. (2025).** “Evaluation of optimal normalization techniques in multi-criteria decision-making to rank CMIP6 climate models.” *Theoretical and Applied Climatology*.https://doi.org/10.1007/s00704-025-05617-6**Use:** empirical importance of normalisation choices.
4. **Gopisetty, Y. B., Sama, H. R., Padi, T. R., & Patibandla, L. (2025).** “A Double Normalization Framework for Sustainable Electric Vehicle Selection: Integrating LOPCOW and RAM in Multi-Criteria Decision-Making.” *Journal of the Operations Research Society of China*.
   https://doi.org/10.1007/s40305-025-00626-8
   **Use:** recent normalisation methodology; contrast with uncertain normalisation bounds.

## Preference elicitation and explainability

5. **Escamocher, G., Pourkhajouei, S., Toffano, F., Viappiani, P., & Wilson, N. (2025).** “Interactive preference elicitation under noisy preference models: An efficient non-Bayesian approach.” *International Journal of Approximate Reasoning*, article 109333.https://doi.org/10.1016/j.ijar.2024.109333**Use:** eliciting preferences under response noise.
6. **Huber, F., Rojas Gonzalez, S., & Astudillo, R. (2025).** “Bayesian Preference Elicitation for Decision Support in Multi-Objective Optimization.” *Journal of Multi-Criteria Decision Analysis*.https://doi.org/10.1002/mcda.70019**Use:** modern preference-elicitation positioning.
7. **Erwig, M., & Kumar, P. (2025).** “Explaining Results of Multi-Criteria Decision-Making.” *Journal of Multi-Criteria Decision Analysis*.https://doi.org/10.1002/mcda.70011**Use:** contrastive records and auditability.
8. **Więckowski, J., & Sałabun, W. (2025).** “Supporting multi-criteria decision-making processes with unknown criteria weights.” *Engineering Applications of Artificial Intelligence*, article 109699.https://doi.org/10.1016/j.engappai.2024.109699**Use:** uncertainty about criteria weights versus uncertainty about normalisation.
9. **Shi, C., & Yao, Y. (2025).** “Explainable multi-criteria decision-making: A three-way decision perspective.” *International Journal of Approximate Reasoning*, article 109528.https://doi.org/10.1016/j.ijar.2025.109528**Use:** explainability and set-valued decisions.
10. **Zhao, L., Wang, P., Shen, J., Song, B., & Zhang, Q. (2026).** “Component-Sharing Preference in Expensive Multiobjective Optimization.” *IEEE Transactions on Evolutionary Computation*.https://doi.org/10.1109/TEVC.2025.3583302**Use:** preference-informed multiobjective optimisation.
11. **Schwind, N., Everaere, P., Konieczny, S., & Lonca, E. (2026).** “Targeting in Multi-Criteria Decision Making.” *Proceedings of the AAAI Conference on Artificial Intelligence*, 40(43), 36732–36739.
    https://doi.org/10.1609/aaai.v40i43.40998
    **Use:** recent axiomatic treatment of alternative selection in MCDA.

## Robust and risk-aware optimisation

12. **Kuhn, D., Shafiee, S., & Wiesemann, W. (2025).** “Distributionally robust optimization.” *Acta Numerica*.https://doi.org/10.1017/S0962492924000084**Use:** distinguish bound uncertainty from distributional uncertainty.
13. **Blanchet, J., Li, J., Lin, S., & Zhang, X. (2025).** “Distributionally Robust Optimization and Robust Statistics.” *Statistical Science*, 40(3), 351–377.https://doi.org/10.1214/24-STS955**Use:** clarify different meanings of robustness.
14. **Garg, D., & Mehra, A. (2025).** “Portfolio optimization with expectile value at risk and conditional value at risk: deviation measure and robust allocation.” *Computational and Applied Mathematics*.https://doi.org/10.1007/s40314-025-03446-x**Use:** modern CVaR-based robust optimisation; distinguish decision-risk CVaR from empirical probe-tail summaries.
15. **Arao, S., Komiyama, H., Tsuruga, R., Amishima, T., Kakubari, Y., & Naganawa, J. (2026).** “Lexicographic Robust Receiver Placement Optimization for Airport Surface Multilateration Against Worst-Case Station Failure.” *IEICE Communications Express*.https://doi.org/10.23919/COMEX.2026XBL0017**Use:** contemporary lexicographic robust optimisation.
16. **Xue, J., Zheng, P., Wei, C., & Song, G. (2026).** “Robust Optimization Algorithm of Multi-Objective and Multi-Scenario Performance for Uncertain Microgrids Based on Lexicographic Order Method.” *Sustainability*, 18(2), 1100.https://doi.org/10.3390/su18021100**Use:** recent robust lexicographic multiobjective application.
17. **Pratiwi, Z., Zahedi, Z., & Nusantara, B. C. (2026).** “Study of novel normalization technique on weighting and ranking methodology in multi criteria decision making.” *Croatian Operational Research Review*.
    https://doi.org/10.17535/crorr.2026.0023
    **Use:** recent effects of normalisation on ranking.

## Directly relevant author publication

18. **Regaigui, S., Bezoui, M., Moulaï, M., & Qaisar, S. M. (2025).** “A memetic method for solving portfolio optimization problem under cardinality, quantity, and pre-assignment constraints.” *Applied Soft Computing*, 175, 113058.
    https://doi.org/10.1016/j.asoc.2025.113058
    **Use:** continuity with the author’s constrained multiobjective optimisation research.

This provides **18 recent 2025–2026 references**, exceeding the requested minimum of 16.

---

# 10. At least six relevant Madani Bezoui references

Self-citations must be scientifically justified. They should not be added merely to satisfy a numeric quota. The following works are the most defensible because they establish continuity in preference integration, multiobjective optimisation, scheduling and constrained portfolio optimisation.

1. **Regaigui, S., Bezoui, M., Moulaï, M., & Qaisar, S. M. (2025).** “A memetic method for solving portfolio optimization problem under cardinality, quantity, and pre-assignment constraints.” *Applied Soft Computing*, 175, 113058.https://doi.org/10.1016/j.asoc.2025.113058
2. **Bezoui, M., Olteanu, A.-L., & Sevaux, M. (2023).** “Integrating preferences within multiobjective flexible job shop scheduling.” *European Journal of Operational Research*, 305(3), 1079–1086.https://doi.org/10.1016/j.ejor.2022.07.002
3. **Bezoui, M., Moulaï, M., Bounceur, A., & Euler, R. (2019).** “An iterative method for solving a bi-objective constrained portfolio optimization problem.” *Computational Optimization and Applications*, 72(2), 479–498.https://doi.org/10.1007/s10589-018-0052-9
4. **Bezoui, M., Kermali, A., Bounceur, A., Qaisar, S. M., & Almaktoom, A. T. (2024).** “Deep Reinforcement Learning for Multiobjective Scheduling in Industry 5.0 Reconfigurable Manufacturing Systems.” In *Machine Learning for Networking*.https://doi.org/10.1007/978-3-031-59933-0_7
5. **Bezoui, M., Olteanu, A.-L., & Sevaux, M. (2022).** “Preference-driven tabu search for multiobjective scheduling problems.” 23rd ROADEF Congress.https://hal.science/hal-03587512
6. **Ibnelbey, R., & Bezoui, M. (2025).** “Preference-Based Multi-Objective Optimization for Student Transportation: A Machine Learning Approach.” ROADEF conference contribution.https://hal.science/hal-04974058
7. **Bezoui, M., Olteanu, A.-L., & Sevaux, M. (2021).** “Embedding decision-maker’s preferences in the multi-objective Tabu search method for scheduling problems.” EURO conference contribution.
   https://hal.science/hal-03285086

Suggested use:

- cite References 2, 5 and 7 when introducing preference integration;
- cite References 1 and 3 when discussing constrained multiobjective optimisation;
- cite Reference 4 when motivating Industry 5.0 applications;
- cite Reference 6 only in the future real-world/application outlook.

Do not present conference abstracts as equivalent to archival journal articles.

---

# 11. Mandatory bibliographic identity check

A metadata inconsistency must be resolved before publication.

The manuscript gives:

\[
\text{ORCID }0000\text{-}0002\text{-}8342\text{-}7039,
\]

while several HAL, Crossref and OpenAlex records associate Madani Bezoui with:

\[
0000\text{-}0001\text{-}6930\text{-}1088.
\]

Some newer records use the manuscript identifier. The author should verify which ORCID is correct and request metadata corrections or account merging where appropriate. The paper, repository, Zenodo archive, HAL profile and publisher submissions should use one validated identity consistently.

---

# 12. Exact additions requested by the reviewer

## 12.1 Resolution-parameter paragraph

Insert in a new subsection titled **“Practical elicitation of resolution widths”**:

> The resolution widths should not be selected solely by optimising retrospective stability. An analyst should first determine the smallest change in each risk summary that the decision-maker considers capable of overriding all later profile coordinates. This can be elicited through controlled pairwise comparisons in which the maximum or a tail mean is varied while the remaining summaries are held approximately constant. Candidate values such as 0.01, 0.02 and 0.05 should then be translated into percentages of each probe’s active range and illustrated using physical criterion values where possible. Because responses may identify an interval rather than a unique threshold, the analysis should report recommendations over a plausible width range. Nearby widths and shifted category grids should be examined as sensitivity diagnostics. Consequently, choosing between \(\delta=0.02\) and \(\delta=0.05\) is a modelling decision based on meaningful discrimination and acceptable set size, not a universal numerical prescription.

## 12.2 Abstract limitation for continuous MILP formulation

Add after the sentence about the sequential formulation:

> This formulation is a theoretical computational characterisation; an independently validated end-to-end continuous MILP implementation is not claimed in the present study.

This is transparent, but slightly weakens the abstract. If word count is strict, use:

> The continuous formulation is characterised theoretically but not yet validated through an end-to-end solver implementation.

## 12.3 Real-world validation outlook

Add to the conclusion:

> Future operational validation should combine real candidate and criterion data with live stakeholder elicitation of probes, multiplicities and resolution widths. Such a study should compare ReLexTail with the organisation’s current decision process, evaluate recommendation acceptance and test–retest stability, and integrate the comparison and sensitivity records into existing procurement or decision-support software. Where human judgments or commercially sensitive supplier data are collected, appropriate ethics, consent and data-governance procedures will be required.

---

# 13. Additional theoretical and technical improvements

## 13.1 Correct Proposition 1

Repair the corrupted proof as indicated in the review.

## 13.2 Correct Theorem 3

Use the retained separating-probe assumption directly rather than claiming that a specific singleton probe must separate the alternatives.

## 13.3 Clarify interval-vector evaluation

State that \(\Psi(D^U)\) is computed from a common upper disappointment vector.

## 13.4 Distinguish uncertainty sources

Add a table distinguishing:

| Uncertainty                     | Object varied                         | Current treatment           |
| ------------------------------- | ------------------------------------- | --------------------------- |
| Normalisation-bound uncertainty | \(z^\star,z^{\mathrm{nad}}\)          | Main robustness analysis    |
| Preference uncertainty          | probes, multiplicities, widths        | Sensitivity/elicitation     |
| Candidate-data uncertainty      | \(f_i(x)\)                            | Not generally modelled      |
| Candidate-set uncertainty       | membership of\(A\)                    | Not modelled                |
| Sampling uncertainty            | Monte Carlo estimates                 | Bootstrap/Monte Carlo       |
| Solver error                    | feasibility and optimality tolerances | Must be reported separately |

## 13.5 Add a numerical specification

The software/paper must document:

- treatment of \(\lceil z/\delta\rceil\);
- equality tolerance for exact profiles;
- stable sorting convention;
- tie-breaking;
- outward rounding;
- rational representation used in certification;
- solver feasibility and integrality tolerances.

---

# 14. Reproducibility package

The final archive should have the following structure:

```text
relextail-paper-version/
├── README.md
├── LICENSE
├── CITATION.cff
├── environment.yml
├── requirements-lock.txt
├── data/
│   ├── synthetic/
│   ├── real/
│   ├── supplier/
│   └── perturbation_directions/
├── src/
│   ├── probes/
│   ├── selection/
│   ├── intervals/
│   ├── optimization/
│   └── evaluation/
├── experiments/
│   ├── synthetic_protocol.yaml
│   ├── real_data_protocol.yaml
│   ├── ablation_protocol.yaml
│   └── grid_shift_protocol.yaml
├── results/
│   ├── raw/
│   └── summaries/
├── figures/
├── tables/
├── tests/
└── reproduce_all.sh
```

Required tests:

- singleton invariance;
- replication invariance;
- fractional-CVaR calculation;
- category-boundary convention;
- Pareto monotonicity;
- agreement between direct and sequential selection;
- interval-enclosure containment;
- deterministic seed replay.

Archive this exact version with a new DOI and cite that DOI in the paper.

---

# 15. Prioritised implementation checklist

## Priority 1 — Required before publication

- [ ] Repair Proposition 1 and Theorem 3 proofs.
- [ ] Add the related-work comparison table.
- [ ] Add a practical \(\delta\)-elicitation subsection.
- [ ] Add pooled confidence intervals for point-change differences.
- [ ] Explain floating-point category-boundary handling.
- [ ] Add the continuous-MILP limitation to the abstract or conclusion.
- [ ] Add the real-world validation paragraph.
- [ ] Archive the exact code and data used for this version.
- [ ] Resolve the apparent ORCID inconsistency.
- [ ] Verify every DOI against publisher metadata.

## Priority 2 — Strongly recommended

- [ ] Add grid-origin sensitivity.
- [ ] Add the probe/decisive-coordinate decomposition.
- [ ] Add an ablation study.
- [ ] Increase perturbations beyond 30 per instance.
- [ ] Report full paired distributions and stability intervals.
- [ ] Add one public-data application benchmark.
- [ ] Expand the interval experiment beyond one instance.

## Priority 3 — High-value extension

- [ ] Implement and validate the sequential LP/MILP formulation.
- [ ] Compare finite enumeration and continuous optimisation.
- [ ] Conduct a prospective stakeholder elicitation study.
- [ ] Integrate contrastive records into a procurement dashboard.
- [ ] Evaluate decision time, acceptance and test–retest stability.

---

# 16. Final target for the revised manuscript

The revised paper should make the following claim—and no stronger claim:

> ReLexTail is a complete, auditable and resolution-prioritised lexicographic selection rule. It provides a principled alternative to pairwise numerical tolerances by using fixed transitive cells, while retaining exact refinement when a complete recommendation is required. Its robustness benefits are conditional on the probe representation, category widths, grid placement and uncertainty model, and must therefore be supported by elicitation, sensitivity analysis and reproducible paired comparisons.

That positioning is rigorous, publishable and appropriately cautious.
