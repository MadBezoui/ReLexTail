Madani, I conducted a bibliographic and positioning audit of the manuscript as of **7 September 2026**. The main conclusion is clear:

> The existing references are mostly authentic and correctly used, but the bibliography is too narrow for a paper claiming a methodological contribution at the intersection of MCDA, lexicographic optimization, tail-risk aggregation, robustness, interval certification, and explainability.

One DOI is incorrect, one DOI contains a typographical error, several foundational streams are under-cited, and the 2025–2026 literature needs substantial reinforcement.

---

# 1. Audit of the references currently cited

## 1.1 Summary

The manuscript contains **17 references**.

| Result                                                                            |   Count |
| --------------------------------------------------------------------------------- | ------: |
| References whose identity and general metadata are verified                       |      17 |
| Incorrect DOI                                                                     |       1 |
| DOI containing a spacing/typographical defect                                     |       1 |
| References that are relevant but insufficient to support broad positioning claims | Several |
| Evidently fabricated references                                                   |       0 |

The strongest bibliographic defect is the DOI attached to Kostreva and Ogryczak (1999).

---

## 1.2 Reference-by-reference audit

| Reference                                            | Verification                                                                                                                                                        | Relevance and required action                                                                                                                                                                              |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Erwig & Kumar (2025)**                       | Verified:*Journal of Multi-Criteria Decision Analysis*, 32(1), e70011, DOI [10.1002/mcda.70011](https://doi.org/10.1002/mcda.70011).                               | Highly relevant to contrastive explanations and replay records. Retain. Explain that their framework targets score decomposition, whereas ReLexTail exposes the decisive coordinate of an ordered profile. |
| **Greco, Mousseau, & Słowiński (2008)**      | Verified:*EJOR*, 191(2), 416–436, DOI [10.1016/j.ejor.2007.08.013](https://doi.org/10.1016/j.ejor.2007.08.013).                                                   | Essential for Robust Ordinal Regression. Retain.                                                                                                                                                           |
| **Huber, Rojas Gonzalez, & Astudillo (2025)**  | Verified:*Journal of Multi-Criteria Decision Analysis*, 32(3), e70019, DOI [10.1002/mcda.70019](https://doi.org/10.1002/mcda.70019).                               | Highly relevant, but it concerns learned preference uncertainty, not normalization uncertainty. The distinction made in the manuscript is correct.                                                         |
| **Hwang & Yoon (1981)**                        | Verified. Book DOI[10.1007/978-3-642-48318-9](https://doi.org/10.1007/978-3-642-48318-9).                                                                            | Appropriate foundational citation for distance-based and multiple-attribute methods.                                                                                                                       |
| **Kostreva & Ogryczak (1999)**                 | Article verified, but the DOI in the manuscript is wrong.                                                                                                           | **Correct DOI:** [10.1051/ro:1999112](https://doi.org/10.1051/ro:1999112), not `10.1051/ro:1999118`. This must be corrected.                                                                        |
| **Kuhn, Shafiee, & Wiesemann (2025)**          | Verified:*Acta Numerica*, 34, 579–804, DOI [10.1017/S0962492924000084](https://doi.org/10.1017/S0962492924000084).                                                | Authoritative DRO review. Retain, but do not present DRO as a close competitor: it concerns ambiguity over probability laws, unlike a deterministic box of normalization bounds.                           |
| **Lahdelma, Hokkanen, & Salminen (1998)**      | Verified, DOI[10.1016/S0377-2217(97)00163-X](https://doi.org/10.1016/S0377-2217(97)00163-X).                                                                         | Retain. Remove the space currently appearing inside`S0377 -2217`.                                                                                                                                        |
| **Miettinen (1999)**                           | Verified. DOI[10.1007/978-1-4615-5563-6](https://doi.org/10.1007/978-1-4615-5563-6).                                                                                 | Appropriate foundational source for multiobjective optimization and preference articulation.                                                                                                               |
| **Ogryczak & Śliwiński (2003)**              | Verified:*EJOR*, 148(1), 80–91, DOI [10.1016/S0377-2217(02)00399-5](https://doi.org/10.1016/S0377-2217(02)00399-5).                                               | Directly relevant to ordered aggregation and linear formulations. Retain.                                                                                                                                  |
| **Ogryczak & Tamir (2003)**                    | Verified:*Information Processing Letters*, 85(3), 117–122, DOI [10.1016/S0020-0190(02)00370-8](https://doi.org/10.1016/S0020-0190(02)00370-8).                    | Directly supports sums-of-largest-functions formulations. Retain.                                                                                                                                          |
| **Paradowski, Wątróbski, & Sałabun (2025)** | Verified:*Artificial Intelligence Review*, 58, Article 298, DOI [10.1007/s10462-025-11307-6](https://doi.org/10.1007/s10462-025-11307-6).                          | Relevant to rank stability under perturbations. Retain, but distinguish empirical robustness coefficients from proof-oriented certification.                                                               |
| **Rockafellar & Uryasev (2000)**               | Verified:*Journal of Risk*, 2(3), 21–41, DOI [10.21314/JOR.2000.038](https://doi.org/10.21314/JOR.2000.038).                                                      | Essential. Clarify that the paper uses the upper-tail mass\(\alpha\), whereas standard CVaR notation often uses a confidence level.                                                                        |
| **Tervonen & Figueira (2008)**                 | Verified:*Journal of Multi-Criteria Decision Analysis*, 15(1–2), 1–14, DOI [10.1002/mcda.407](https://doi.org/10.1002/mcda.407).                                 | Appropriate SMAA survey. Retain.                                                                                                                                                                           |
| **Tsanas & Xifara (2012)**                     | Verified as a dataset: UCI Energy Efficiency, DOI[10.24432/C51307](https://doi.org/10.24432/C51307).                                                                 | The entry should explicitly include the document type**[Dataset]**, repository and version/access information if required by the journal.                                                                  |
| **Więckowski & Sałabun (2025)**              | Verified:*Engineering Applications of Artificial Intelligence*, 140, 109699, DOI [10.1016/j.engappai.2024.109699](https://doi.org/10.1016/j.engappai.2024.109699). | Relevant to unknown weights. Retain, while preserving the distinction from bound uncertainty.                                                                                                              |
| **Wierzbicki (1980)**                          | Verified, DOI[10.1007/978-3-642-48782-8_32](https://doi.org/10.1007/978-3-642-48782-8_32).                                                                           | Appropriate reference-point foundation.                                                                                                                                                                    |
| **Yager (1988)**                               | Verified:*IEEE Transactions on Systems, Man, and Cybernetics*, 18(1), 183–190, DOI [10.1109/21.87068](https://doi.org/10.1109/21.87068).                          | Essential OWA citation. Retain.                                                                                                                                                                            |

---

# 2. Important weaknesses in the current literature positioning

## 2.1 Missing direct citation for lexicographic minimax

The manuscript repeatedly invokes “exact lexicographic minimax” and introduces “LexPR”, but does not cite a direct treatment of lexicographic minimax. Add:

> Ogryczak, W. (1997). On the lexicographic minimax approach to location problems. *European Journal of Operational Research, 100*(3), 566–585. DOI: [10.1016/S0377-2217(96)00154-3](https://doi.org/10.1016/S0377-2217(96)00154-3).

This reference is more directly relevant than relying only on equitable optimization and OWA.

## 2.2 Missing interval-analysis foundation

Section 5 discusses dependency loss, shared anchors, outward rounding and interval enclosures. These are standard interval-analysis issues, but no foundational interval-analysis source is cited. Add:

> Moore, R. E., Kearfott, R. B., & Cloud, M. J. (2009). *Introduction to Interval Analysis*. SIAM. DOI: [10.1137/1.9780898717716](https://doi.org/10.1137/1.9780898717716).

The novelty claim should not be “dependency preservation is new”. The manuscript already avoids that claim. The contribution is its **specialization to the shared-anchor quotient and its decision-level empirical consequence**.

## 2.3 Insufficient coverage of contemporary MCDA

The current paragraph beginning “Recent work reinforces four adjacent needs” cites only four recent papers. This is too narrow to support a strong state-of-the-art positioning. In particular, it omits:

- the 2025 retrospective on 50 years of MCDA;
- recent work on relative robustness;
- recent explainable MCDA;
- recent combinations of probabilistic uncertainty and outranking;
- recent SMAA-based elicitation;
- recent exact anytime lexicographic enumeration;
- behavioural evidence concerning interactive multiobjective optimization.

## 2.4 “Tail regret” terminology needs stronger positioning

Inside the selection rule, \(T_\alpha\) aggregates **probe disappointments**, not decision regret against an alternative or state-dependent optimum. External regret is used only in the evaluation study.

Two solutions are possible:

1. retain “tail-regret” but state explicitly, near the first occurrence, that it is a named decision index built from normalized disappointments; or
2. use “tail-disappointment” for the internal profile and reserve “regret” for Equation (13).

The second option is terminologically cleaner.

## 2.5 The closest-literature claim remains unresolved

Table 6 honestly labels “Priority over the closest literature” as unestablished. This is scientifically prudent, but it also signals that the literature review is not yet submission-ready. The revised section below resolves much of this problem, but I recommend avoiding an absolute “first method” claim. Prefer:

> “We are not aware of prior work combining these components under the same deterministic preorder and certification contract.”

## 2.6 Author-identity metadata inconsistency

The manuscript gives the ORCID:

> `0000-0002-8342-7039`

This identifier appears in the recent IEEE and ACM metadata. However, some older Crossref records attributed to Madani Bezoui, including the 2025 *Applied Soft Computing* record, contain:

> `0000-0001-6930-1088`

This should be corrected at publisher/Crossref level if the latter is obsolete or erroneous. Otherwise, automated indexing may split the publication record. The current HAL profile confirms the relevant publication list, while the recent IEEE record uses `0000-0002-8342-7039` ([HAL profile](https://cv.hal.science/mbezoui); [IEEE/Crossref record](https://doi.org/10.1109/OJCS.2026.3681725)).

## 2.7 Reproducibility wording

The repository exists and documents the archive and commands ([GitHub repository](https://github.com/MadBezoui/ReLexTail)). However, its README also states that parts of the legacy test suite fail against the current API. Therefore, replace “complete replay package” by a more precise formulation unless a clean release test is provided:

> “The archive contains the data, scripts, current certification tests and documented reproduction commands; known failures in the legacy test suite are separately disclosed.”

---

# 3. Proposed “Related Work” section

The following section is written directly in English so that it can be inserted into the manuscript. It cites more than 15 works from 2025–2026 and incorporates six publications involving Madani Bezoui without presenting the peripheral ones as direct antecedents of ReLexTail.

---

## 2 Related work

### 2.1 Multicriteria recommendation and ordered profiles

Multiple-criteria decision analysis provides several conceptually different routes from a set of feasible or Pareto-efficient alternatives to a recommendation. Compensatory methods combine criterion evaluations through weighted scores, utility functions, distances or reference points, whereas noncompensatory and order-based methods emphasize the worst-performing coordinates or impose priorities between objectives (Hwang & Yoon, 1981; Wierzbicki, 1980; Miettinen, 1999). A recent retrospective by Greco, Słowiński, and Wallenius (2025) traces this development from classical aggregation methods to preference-disaggregation and robust ordinal-regression approaches. This broader perspective is important here because ReLexTail is not intended as a universally preferable aggregation method: it implements a declared priority structure over a multiset of interpretable concerns.

Ordered weighted averaging associates weights with ranked outcomes rather than named criteria (Yager, 1988). Related equitable-optimization models seek solutions that improve the least satisfactory components of an achievement vector (Kostreva & Ogryczak, 1999), while lexicographic minimax refines the comparison of ordered profiles by successively minimizing their worst components (Ogryczak, 1997). Linear representations of ordered weighted objectives and sums of the largest functions provide the computational basis for such models (Ogryczak & Śliwiński, 2003; Ogryczak & Tamir, 2003). Recent work on anytime lexicographic enumeration addresses a complementary problem: Foschini et al. (2026) generate the lexicographically best nondominated solutions progressively, whereas ReLexTail assumes a fixed candidate set and defines a single preorder that combines resolution categories, tail summaries and exact ordered-profile refinement.

The upper-tail summaries used by ReLexTail are instances of empirical CVaR-type functionals (Rockafellar & Uryasev, 2000). In the present setting, however, the empirical atoms are declared probe disappointments rather than realizations of a stochastic loss. This distinction separates the selection mechanism from distributionally robust optimization, where decisions are protected against ambiguity in the probability law governing uncertain outcomes (Kuhn, Shafiee, & Wiesemann, 2025). ReLexTail instead treats a deterministic box of uncertain normalization parameters and makes no distributional-robustness claim.

### 2.2 Preference uncertainty and normalization uncertainty

A major part of contemporary MCDA concerns incomplete, uncertain or interactively elicited preferences. Stochastic multicriteria acceptability analysis represents uncertainty over weights or evaluations through acceptability measures (Lahdelma, Hokkanen, & Salminen, 1998; Tervonen & Figueira, 2008). Robust ordinal regression derives necessary and possible preference relations from a set of value functions compatible with preference information (Greco, Mousseau, & Słowiński, 2008). More recently, Więckowski and Sałabun (2025) proposed support procedures for settings with unknown criterion weights, while Huber, Rojas Gonzalez, and Astudillo (2025) used a Bayesian utility model and informative pairwise queries to identify preferred Pareto solutions. Zhao et al. (2026) combine SMAA-2 and FITradeoff to reduce the interaction burden during pairwise elicitation.

These methods vary preference parameters, criterion weights or probabilistic evaluations. ReLexTail addresses a different uncertainty source: the preference rule, probe family and resolution grid are fixed, while the bounds used to normalize criterion values are allowed to vary within a prescribed box. Consequently, its possible and necessary winner sets resemble the quantifier structure used in SMAA and robust ordinal regression, but their semantics are different. A possible ReLexTail winner is supported by at least one admissible normalization vector, not by at least one compatible utility function or sampled weight vector.

Recent work also stresses that interactive elicitation is affected by behavioural and procedural choices. Halstead et al. (2026), for example, show that anchoring can prevent users from reaching their most preferred solution in interactive multiobjective optimization, especially when they decide on behalf of others. Such evidence reinforces the need to distinguish an explicitly declared deterministic rule from a claim of recovered or latent human preferences. ReLexTail provides the former; it does not claim that its cells or probes statistically identify a decision maker’s true utility function.

### 2.3 Robustness, sensitivity and certification

Sensitivity analysis typically measures how rankings change when weights, evaluations or method parameters are perturbed. Paradowski, Wątróbski, and Sałabun (2025) introduce rank-stability and balance-point coefficients for diagnosing the robustness of MCDM results. Jangid et al. (2025) similarly compare the stability of several MCDM methods under perturbations in a logistics setting. Weber (2026) takes a different optimization perspective and defines relatively robust multicriteria decisions through a worst-case performance ratio over admissible weights. Cebesoy, Tuncer Şakar, and Yet (2025) combine outranking methods with Bayesian networks to represent uncertain evaluations and communicate the resulting decision support.

These contributions illustrate that “robustness” does not denote a single mathematical property. It may refer to empirical rank stability, worst-case performance over weights, probabilistic acceptability, or invariance of a selected alternative over a parameter region. ReLexTail adopts the last interpretation. Its certification problem asks whether the same unique recommendation is produced for every normalization vector in a prescribed box. Random perturbation experiments provide sensitivity evidence but cannot establish this universal statement.

The interval component of ReLexTail follows the general principle that dependency loss can enlarge interval enclosures when repeated occurrences of a shared variable are treated independently (Moore, Kearfott, & Cloud, 2009). The specific shared quantities here are the best and worst probe anchors used by every candidate at a fixed bound vector. The contribution is therefore not a new principle of interval arithmetic, but a decision-focused specialization: the anchors are retained within a common quotient, and certification stops once the first lexicographically decisive profile coordinate separates the nominal winner from each rival. This differs from requiring every candidate and every risk coordinate to remain within its original resolution cell.

### 2.4 Explanation and auditability

Explanation has become an explicit concern in MCDA. Erwig and Kumar (2025) derive contrastive explanations from fine-grained representations of the computations performed by weighted and hierarchical decision methods. Shi and Yao (2025) propose an explainable MCDA framework based on three-way decisions. ReLexTail follows the same general objective of making a recommendation inspectable, but its explanation object is specific to its preorder: for each rival, it records the first coordinate at which the complete profile differs, the values being compared and, for categorical coordinates, the applicable resolution width. Such a record explains why a pairwise comparison is settled, while independent replay of all pairwise records establishes optimality over the finite candidate set.

Auditability is also distinct from statistical calibration. A deterministic replay can verify that the published recommendation follows from the declared candidates, probes, bounds and numerical conventions. It does not establish that the probes recover stakeholder preferences, that the selected candidate minimizes an external population loss, or that a certificate has a calibrated probability of correctness. These remain separate empirical questions.

### 2.5 Relation to the authors’ previous work

The present work also extends a broader research programme on preference-aware multiobjective optimization and decision-support tooling. Bezoui, Olteanu, and Sevaux (2023) integrated decision-maker preferences into multiobjective flexible job-shop scheduling, while Bezoui et al. (2024) examined hybrid metaheuristics for multiobjective manufacturing and supply-chain optimization in an Industry 5.0 context. Ibnelbey and Bezoui (2025) subsequently studied preference-based multiobjective optimization for student transportation, and Regaigui et al. (2025) developed a memetic method for portfolio optimization under cardinality, quantity and pre-assignment constraints. More recent contributions investigate similarity-weighted transfer for manufacturing optimization (Bezoui, Nouinou, & Bounceur, 2026) and a hardware–software decomposition architecture for scalable digital-twin systems (Bounceur et al., 2026).

These studies motivate the need for interpretable optimization and reproducible decision-support pipelines, but they are not direct antecedents of the ReLexTail preorder or its interval certificate. The closest methodological antecedent in this sequence is the preference-integration work of Bezoui, Olteanu, and Sevaux (2023); the portfolio, manufacturing and digital-twin contributions provide application and computational context rather than proofs of the present ordering or certification results.

### 2.6 Positioning of ReLexTail

ReLexTail combines established components—active-range normalization, ordered aggregation, empirical CVaR, fixed resolution cells, lexicographic refinement and interval enclosure—under a specific decision contract. Relative to exact lexicographic minimax, fixed cells postpone sub-resolution differences until broader tail categories have been compared. Relative to SMAA, Bayesian preference elicitation and robust ordinal regression, the preference rule is held fixed and uncertainty is assigned to normalization bounds. Relative to empirical robustness coefficients, the method produces a deterministic box certificate rather than a sensitivity score. Relative to explainable MCDA, it supplies a method-specific first-difference record and an independent replay path.

Accordingly, the contribution is not the invention of CVaR, ordered aggregation, lexicographic optimization or dependency-aware interval arithmetic. It is the construction and analysis of a resolution-aware preorder together with a decision-focused certificate that preserves the shared normalization structure. To our knowledge, the cited literature does not combine these elements under the same finite-set selection rule and exact certification contract; this statement should nevertheless be presented as a scoped literature-based assessment rather than as an unrestricted priority claim.

---

# 4. Recent references to add: 2025–2026

The following list contains **17 references from 2025–2026**. The six references involving Madani Bezoui are marked **†**.

## Directly relevant MCDA, robustness and preference literature

1. **Cebesoy, M., Tuncer Şakar, C., & Yet, B. (2025).** Multicriteria decision support under uncertainty: Combining outranking methods with Bayesian networks. *Annals of Operations Research, 355*(3), 2971–2998. [https://doi.org/10.1007/s10479-024-06064-8](https://doi.org/10.1007/s10479-024-06064-8)
2. **Erwig, M., & Kumar, P. (2025).** Explaining results of multi-criteria decision-making. *Journal of Multi-Criteria Decision Analysis, 32*(1), e70011. [https://doi.org/10.1002/mcda.70011](https://doi.org/10.1002/mcda.70011)
3. **Greco, S., Słowiński, R., & Wallenius, J. (2025).** Fifty years of multiple criteria decision analysis: From classical methods to robust ordinal regression. *European Journal of Operational Research, 323*(2), 351–377. [https://doi.org/10.1016/j.ejor.2024.07.038](https://doi.org/10.1016/j.ejor.2024.07.038)
4. **Huber, F., Rojas Gonzalez, S., & Astudillo, R. (2025).** Bayesian preference elicitation for decision support in multi-objective optimization. *Journal of Multi-Criteria Decision Analysis, 32*(3), e70019. [https://doi.org/10.1002/mcda.70019](https://doi.org/10.1002/mcda.70019)
5. **Jangid, P., Kumar, T., Jahnvi, Dhanuk, K., & Sharma, M. K. (2025).** A stability and robustness analysis of multi-criteria decision methods in logistics. *Decision Analytics Journal, 16*, 100618. [https://doi.org/10.1016/j.dajour.2025.100618](https://doi.org/10.1016/j.dajour.2025.100618)
6. **Kuhn, D., Shafiee, S., & Wiesemann, W. (2025).** Distributionally robust optimization. *Acta Numerica, 34*, 579–804. [https://doi.org/10.1017/S0962492924000084](https://doi.org/10.1017/S0962492924000084)
7. **Paradowski, B., Wątróbski, J., & Sałabun, W. (2025).** Novel coefficients for improved robustness in multi-criteria decision analysis. *Artificial Intelligence Review, 58*, Article 298. [https://doi.org/10.1007/s10462-025-11307-6](https://doi.org/10.1007/s10462-025-11307-6)
8. **Shi, C., & Yao, Y. (2025).** Explainable multi-criteria decision-making: A three-way decision perspective. *International Journal of Approximate Reasoning, 187*, 109528. [https://doi.org/10.1016/j.ijar.2025.109528](https://doi.org/10.1016/j.ijar.2025.109528)
9. **Więckowski, J., & Sałabun, W. (2025).** Supporting multi-criteria decision-making processes with unknown criteria weights. *Engineering Applications of Artificial Intelligence, 140*, 109699. [https://doi.org/10.1016/j.engappai.2024.109699](https://doi.org/10.1016/j.engappai.2024.109699)
10. **Foschini, M., Tsouros, D., Dilkina, B., & Guns, T. (2026).** Anytime lexicographic enumeration of the Pareto front in multi-objective combinatorial optimisation. *Journal of Multi-Criteria Decision Analysis, 33*(1). [https://doi.org/10.1002/mcda.70029](https://doi.org/10.1002/mcda.70029)
11. **Halstead, M. E., López-Ibáñez, M., Farmer, G., & Warren, P. A. (2026).** Multiobjective optimisation for others: How anchoring effects change based on who guides the interaction. *Journal of Multi-Criteria Decision Analysis, 33*(2). [https://doi.org/10.1002/mcda.70036](https://doi.org/10.1002/mcda.70036)
12. **Weber, T. A. (2026).** Relatively robust multicriteria decisions. *Management Science, 72*(4), 3175–3203. [https://doi.org/10.1287/mnsc.2025.00510](https://doi.org/10.1287/mnsc.2025.00510)
13. **Zhao, Q., Balugani, E., Gamberini, R., & Lolli, F. (2026).** SMAA-based FITradeoff: An efficient framework for pairwise elicitation in multicriteria decision analysis. *Journal of Multi-Criteria Decision Analysis, 33*(2). [https://doi.org/10.1002/mcda.70031](https://doi.org/10.1002/mcda.70031)

## Recent publications involving Madani Bezoui

14. **† Regaigui, S., Bezoui, M., Moulai, M., & Qaisar, S. M. (2025).** A memetic method for solving portfolio optimization problem under cardinality, quantity, and pre-assignment constraints. *Applied Soft Computing, 175*, 113058. [https://doi.org/10.1016/j.asoc.2025.113058](https://doi.org/10.1016/j.asoc.2025.113058)
15. **† Ibnelbey, R., & Bezoui, M. (2025).** Preference-based multi-objective optimization for student transportation: A machine learning approach. *Congrès annuel de la Société Française de Recherche Opérationnelle et d’Aide à la Décision*. [HAL-04974058](https://hal.science/hal-04974058)
16. **† Bezoui, M., Nouinou, H., & Bounceur, A. (2026).** Meta-learning with similarity-weighted transfer for manufacturing optimization. *Congrès annuel de la Société Française de Recherche Opérationnelle et d’Aide à la Décision*. [HAL-05548907](https://hal.science/hal-05548907)
17. **† Bounceur, A., Bezoui, M., Mir, F., Oulefki, A., Ouamri, M.-A., Seker, H., Foufou, S., Amira, A., & Himeur, Y. (2026).** Phygital Twin IoT: A hardware-software decomposition architecture for scalable and secure digital twin IoT systems. *IEEE Open Journal of the Computer Society, 7*, 755–768. [https://doi.org/10.1109/OJCS.2026.3681725](https://doi.org/10.1109/OJCS.2026.3681725)

To reach the requested six Bezoui references without artificial inflation, add these two earlier but methodologically relevant works:

18. **† Bezoui, M., Olteanu, A.-L., & Sevaux, M. (2023).** Integrating preferences within multiobjective flexible job shop scheduling. *European Journal of Operational Research, 305*(3), 1079–1086. [https://doi.org/10.1016/j.ejor.2022.07.002](https://doi.org/10.1016/j.ejor.2022.07.002)
19. **† Bezoui, M., Almaktoom, A. T., Bounceur, A., Qaisar, S. M., & Chouman, M. (2024).** Hybrid metaheuristics for Industry 5.0 multi-objective manufacturing and supply chain optimization. In *2024 21st Learning and Technology Conference*, 245–249. [https://doi.org/10.1109/LT60077.2024.10469011](https://doi.org/10.1109/LT60077.2024.10469011)

Thus, the proposed section contains:

- **17 references published in 2025–2026**;
- **6 publications involving Madani Bezoui**;
- a clear separation between direct methodological antecedents and contextual self-citations.

---

# 5. Two foundational additions

20. **Moore, R. E., Kearfott, R. B., & Cloud, M. J. (2009).** *Introduction to Interval Analysis*. SIAM. [https://doi.org/10.1137/1.9780898717716](https://doi.org/10.1137/1.9780898717716)
21. **Ogryczak, W. (1997).** On the lexicographic minimax approach to location problems. *European Journal of Operational Research, 100*(3), 566–585. [https://doi.org/10.1016/S0377-2217(96)00154-3](https://doi.org/10.1016/S0377-2217(96)00154-3)

These two are indispensable despite not being recent: one supports the lexicographic-minimax lineage, and the other supports the dependency and enclosure discussion.

---

# 6. Recommended editorial changes

## Mandatory corrections

1. Replace:

```text
doi: 10.1051/ro:1999118
```

with:

```text
doi: 10.1051/ro:1999112
```

2. Replace:

```text
10.1016/S0377 -2217(97)00163-X
```

with:

```text
10.1016/S0377-2217(97)00163-X
```

3. Cite Tsanas and Xifara explicitly as a dataset:

```text
Tsanas, A., & Xifara, A. (2012). Energy Efficiency [Dataset].
UCI Machine Learning Repository.
https://doi.org/10.24432/C51307
```

4. Add Ogryczak (1997) at the first definition of exact lexicographic minimax.
5. Add Moore, Kearfott, and Cloud (2009) when discussing dependency loss and interval quotients.
6. Harmonize the author ORCID in Crossref, HAL, the manuscript and the repository.

## Strongly recommended

Replace the current short paragraph beginning:

> “Recent work reinforces four adjacent needs…”

with the new *Related Work* section. The present paragraph reads as a list of recent papers rather than a structured comparison.
