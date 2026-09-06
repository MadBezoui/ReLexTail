# Plan for an Enhanced Version: Certified, Decision-Focused Multicriteria Selection

**Planning date:** 6 September 2026  
**Project:** LexPR / ReLexTail  
**Deliverables:** a new method and its proofs, a reproducible benchmark and data release, validated software, and a submission-quality paper.  
**Status:** research proposal. New guarantees, originality and performance improvements below are hypotheses or proof obligations, not completed results.

## 1. Objective and the claim we should actually pursue

Develop a genuinely stronger contribution than another discretised ranking rule: **a decision-focused certification procedure that preserves dependencies in normalisation uncertainty, identifies which uncertainty can actually change the recommendation, and supports calibrated point recommendations with explicit abstention when evidence is inadequate.** Working name: **CertReLex**. This name is provisional and requires a collision search.

The ambition is to establish a new best documented trade-off between external decision regret, reliability, recommendation coverage and computational cost on a prespecified benchmark against the strongest applicable methods available by the literature cutoff. It is not scientifically defensible to promise a method that beats every MCDA approach under every preference model. Different methods solve different decision problems and optimise different objectives. Universal dominance is not the acceptance criterion.

A successful paper could claim:

> Under a fixed information and compute budget, dependency-preserving certification substantially increases the fraction of decisions certified relative to interval baselines. A separately calibrated recommendation policy improves external regret at matched coverage and meets a prespecified reliability target on held-out decision instances.

Every part of that sentence needs its own experiment. If only the first part succeeds, publish the algorithmic contribution without claiming superior decision quality. If neither succeeds, do not manufacture a superiority narrative.

**Literature cutoff:** material demonstrably public on or before 6 September 2026. This is not a review of the remainder of 2026. Repeat the search immediately before submission, recording first-online dates separately from issue dates.

## 2. Starting point: preserve what exists and resolve what remains weak

The current local protocol records 90 candidate sets, three synthetic families, criterion counts 3/6/10, 80 candidates per set, 10,000 evaluation weights, 500 matched perturbations per level, eight uncertainty levels and eight resolution widths. The current submission also has extension scripts for ablations, grid sensitivity and a public-data benchmark. These facts come from the files inspected for this plan, not the earlier conversation's smaller experiment.

Freeze this version as the **development baseline**, not the enhanced method's untouched test set. Previous inspection and tuning already make it unsuitable as final confirmatory evidence.

The remaining scientific opportunities are more consequential than increasing the number of perturbation draws:

| Weakness | Required improvement | Evidence needed |
|---|---|---|
| Independent interval bounds discard shared quantities | Bound the decisive comparison jointly | Tighter certified bounds at equal time, not merely more boxes |
| Global distance to any category boundary can be zero | Certify decision relevance rather than all coordinates | Examples where the global margin is zero but the winner is certified |
| Resolution and grid origin are discretionary | Separate elicited resolution from statistical policy tuning | Locked calibration protocol and origin sensitivity |
| Stable or large sets can make methods look artificially good | Match recommendation coverage and shortlist size | Coverage–risk and set-size–regret curves |
| Uniform linear preferences favour a narrow evaluation | Evaluate several declared preference populations | Held-out linear, nonlinear and elicited preferences |
| A public feature table is not an operational decision study | Add measured repeated observations and real decision context | Provenance, criterion directions, uncertainty estimates and preferences |
| Legacy and submission code use different numerical conventions | Introduce a single explicit numerical contract | Rational reference tests and independent certificate replay |
| A theoretically available formulation is not a validated solver | Implement, benchmark and cross-check the claimed algorithm | Exact small-instance oracles and time-limited large-instance results |

Retain the corrected S7–S6 supplier contrast as an explanatory regression case. Do not reintroduce unsupported cycle frequencies, zero set-change claims or a single-coordinate margin presented as a global stability guarantee.

## 3. Literature map and novelty gate

Use the following as an initial shortlist, not as a completed systematic review. The linked publisher/proceedings or author-posted records were checked during planning. Some records were accessible only through their abstract or preview; full-text verification remains a work package.

