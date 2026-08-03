
# 1. Final verdict

## **Major revision**

Several important corrections from the first review have been implemented correctly, notably the admissible-probe definition, explicit bound-dependent anchoring, Pareto separation, fixed-profile assumptions in the principal theorems, finite-algorithm complexity, sampling terminology, and continuous-polyhedron solver counts.

However, three frozen blockers remain unresolved:

1. the experiments still define a **floored sampling support** and then certify over its “deterministic hull” without proving that this hull is a valid Cartesian positive-denominator box;
2. the advertised ReLexTail v2.0.0 reproduction artifacts remain publicly unavailable/mismatched;
3. RQ7 still claims 100% validation of continuous-polyhedral optimisation by equality with 200 discretised candidate identifiers, while §6 explicitly acknowledges that this is not an independent validation of the continuous optimum.

A fourth frozen condition—fully explicit treatment of probe retention—is substantially improved but remains ambiguous in Algorithm 3. The review therefore cannot recommend acceptance or minor revision yet.

No author-response document or tracked-changes file was supplied in the present input. Verification below is based on the revised manuscript and the public artifact locations.

---

# 2. Resolution matrix

| ID | Previous severity | Status                       | Verification evidence                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | Remaining action                                                                                                                                                                                                                                     |
| -: | ----------------- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|  1 | Blocker           | **Unresolved**         | The abstract and Proposition 2 now correctly assume a rectangular set with positive denominators. However, §6.2 still samples floored nadirs and states that certification uses “the deterministic hull of this support, the box\(B(p)\).” The floor couples ideal and nadir. The Cartesian hull is not shown to satisfy \(z_i^{\mathrm{nad}}-z_i^\star\ge\gamma_i>0\).                                                                                                                                                | Define the exact perturbation formulas and certified endpoint bounds. Prove the whole certified box has a positive denominator, or replace it by a valid restricted rectangle. Re-run certification if the box changes.                              |
|  2 | Blocker           | **Partially resolved** | Eq. (2), Proposition 2, and Algorithm 3 now recognise fixed retention and subdivide boxes when an active-range lower bound is too small. This is a substantial correction. However, “retained probe” is not operationally fixed: Algorithm 3 uses\(\min_q\inf R_q\) without defining whether \(q\) ranges over the declared family, the nominal retained family, or a box-specific family. A probe inactive throughout a box causes endless subdivision until budget exhaustion rather than a formally declared regime. | Define\(Q_\beta\) or, preferably, state that certification uses the nominal/declared family \(Q_0\) and resolves a box only when all \(q\in Q_0\) satisfy \(\inf_\beta R_q>\varepsilon_q\). State explicitly that all other boxes remain unresolved. |
|  3 | Blocker           | **Unresolved**         | On 3 August 2026,[Zenodo 21739625](https://zenodo.org/records/21739625) still exposes version 1.0.4, titled “Lexicographic Probe-Regret Selection…”, with `LexPR-v1.0.4.zip`. The stated [GitHub repository](https://github.com/MadBezoui/ReLexTail) and API endpoint return 404.                                                                                                                                                                                                                                      | Publish and verify the exact ReLexTail v2.0.0 archive before publication. Correct the DOI/tag if necessary.                                                                                                                                          |
|  4 | Blocker           | **Unresolved**         | §6 now correctly states that comparison with sampled weighted-sum points is not validation of optimality and that exact vertex enumeration was not attempted. Nevertheless, §7.7 and Table 7 still claim “100% agreement” between a continuous-polyhedral solution and an “exact reference set” consisting of\(N=200\) discretised points, judged by candidate identifiers. These statements contradict §6.                                                                                                        | Remove the continuous-optimality validation claim or provide a genuine continuous/small-instance exact validation. Relabel the present result as finite restricted-reference agreement.                                                              |
|  5 | Important         | **Partially resolved** | Proposition 3 and Theorem 6 are now correctly restricted to continuous polyhedra, and the mixed-integer extension is separated. However, §6 later states: “Theorem 6 covers mixed-integer sets while the study exercises polytopes only,” contradicting the revised theorem.                                                                                                                                                                                                                                           | Replace that sentence by: “A mixed-integer extension is described but neither covered by Theorem 6 as stated nor benchmarked here,” or add a separate formally numbered mixed-integer proposition.                                                 |
|  6 | Important         | **Resolved**           | Algorithm 2 now uses direct lexicographic minimisation rather than sorting all candidates. §6.1 correctly gives\(O(NK\log K)\) and notes that full reporting sort adds \(O(NK\log N)\).                                                                                                                                                                                                                                                                                                                                  | None.                                                                                                                                                                                                                                                |
|  7 | Important         | **Resolved**           | Definition 1 now requires\(R\supseteq\{0,\mathbf1\}\cup\{r(x;b)\}\), finite-valued monotonicity, and \(q(\mathbf1)>q(0)\).                                                                                                                                                                                                                                                                                                                                                                                                | None.                                                                                                                                                                                                                                                |
|  8 | Important         | **Resolved**           | The revised Eq. (2) explicitly defines\(r(x;b)\), \(q^\star(b)\), \(q^w(b)\), \(R_q(b)\), and \(D_q(x;b)\).                                                                                                                                                                                                                                                                                                                                                                                                               | None, subject to the retention clarification under ID 2.                                                                                                                                                                                             |
|  9 | Important         | **Resolved**           | Theorem 3 now formally defines Pareto separation. Its proof is correct: monotonicity gives weak componentwise dominance, separation gives at least one strict disappointment, and\(T_{100}\) is then strict.                                                                                                                                                                                                                                                                                                              | None.                                                                                                                                                                                                                                                |
| 10 | Important         | **Partially resolved** | Proposition 2 now includes positive denominators, fixed retained multiset, multiplicities, resolutions and tail fractions. The proof is valid for such a box. Its application to the actual\(B(p)\) remains unverified because IDs 1–2 remain open.                                                                                                                                                                                                                                                                      | Resolve IDs 1–2 and state outward-enclosure validity explicitly in the proposition assumptions.                                                                                                                                                     |
| 11 | Important         | **Unresolved**         | The displayed radius notation remains ambiguous: the same visual symbol\(\rho\) is used for the certification frontier and witness upper bound. The claim “raising the budget can only raise it” is retained without a nested continuation policy.                                                                                                                                                                                                                                                                      | Use unambiguous notation such as\(\underline\rho_{B,d}\le\rho^\star\le\overline\rho_{\mathrm{wit}}\), and condition budget monotonicity on reuse/refinement of the same search tree.                                                                 |
| 12 | Important         | **Resolved**           | §6.2 is renamed appropriately, distinguishes sampled inner/outer approximations, includes the ceiling in the sample-size formula, and states the zero/small-probability limitation.                                                                                                                                                                                                                                                                                                                                      | None.                                                                                                                                                                                                                                                |
| 13 | Important         | **Unresolved**         | Figure 5 says methods use identical evaluation weights, but the manuscript still does not specify whether RW and SMAA draws are frozen across bound perturbations, nor the common-random-number and seed hierarchy.                                                                                                                                                                                                                                                                                                       | Add the exact stochastic protocol. If stochastic preferences were redrawn across perturbations, recompute point-flip rates using fixed draws.                                                                                                        |
| 14 | Important         | **Unresolved**         | The abstract and Table 1 frame empirical evidence relative to exact leximax, while §§7.2–7.3 and Table 6 principally claim improvement over exact LexPR. Table 6 still contains no ReLexTail rows or confidence intervals needed to verify the central comparison; Figure 5 remains subset-based.                                                                                                                                                                                                                      | Add the requested full-population ReLexTail/LexPR/leximax table with paired CIs and use comparator names consistently.                                                                                                                               |
| 15 | Important         | **Partially resolved** | Figure 5’s caption now says upper-tail regret. However, the embedded axis still reads “Subset-Averaged Tail Loss,” and §§7.2–7.3 continue to alternate between loss and regret. The displayed metric definition on p. 17 is incomplete: the formula for\(L_w\) and \(\Delta L_w\) is missing/malformed.                                                                                                                                                                                                             | Restore the complete equations and replace all “tail loss” labels referring to\(\Delta L_w\) by “upper-tail regret.”                                                                                                                             |
| 16 | Important         | **Resolved**           | The category-set change rate is now explicitly defined and is stated separately from point flip, Jaccard similarity and winner retention.                                                                                                                                                                                                                                                                                                                                                                                 | None.                                                                                                                                                                                                                                                |
| 17 | Important         | **Partially resolved** | Causal wording has been softened to “associated with.” Nevertheless, Table 6 does not itself contain a CVaR/ReLexTail row establishing the claimed association with “highest measured quality and explanatory power.”                                                                                                                                                                                                                                                                                                 | Either include the relevant ablation row or replace the claim by a narrower description of what Table 6 actually compares.                                                                                                                           |
| 18 | Important         | **Partially resolved** | Figure 5’s caption correctly calls the plot a descriptive trade-off diagram and says it does not identify a unique resolution. The body nevertheless retains “Quality-Stability frontier,” “move the frontier,” and “\(\delta=0.01\) provides the strongest compromise.”                                                                                                                                                                                                                                           | Apply the corrected wording consistently in §§7.2–7.3 and in the graphic’s embedded title.                                                                                                                                                       |
| 19 | Important         | **Unresolved**         | Figure 7 remains inconsistent with §7.8. The prose reports\(M=0.342\), \(C_M=35\), while the plotted score/tail ranges appear approximately \(0.50\)–\(0.70\) and the category axis extends only to about 14.                                                                                                                                                                                                                                                                                                           | Regenerate Figure 7 from the supplier audit record or correct the prose. Include exact values in the caption or a compact table.                                                                                                                     |
| 20 | Important         | **Unresolved**         | §7.8 still states that interval mode “brackets the necessary winners,” whereas the method encloses\(S_{\rm pos}\) and only provides a sufficient test for a necessary singleton. Figure 8 remains insufficiently explicit about inner/outer sets.                                                                                                                                                                                                                                                                      | Replace with “brackets the possible-winner set” and identify every Figure 8 curve precisely.                                                                                                                                                       |
| 21 | Important         | **Unresolved**         | The manuscript still gives neither the formal pairwise-tolerance relation nor the definition/witness for a “cycle.” The 82% claim is therefore not reproducible or mathematically interpretable.                                                                                                                                                                                                                                                                                                                        | Add the comparator definition, cycle criterion, one three-alternative witness, denominator and uncertainty interval.                                                                                                                                 |
| 22 | Important         | **Partially resolved** | The abstract now uses “To our knowledge” and presents the novelty as the specific integration. The related-work section still says existing multiple-CVaR formulations categorically lack the hierarchy, and no direct comparison with achievement bands/lexicographic goal programming or lexicographic OWA was added.                                                                                                                                                                                                 | Add a concise positioning paragraph. No new experiment is required.                                                                                                                                                                                  |
| 23 | Important         | **Partially resolved** | The scope and tolerance distinction are improved, and\(W_{\rm exact}\subseteq W^\varepsilon_{\rm ReLexTail}\) is stated. However, the full direct model is still schematic: the displayed ordered-statistic formula is incomplete, and the exact representation of all \(D_q(x)\) and carried stage constraints is not fully given.                                                                                                                                                                                       | Put the complete formulation in the manuscript appendix or in the verified archive, with a precise cross-reference.                                                                                                                                  |
| 24 | Important         | **Resolved**           | The audit statement now correctly requires the disappointment matrix plus multiplicities, identifiers, tail fractions, resolutions, construction rules, IEEE encodings and tie-breaking. It distinguishes stored-machine-value replay.                                                                                                                                                                                                                                                                                    | None.                                                                                                                                                                                                                                                |
| 25 | Important         | **Unresolved**         | Table 5 still labels the dense-grid experiment “Known-truth,” even though §6 correctly says the grid is finite and can miss small winning regions.                                                                                                                                                                                                                                                                                                                                                                     | Rename it “Dense-grid stress test.”                                                                                                                                                                                                                |
| 26 | Minor             | **Partially resolved** | Theorem 5 now uses finite\(A\) and Corollary 1 is numbered. The corollary reverts to \(X\), despite relying on a finite minimum.                                                                                                                                                                                                                                                                                                                                                                                          | Replace\(X\) by \(A\) in Corollary 1, or use an infimum and state an infinite-set extension.                                                                                                                                                         |
| 27 | Minor             | **Resolved**           | The revised text distinguishes theoretical exact-real\(\Psi\) from stored machine profile \(\widehat\Psi\).                                                                                                                                                                                                                                                                                                                                                                                                               | None.                                                                                                                                                                                                                                                |
| 28 | Minor             | **Partially resolved** | Separate\(\varepsilon_f\) and \(\varepsilon_q\) now appear, but the first paragraph of §3.1 still says “threshold \(\varepsilon_z\)” before defining \(\varepsilon_f\).                                                                                                                                                                                                                                                                                                                                                | Replace\(\varepsilon_z\) by \(\varepsilon_f\) and ensure Algorithm 2 uses \(\varepsilon_q\) for probe deletion.                                                                                                                                      |
| 29 | Minor             | **Partially resolved** | Table 4 is better ordered and more informative. Some formulas remain abbreviated or malformed, including the weighted-sum normalisation and the exact hidden-preference metric.                                                                                                                                                                                                                                                                                                                                           | Typeset explicit formulas cleanly and state anchor conventions for every comparator.                                                                                                                                                                 |
| 30 | Minor             | **Partially resolved** | Several output distinctions are corrected. Remaining defects include the split Section 1 heading, the statement that Section 4 shows a constructed case, Figure 1’s “one alternative,” and inconsistent\(W_{\rm ReLexTail}\) versus \(W_{\rm exact}\).                                                                                                                                                                                                                                                                 | Apply one final terminology/cross-reference pass.                                                                                                                                                                                                    |

---

# 3. Regression check

## 3.1 Definitions

### Verified

- Definition 1 is now mathematically well-posed.
- Bound-dependent probe anchors and disappointments are explicitly introduced.
- \(W_{\rm exact}\) and \(W_{\rm cat}\) are distinguished.
- The theoretical profile \(\Psi\) and machine profile \(\widehat\Psi\) are distinguished.
- Category-set change rate is explicitly defined.

### Remaining defects

- The sampled floored support and certified rectangular box are still not reconciled.
- The exact perturbation formulas in §6.2 are malformed in the PDF.
- The retained family used by Algorithm 3 remains ambiguous.
- \(\varepsilon_z/\varepsilon_f/\varepsilon_q\) is not fully consistent.
- \(S_{\rm pos}\), \(S_{\rm nec}\), and Figure 8 terminology remain inconsistent.

---

## 3.2 Theorems

### Verified

- Theorems 1–2 are valid under their revised fixed-family assumptions.
- Proposition 1 remains valid.
- Theorem 3 is now correctly formulated using Pareto separation.
- Theorem 4 is valid under fixed tail fractions and resolutions.
- Theorem 5 is valid for finite \(A\) and fixed \(K\).
- Proposition 2 is valid **as a conditional mathematical proposition** on a fixed-retention, positive-denominator box.
- Proposition 3’s arithmetic is correct for continuous polyhedra.
- Theorem 6 is valid in its revised continuous-polyhedron scope.

### Remaining defects

- Proposition 2 is not yet shown to apply to the experimental uncertainty set.
- Corollary 1 uses \(X\) instead of finite \(A\).
- Radius notation and budget-monotonicity conditions remain unclear.
- A later paragraph incorrectly says Theorem 6 covers mixed-integer sets.

---

## 3.3 Algorithms

### Verified

- Algorithm 2 now supports the claimed \(O(NK\log K)\) complexity.
- Algorithm 3 correctly uses terminal-leaf unions rather than global subtraction.
- Budget exhaustion conservatively contributes unresolved survivor sets to `Out`.
- A box is resolved only through a candidate certified to beat every rival.

### Remaining defects

- Algorithm 3 must state the exact probe index set used in the active-range test.
- Its output header says:
  \[
  \text{Out}\supseteq S_{\rm nec},
  \]
  whereas the intended and stronger invariant is
  \[
  \text{In}\subseteq S_{\rm pos}\subseteq\text{Out}.
  \]
  The current statement is not false, because \(S_{\rm nec}\subseteq S_{\rm pos}\), but it fails to state the algorithm’s advertised guarantee.
- Persistent inactive probes need an explicit “return unresolved” rule rather than implicit repeated subdivision.
- The complete LP/MILP formulation remains too schematic.

---

## 3.4 Solver counts

The revised counts remain correct for continuous polyhedral \(X\):

\[
2m \quad\text{criterion-bound LPs},
\]

\[
2(m+1)+(m+1)=3m+3
\quad\text{probe-anchor LPs},
\]

so preprocessing is

\[
5m+3\ \text{LPs}.
\]

ReLexTail then uses:

\[
4\ \text{MILP category stages},
\]

\[
4\ \text{exact-tail LP stages},
\]

and

\[
K-1=m+1\ \text{terminal LP stages}.
\]

Therefore:

\[
6m+8\ \text{LPs}+4\ \text{MILPs}
\]

is correct.

For exact continuous LexPR:

\[
(5m+3)+(m+2)=6m+5\ \text{LPs}.
\]

The only remaining solver-count correction is the contradictory statement that Theorem 6 covers mixed-integer sets.

---

## 3.5 Experiments

### Improvements verified

- The distinction between sampled and certified possible-winner analysis is clearer.
- The dense-grid limitations are acknowledged.
- Figure 5’s caption now correctly warns that no unique resolution is identified.
- Generator heterogeneity is explicitly acknowledged.
- The continuous weighted-sum comparator is correctly not presented as proof of optimality in §6.

### Remaining failures

- Current artifacts cannot be inspected or reproduced.
- The RQ7 “100% validation” claim contradicts the §6 caveat.
- Full-population ReLexTail versus LexPR/leximax numbers and CIs remain absent.
- RW/SMAA common-random-number handling is unspecified.
- The 82% cycle experiment is undefined.
- The dense-grid experiment remains mislabeled “Known-truth.”
- The RQ4 attribution remains unsupported by the displayed table.

---

## 3.6 Metrics

### Verified

- Category-set change rate is now explicitly separated from point flip.
- Fixed nominal evaluation bounds are conceptually retained.
- Common evaluation weights are claimed in Figure 5.

### Remaining defects

- The displayed definition of \(L_w\) and \(\Delta L_w\) is incomplete.
- “Tail loss” and “tail regret” remain inconsistent.
- Main confidence intervals are still relegated to the archive.
- The pooled/subset estimands are not fully harmonised.
- The stochastic-method flip protocol remains unclear.

---

## 3.7 Tables and figures

### Corrected

- Table 4 precedes Table 5.
- Figure 5’s caption has been substantially improved.
- Table 3 is described more cautiously in the surrounding text.

### Still inconsistent

- Table 1 says empirical claims are relative to exact leximax, while its rows name exact LexPR.
- Table 5 still says “Known-truth.”
- Table 6 omits ReLexTail variants and central CIs.
- Figure 5’s embedded title/axis retain “frontier” and “tail loss.”
- Figure 7 conflicts numerically with §7.8.
- Figure 8 does not clearly identify certified inner/outer possible-winner sets.
- Table 7 still describes an invalid continuous-optimum validation protocol.

---

## 3.8 Abstract and conclusion

### Corrected

- Novelty is now framed as “to our knowledge.”
- Certification is conditioned on fixed retention and positive denominators.
- The conclusion correctly distinguishes categorical stability from fully refined point stability.
- General superiority is explicitly disclaimed.

### Remaining propagation defects

- The abstract compares tail regret with exact leximax, while the main empirical claim is framed against exact LexPR.
- The contribution section still states certification without immediately repeating the corrected uncertainty assumptions.
- The conclusion’s certification statement is mathematically acceptable, but the experiments have not been shown to satisfy those assumptions.
- The direct-MILP claim remains vulnerable to the unresolved RQ7 validation wording.

---

## 3.9 Reproducibility

**Unresolved blocker.**

The public DOI and GitHub locations do not provide the claimed ReLexTail v2.0.0 artifact. Consequently, I could not verify:

- implementation of \(\widehat\Psi\);
- outward rounding;
- active-range retention handling;
- one-command reproduction;
- stochastic common-random-number use;
- Table 6 confidence intervals;
- Figure 7 values;
- Figure 8 curve definitions;
- direct-optimisation formulations;
- audit replay.

This is an availability mismatch, not an allegation that the computations are false.

---

# 4. New issues

No new substantive blocking issue is introduced.

One revision-created editorial/contract defect should be corrected:

> **Algorithm 3 output header states `Out \(\supseteq S_{\rm nec}\)` instead of the intended `In \(\subseteq S_{\rm pos}\subseteq Out\)`.**

This does not invalidate the underlying algorithm because the prose gives the stronger correct invariant, but the pseudocode header must be repaired.

No previously overlooked blocker is raised.

---

# 5. Final finite correction list

The following finite list is sufficient; no further extension is requested.

## Blocking corrections

1. **Repair the uncertainty domain.**Give explicit endpoint formulas for \(B(p)\) and prove
   \[
   \inf_{b\in B(p)}(z_i^{\rm nad}-z_i^\star)>0
   \]
   for every criterion. Remove or reformulate the floor/hull construction if this cannot be shown.
2. **Freeze the certification probe family operationally.**Define the set over which Algorithm 3 tests \(R_q\). State that boxes without certified uniform retention are unresolved.
3. **Publish the correct artifact.**The DOI and GitHub tag must expose the exact ReLexTail v2.0.0 archive used by the paper.
4. **Correct RQ7.**
   Either provide a valid continuous-optimum verification or explicitly relabel Table 7 as agreement on a finite discretised reference set. Remove “exact reference set” and “validation of continuous optima” unless justified.

## Important consistency corrections

5. Replace the mixed-integer statement after Theorem 6 so that it matches the theorem’s continuous scope.
6. Repair radius notation and qualify budget monotonicity by a nested continuation policy.
7. State RW/SMAA fixed-draw and common-random-number protocols.
8. Add one main-paper table containing ReLexTail, exact LexPR and exact leximax results on the full population, including paired 95% CIs.
9. Restore the complete definitions:
   \[
   L_w(x;b_0)=\sum_iw_ir_i(x;b_0),
   \qquad
   \Delta L_w=L_w(x^\star;b_0)-\min_yL_w(y;b_0).
   \]
10. Use “upper-tail regret” consistently; remove “tail loss” where the plotted variable is \(\Delta L_w\).
11. Remove “strongest compromise” unless an explicit selection rule is supplied; replace remaining “frontier” wording by “trade-off diagram.”
12. Correct Figure 7 or §7.8 so that \(M\), \(T_\alpha\), and category values agree.
13. Replace “brackets the necessary winners” by “brackets the possible-winner set” and clarify Figure 8.
14. Define the pairwise-tolerance cycle experiment.
15. Rename Table 5’s “Known-truth” experiment “Dense-grid stress test.”
16. Complete or stably cross-reference the full LP/MILP formulation.

## Finite editorial corrections

17. Change Algorithm 3’s output contract to
    \[
    \mathrm{In}\subseteq S_{\rm pos}\subseteq\mathrm{Out}.
    \]
18. Replace \(X\) by finite \(A\) in Corollary 1.
19. Replace the stray \(\varepsilon_z\) by \(\varepsilon_f\).
20. Harmonise \(W_{\rm exact}\) and \(W_{\rm ReLexTail}\).
21. Correct the Section 1 heading and the inaccurate statement that Section 4 contains the constructed case.
22. Correct Reference [22]’s page range, currently rendered “2–1222,” to the appropriate article-number format, apparently “2:1–2:22.”

---

# 6. Publication recommendation

The revision has made genuine and mathematically useful progress, and the finite ReLexTail order itself now appears sound under a clearly fixed probe family. Nevertheless, publication cannot yet be recommended because the certified experiments have not been tied to a demonstrably valid positive-denominator uncertainty box, the reproduction archive remains unavailable in the claimed version, and the continuous-direct-optimisation validation claim remains internally contradictory. These are exactly frozen blockers from the first review, not new standards. Once they and the finite consistency corrections above are resolved, the manuscript should be reassessed primarily through artifact and internal-consistency verification rather than another open-ended scientific review.