| Research line | Initial source | Consequence for this project |
|---|---|---|
| Relative robustness with unknown criterion weights | Weber, **Relatively Robust Multicriteria Decisions** (online 2025), [Management Science](https://pubsonline.informs.org/doi/10.1287/mnsc.2025.00510) | Mandatory recent comparator. Its native relative-performance guarantee must be reported separately from our range-normalised regret. |
| Approximate lexicographic fairness and noise sensitivity | Henzinger et al., **Leximax Approximations and Representative Cohort Selection** (2022), [FORC proceedings](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.FORC.2022.2) | Do not portray all approximate lexicographic approaches as nontransitive pairwise tolerances. Compare a precise applicable definition. |
| Earlier lexicographic robustness | **Lexicographic α-robustness: An alternative to min–max criteria** (2012), [EJOR](https://www.sciencedirect.com/science/article/abs/pii/S037722171200094X) | Fixed categories plus worst-first aggregation are not enough to establish novelty. |
| Modern MCDA positioning | **Fifty years of multiple criteria decision analysis: From classical methods to robust ordinal regression** (2025 issue), [EJOR record](https://www.sciencedirect.com/science/article/pii/S0377221724005988) | Position recommendation development and elicitation correctly; use the review to locate primary methods. |
| Sensitivity to the chosen robustness objective | **The Best of Many Robustness Criteria in Decision Making: Formulation and Application to Robust Pricing**, [author preprint](https://arxiv.org/abs/2403.12260) | Test several external objectives and do not optimise the benchmark around a favoured regret definition. Verify publication status before citation. |
| Recent regret-driven elicitation | **Geometric Preference Elicitation for Minimax Regret Optimization in Uncertainty Matroids** (2025 preprint), [author record](https://arxiv.org/abs/2503.18668) | Relevant to an optional interactive extension; its matroid-specific setting is not automatically a directly applicable baseline. |
| Ordered optimisation foundations | Ogryczak and Śliwiński (2003), [ordered weighted averaging LPs](https://www.sciencedirect.com/science/article/pii/S0377221702003995) | Reuse established formulations; identify exactly what the new certificate changes. |
| Public multiobjective model-selection benchmarking | Pfisterer et al., **YAHPO Gym** (2022), [AutoML proceedings](https://proceedings.mlr.press/v188/pfisterer22a.html) | Useful supplementary surrogate benchmark, explicitly distinguished from fresh measured outcomes. |

### Required search and comparison artefacts

Create `literature/search_log.csv`, `literature/evidence_matrix.csv`, and `literature/novelty_memo.md`. Search combinations of normalisation/normalization uncertainty, robust ordinal regression, necessary/possible winners, relative regret, approximate leximax, selective decision making, certified robustness, parametric optimisation, and preference elicitation. Search primary publications through EJOR, JMCDA, Management Science, Operations Research, relevant optimisation journals, proceedings and author preprints. Follow both backward and forward citations.

For each relevant work record the decision domain, input information, assumptions, uncertainty model, output type, exact guarantee, complexity, executable implementation and publication status. A missing experiment in another paper is not evidence that its method lacks a property. An unavailable implementation is not a losing baseline.

**Novelty gate:** before a large benchmark run, identify one theorem or algorithmic result not already supplied by the closest work under equivalent assumptions. Document a direct reduction if the proposal is equivalent to an existing method. If it is equivalent, reposition or redesign it. Neither this preliminary search nor a new acronym establishes originality.

## 4. Proposed original contribution

### 4.1 Core contribution: certify the decision, not every intermediate coordinate

The current sufficient stability condition requires all candidate risk coordinates to remain within their categories. That can fail for an irrelevant alternative, an invariant boundary coordinate, or a coordinate occurring after an already decisive comparison. The new algorithm should instead certify that the nominal winner beats each relevant rival throughout the uncertainty set, allowing irrelevant categories and orderings to change.

For a fixed candidate set A, probe multiset Q, resolution vector δ and grid convention, let Ψ(x;b) be the complete ReLexTail profile at bounds b. For a unique nominal winner x₀ define:

\[
\mathcal R_{x_0}=\{b:\Psi(x_0;b)<_{\rm lex}\Psi(y;b)\ \text{for every }y\ne x_0\}.
\]

The primary computational object is a certified inner region for this decision region, together with explicit counterexample bounds when available. For nested uncertainty sets B(r), define

\[
\rho^*(x_0)=\sup\{r:B(r)\subseteq\mathcal R_{x_0}\}.
\]

An empty qualifying set is reported as “no unique-winner certificate,” not silently converted into positive stability. Tied nominal optima require a separately defined set-preservation contract.

Return a lower certified radius and, where a verified counterexample exists, an upper witness radius. Budget exhaustion leaves a bracket or an unresolved result. A discovered switch can bound the unique-winner radius even if the alternative only ties x₀, depending on the declared contract.

### 4.2 Preserve algebraic dependence before branching

Use these identities as starting points, not as novel theorems in themselves:

1. **Singleton cancellation.** Active-range singleton disappointments do not depend on admissible criterion bounds. Enclose their numerical evaluation once; never repeatedly branch to resolve a nonexistent bound dependence.
2. **Shared-anchor cancellation in pairwise differences.** For a retained probe,

\[
D_q(x;b)-D_q(y;b)=\frac{q(r(x;b))-q(r(y;b))}{q^w(b)-q^\star(b)}.
\]

The shared best anchor cancels. Bound this expression jointly where useful instead of subtracting two independently widened disappointment intervals. This identity alone does not solve comparisons of sorted tails or prove a global lexicographic sign.
3. **Equivalent parameterisations.** Write rᵢ=aᵢfᵢ+cᵢ. A mean probe's active normalisation cancels its common intercept; common positive scaling of its slopes also cancels. For the grand maximum, a common additive shift and common positive scaling cancel after active normalisation. Derive the appropriate shared quotient representation and its actual image of B. Do not replace a correlated transformed domain by an unjustified independent box or assert a dimension reduction before proving it.
4. **Decision-relevant branches.** Refine only unresolved rival comparisons and the category, anchor or tail-membership boundaries that could reverse them. Cache structural equalities and already proved prefix relations.

Investigate rational polyhedral constraints where active branches are fixed, affine arithmetic, McCormick relaxations for remaining products/ratios, and exact rational interval subdivision as a fallback. General ratios and changing active sets are not automatically an LP or MILP. Report global relaxation gaps and unresolved cases honestly.

### 4.3 Output contract and policy extension

The certificate engine takes a declared rule; it must not change winners in order to appear more stable. On fixed inputs, old and new engines should agree on the underlying selection. Their comparison is about soundness, tightness and computation.

A **separate** policy layer may choose among a finite, prespecified collection of resolutions using development and calibration data. This changes the decision procedure and must be labelled as such. Keep an elicited-resolution mode for decision makers who choose meaningful widths directly.

The policy returns one of:

- a point with a verified decision-preservation certificate over the declared box;
- a possible-winner enclosure or bounded shortlist with explicit unresolved status;
- an abstention/request for more information.

A certificate that x is a ReLexTail winner is not a guarantee of small regret for an unknown person. External-regret calibration is a separate statistical claim. A shortlist cannot be scored as if an oracle subsequently chooses its best element unless the protocol actually gives the decision maker that additional information and counts its cost.

### 4.4 Optional calibration guarantee with explicit assumptions

For a finite library of L policies fixed before calibration, let a calibration episode include an independent decision problem and a prespecified realised evaluation loss. Define bounded indicators for point emission and for emission with external regret above ε. Simultaneously bound their population means using a finite-family concentration bound, splitting the error probability across policies and both quantities.

For policy θ, let U_bad(θ) be an upper bound on the bad-emission probability and L_emit(θ)>0 a lower bound on emission probability. Then

\[
P(\text{regret}>\varepsilon\mid\text{point emitted})
\le U_{\rm bad}(\theta)/L_{\rm emit}(\theta)
\]

on the joint confidence event. Select only policies whose ratio meets the declared risk target and whose coverage lower bound meets the required coverage. Report infeasibility if none qualifies. Account explicitly for selecting among L policies; do not use an uncorrected post-selection interval.

This is a proposed application of established concentration tools, not a new concentration theorem. It requires independent/exchangeable decision episodes from the target population. Multiple perturbations of the same matrix are not independent calibration episodes. Simulation-only calibration supports only simulation-population claims. Arbitrary deployment shift, online optional stopping and subgroup-conditional guarantees require additional assumptions and methods; exclude them from the core paper.

## 5. Theory work package

| Result to establish | Required statement and verification | Failure response |
|---|---|---|
| Representation equivalence | Quotient transformations preserve all retained D values and the attainable parameter domain | Keep the original domain; retain cancellation only |
| Sound joint elimination | Every certified comparison holds throughout the stated box, including boundaries | Return unresolved; never add numerical tie tolerances to obtain a proof |
| Decision-focused stability | Certifies some cases excluded by the all-coordinate margin condition | Construct exact examples and characterise why the old condition is conservative |
| Strict computational improvement | Exhibit a family where dependency preservation provably tightens the old enclosure, or derive an output-sensitive complexity result | Present measured speed/tightness gains, without a complexity theorem |
| Anytime validity | Every interrupted run returns valid sets/radius bounds; continuation tightens the retained bracket | Store nested envelopes and all unresolved leaves explicitly |
| Finite convergence conditions | State positive-separation and retention assumptions; describe tie/boundary obstructions | Do not claim finite exact recovery in general |
| Numerical soundness | Outward arithmetic for primitive operations; exact category comparisons; replayable witnesses | Distinguish nominal approximate computation from certification |
| Calibrated emission, if retained | Simultaneous finite-library risk and coverage bounds under a stated episode model | Retain calibration as empirical selection only if the statistical claim cannot be supported |

Use an independent rational reference implementation for small finite problems. Test degenerate ranges, equality at cell endpoints, one-ULP differences, repeated criteria/probes, persistent ties, dominated alternatives, empty retained families, extreme units, changing active anchors and uncertainty boxes crossing observations.

The current snapping convention is an operational numerical rule. Do not reuse its eight-epsilon snapping as an exact-real certificate. Either certify exact rational categories of the stored input values or formalise and certify the operational snapped rule as a different mathematical object.

## 6. Data programme

### 6.1 Controlled synthetic benchmark

Create six development families: simplex, spherical, convex, disconnected, correlated/redundant, and asymmetric-scale. Use m in {3, 6, 10, 20}, N in {50, 200}, and 25 independent matrices per family/m/N cell: **1,200 matrices**.

Within each cell, assign 10 matrices to development, five to calibration and ten to locked in-distribution testing: 480/240/480. Keep all perturbations and derivative cases from a matrix in its partition. Add two entirely unseen stress families, such as narrow-margin boundary constructions and correlated heavy-tailed measurement scenarios, with the same 200-matrix family budget: **400 additional locked out-of-distribution matrices**. These stress families test extrapolation; they do not establish calibration validity under arbitrary shift.

Add a separate exact-oracle suite of 100–200 small, rational, deliberately difficult problems. Add a scaling suite at N up to 10,000 and m up to 50 only after feasibility profiling. No claim requires exhaustively crossing every large N with every other factor.

Use 200 shared perturbations per level in the main experiment; increase only when pilot Monte Carlo precision justifies it. Prefer more independent problems to thousands of highly correlated draws on the same few matrices. Test range-relative boxes, correlated ellipsoidal or polyhedral uncertainty, biased bounds and explicit misspecification. Keep the certified domain matched to the actual uncertainty model.

### 6.2 External preference populations

Prespecify at least these populations: uniform Dirichlet-linear, sparse/extreme linear weights, concentrated unequal weights, monotone piecewise-linear utility, and a monotone interaction/Choquet model with valid capacities. Include an elicited preference population if available.

Define a comparable bounded regret within each utility model and document its sign and zero-range handling. Do not use observed test winners to select a utility family or normalisation. Evaluate mean regret, upper-25% and upper-10% regret, and worst-case regret when an exact or bounded oracle is available. Keep simulated preferences explicitly distinct from human preferences.

### 6.3 Public and measured data

Target three contexts with different uncertainty sources:

| Context | Data route | Decision and measurement requirements |
|---|---|---|
| Product choice | Existing UCI benchmark; optionally [UCI Automobile](https://archive-beta.ics.uci.edu/dataset/10/automobile) | Declare credible criterion directions and missing-data treatment. Historical specifications are not repeated uncertainty measurements or elicited choices. |
| Model deployment | Repeated measured accuracy, inference latency, memory and energy for a fixed set of model configurations on several tasks | Split tasks before calibration; fix hardware and timing conditions; record repeated runs and uncertainty. Use YAHPO only as a labelled surrogate supplement. |
| Operational procurement or engineering | Partner-provided or openly licensed decision matrices with repeated observations/assessor intervals | Obtain actual alternatives, meaningful uncertainty and documented decision requirements. If unavailable, report this as missing field validation rather than fabricate a realistic case. |

Aim for at least 30 independent decision episodes across at least two genuinely measured contexts; final numbers depend on access and the pilot precision analysis. Multiple shortlists cut from the same underlying dataset are correlated and must be grouped as such. They are not 30 independent domains.

If a human study is pursued, define an informed-consent and ethics process before collecting responses, preregister a counterbalanced comparison, pilot comprehension, and justify the final participant count by power or precision. Measure decision regret against later choices only where that interpretation is defensible; also measure comprehension, task time, consistency and willingness to accept a recommendation. Do not assume that the author's preferred supplier is ground truth.

### 6.4 Dataset and provenance contract

Each episode stores `instance_id`, parent/source group, split, stable candidate identifiers, criterion names/directions/units, raw observations, preprocessing, nominal bounds, uncertainty model, probe definitions/multiplicities, preferences where available, missingness flags, random seeds, source URL/DOI, licence and checksum.

Release raw data where permitted and deterministic reconstruction scripts otherwise. Freeze a split manifest and checksums before the final runs. Retain all excluded records with explicit exclusion reasons. Never silently delete an instance because the method abstains, times out or loses.

## 7. Baselines and fair comparisons

Maintain three distinct comparison tracks.

**Track A — fixed-rule certification:** current independent interval engine, the proposed joint engine, naive dense sampling labelled noncertifying, and a suitable general global optimiser/SMT or exact enumeration reference for small cases. Same nominal rule, probes, domain, arithmetic contract and hardware. This isolates the algorithmic contribution.

**Track B — decision quality with equal information:** exact LexPR, original fixed-resolution ReLexTail, calibrated ReLexTail without the new certificate, raw-criterion leximax, mean/OWA or spectral aggregation, standard weighted sum/TOPSIS/VIKOR with declared parameters, minimax regret over the same admissible preference set, SMAA under a declared common prior, and Weber's relatively robust method. Include applicable approximate leximax and robust ordinal regression variants after the novelty review. Native method assumptions must be respected, especially benefit/cost transformations and meaningful baselines for performance ratios.

**Track C — recommendation policies:** competing methods receive the same calibration budget and an equivalent abstention mechanism where mathematically possible. Compare at equal point coverage, shortlist size and wall-clock budget. An uncertified method is not assigned a fictitious zero risk or fictitious certificate failure.

Use published implementations when available. Validate reimplementations against paper examples and small exact instances. Report unsupported/problem-incompatible cases separately. Parameter tuning uses only development data and identical search budgets. If a method needs preferences not supplied to others, either supply equivalent information to all or put it in a separate information track. Human-query methods require a query-budget comparison, not the zero-query leaderboard.

## 8. Experiments, metrics and decision gates

| Experiment | Question | Primary outputs |
|---|---|---|
| E0: numerical correctness | Can any emitted certificate be falsified by an exact oracle? | Violations, witnesses, replay success and unresolved cases |
| E1: mechanism | Does joint dependence handling tighten the decisive comparisons? | Pairwise enclosure widths, resolved rivals, pruned cells and exact adversarial examples |
| E2: fixed-budget certification | Does the new engine certify more for the same resources? | Certified instance fraction, time to certificate, radius-bracket width, unresolved volume |
| E3: held-out decision quality | Does the full policy improve the external trade-off? | Regret at matched coverage and compute; point/set metrics reported separately |
| E4: calibration | Are risk/coverage guarantees operationally useful? | Observed selective risk, interval bounds, coverage, infeasible calibration frequency |
| E5: robustness | What fails with grid shifts, dependence, misspecification or duplicated probes? | Degradation curves and mechanism-specific failures |
| E6: measured external data | Do improvements transfer beyond generated fronts? | Dataset-level paired effects, uncertainty provenance and domain limitations |
| E7: scale and interruption | Is the method practical and honestly anytime? | Runtime, memory, solver gap, timeout/censoring and certificate progression |
| E8: human interpretation, optional | Do explanations help a real decision maker? | Comprehension, time, confidence calibration and query cost |

### Mandatory ablations

Remove singleton cancellation, joint anchor handling, decision-relevant branching and certificate reuse one at a time. Compare global-margin versus decision-focused certification. Compare fixed versus calibrated resolution, category-only versus full refinement, point-only versus abstaining outputs, and fixed versus shifted origins. For the calibration component, test the same calibration wrapper on strong competing methods. Add a “more compute, old engine” control.

### Statistical analysis

The independent unit is the decision instance or source dataset, not each perturbation. Use paired hierarchical/bootstrap or suitable mixed-effect analyses with source grouping. Prespecify primary contrasts and apply Holm correction within that family; label exploratory comparisons. Publish effect sizes and intervals, not only significance or rank diagrams. Include timeouts in the denominator and treat time-to-certificate as censored rather than dropping failures.

Report each real dataset separately before aggregation. Lock practical noninferiority margins using domain meaning and pilot information; do not choose them after observing final results. Estimate sample size from pilot between-instance variability, independent of the eventual locked test.

### Ambitious success targets — targets, not results

1. **Correctness:** zero false certificates on all exact-oracle cases; replay all certificates. Testing supplements, rather than substitutes for, a soundness proof.
2. **Certification:** target a 20 percentage-point increase in certified instances at equal budget, or a threefold median speed-up to the same certificate, over the old engine on the prespecified difficult population.
3. **Decision quality:** target at least a 5% relative reduction in external upper-tail regret against the strongest applicable baseline selected without test leakage, at matched coverage. Require the paired interval to exclude zero and practical noninferiority on the other primary criterion. Near-zero baseline regret requires an absolute-effect analysis instead.
4. **Reliability:** target at most 5% selective violation probability at a prespecified coverage target of 80%, subject to enough independent calibration data. If the bound cannot support that coverage, report the lower achievable coverage.
5. **External evidence:** improvements should reproduce on at least two independent measured contexts; otherwise narrow the application claim.

Do not require every target to publish, but make the title, abstract and claims match the gates actually passed. “Best on the prespecified benchmark under these conditions” is acceptable; “beats all literature” is not a supported conclusion.

## 9. Software, reproducibility and compute

Build the enhanced version in a separate `enhanced/` tree and preserve the current manuscript outputs.

```text
enhanced/
  protocol/              preregistration, splits, baseline and claim registry
  literature/            search log, evidence matrix, novelty memo
  data/{raw,processed}/  immutable observations and generated matrices
  src/                   reference order, geometry, certificates, calibration
  baselines/             version-pinned adapters and reference cases
  tests/                 exact oracles, numerical and replay checks
  configs/               development, calibration, locked test, scaling
  results/               append-only instance results and certificates
  analysis/              paired analysis and generated tables
  manuscript/            paper, proofs, figures and submission assets
  reproduce.py
  environment.lock
  MANIFEST.sha256
```

Resolve legacy API mismatches before relying on a repository-wide green test badge. Specify separately the reference mathematical rule, floating-point selector, certification arithmetic and witness verifier. Make the verifier simpler than the search code and independent of its heuristic decisions. Record solver versions, tolerances, threads, hardware, memory, time limits and random streams.

Use resumable per-instance jobs, common random numbers and cached evaluation losses. Keep calibration and test runs in separate directories with immutable configuration hashes. Generate every number in the manuscript from result files; the build must fail on stale/missing data, unresolved citations or figure/table mismatches.

Start with a 20-instance feasibility pilot and measure costs. Provisionally reserve 200–500 CPU-hours for pilot/method development and 2,000–5,000 CPU-hours for the main study, revising the estimate from profiling before committing resources. Exact small-instance verification has its own budget. Measured model-deployment data may require 50–200 GPU-hours depending on the selected models; choose the task suite first and cap it explicitly. These are planning estimates, not approved spending or hardware reservations.

## 10. Paper design

**Provisional title:** *Decision-Focused Certification for Resolution-Aware Multicriteria Selection under Uncertain Normalisation*.

A second title mentioning calibrated recommendations is justified only if that component adds a validated contribution rather than expanding the scope without sufficient evidence.

Organise the paper into six main sections:

1. Decision problem, relevant literature and a precise statement of the unresolved gap.
2. Declared rule, uncertainty model, numerical contract and output semantics.
3. Dependency-preserving certification, proofs and failure conditions.
4. Algorithms, optional calibration policy and reproducible implementation.
5. Preregistered experiments, measured data, ablations and negative results.
6. Decision-aiding interpretation, limitations and conclusions.

Keep the most important proofs in the paper. Put detailed oracle constructions, complete protocols and exhaustive tables in a versioned reproducibility archive or supplementary material where the target journal permits it. Do not hide assumptions or missing validation in the supplement.

Plan 10–12 substantive figures: motivating false global-margin case; original versus joint enclosure geometry; algorithm and certificate flow; exact-oracle validation; fixed-budget certification frontier; matched-coverage regret frontier; calibration risk–coverage curve; component ablations; family/dataset effects; measured decision case; runtime/censoring; failure map. Use vector figures, accessible colours, uncertainty intervals and captions specifying independent sample units. Do not add decorative figures to meet a count.

Build a claim-to-evidence table before drafting the abstract. Label each entry proved, measured, conditional, unresolved or disproved. Add explicit data/software availability, licences, CRediT, funding, conflicts and AI-assistance disclosure. Draft the cover letter around the verified contribution and appropriate scope, not a superiority slogan.

JMCDA remains a suitable target for a decision-aiding contribution with a clear practical interpretation. A change of venue should depend on the completed contribution, not substitute for fixing weak evidence. Recheck the target's current author guidelines at submission.

## 11. Work plan, ownership and stop rules

The indicative schedule assumes one lead researcher, engineering support for implementation/data work, and an independent methods reviewer. These are proposed roles, not assignments to people or delegated tasks.

| Stage | Indicative time | Owner role | Deliverable and gate |
|---|---|---|---|
| W0: freeze and audit | Week 1 | Lead + engineer | Baseline snapshot, numerical contract, known-failure inventory |
| W1: literature and originality | Weeks 1–2 | Lead + methods reviewer | Evidence matrix and defensible novelty memo; redesign if equivalent |
| W2: exact prototype and theory | Weeks 2–4 | Methods lead | Joint-comparison prototype, exact examples and soundness proof draft |
| W3: data and evaluation protocol | Weeks 2–5 | Data/engineering lead | Licensed sources, split manifest, measured-data feasibility and preregistration |
| W4: pilot and power/compute analysis | Weeks 4–5 | Lead + statistician/reviewer | 20-instance pilot, runtime budget, locked primary contrasts and margins |
| W5: implementation and ablations | Weeks 5–7 | Engineer + methods lead | Verified search engine and independent replay; validated baselines |
| W6: calibration and locked experiments | Weeks 7–9 | Engineer | Frozen policies, final result registry; no test-driven retuning |
| W7: external-data analysis | Weeks 8–10 | Lead + domain collaborator | Grouped external effects and documented limitations |
| W8: paper and adversarial review | Weeks 10–12 | Lead + independent reviewer | Complete manuscript, claim audit, clean reproduction and release candidate |

Human-subject or partner-data collection may take longer and must not be compressed into this schedule by assumption. Begin access work early; do not make the core mathematical paper contingent on an unconfirmed partner.

**Stop or narrow the project when:** the purported new representation is already known; a certificate fails an exact counterexample; the prototype gains only by changing the target rule; improvements vanish against an equally calibrated baseline; apparent gains come only from abstaining more; field data lack meaningful uncertainty; or the held-out effect is absent. After a failed confirmatory test, a redesigned method requires a new untouched test set.

## 12. Immediate next actions and definition of completion

The next implementation sequence is deliberately small:

1. Freeze the current code/data/manuscript and create the evidence and claim registries.
2. Obtain and read the closest primary papers, especially relatively robust decisions, approximate leximax and lexicographic α-robustness.
3. Construct three rational examples: invariant boundary coordinate, cancellation-induced interval slack, and a true winner switch with a verifiable witness.
4. Implement the smallest dependency-preserving pairwise certificate and compare it to the old engine on 20 unseen development cases.
5. Decide whether the improvement supports a new theorem, an algorithmic paper, or neither before scaling the benchmark.
6. Finalise datasets, grouping, utility families, baselines and compute caps; then preregister and freeze the confirmatory split.

The full project is complete only when the claimed new result survives the novelty review, every certificate is replayable, the relevant proofs and numerical tests agree, the final comparisons obey equal-information/coverage/budget contracts, real-data limitations are explicit, the public artefact reproduces all paper claims, and the author has approved the submission and declarations.

**Deliver a stronger scientific result, not a guaranteed winning story.** The plan's originality lies in the proposed decision-focused, dependency-preserving certificate and its carefully separated recommendation policy. Whether that originality and superiority are realised is what the project must establish.
