# Novelty memo

**Date:** 6 September 2026. **Status:** provisional. This memo states precisely
what is claimed to be new, and precisely what would have to be shown for the
claim to fail. It is not a completed systematic review, and it does not assert
that the closest works lack properties whose absence has not been verified in
their full text.

## 1. The claim, stated narrowly enough to be refutable

> For the ReLexTail preorder over a box of admissible normalisation bounds, a
> certificate that a nominal winner beats every rival throughout the box does
> not require the categorical coordinates of any candidate to be retained.
> Consequently the all-candidate retention condition currently used is strictly
> sufficient and not necessary, and there exist instances on which it certifies
> nothing while the decision-focused condition certifies the entire box.

and, separately,

> In the disappointment quotient `D_q = (q - q*) / (q^w - q*)`, the anchors
> `q*(b)` and `q^w(b)` are shared across candidates at a common `b`. Keeping
> them inside a single quotient -- rather than widening numerator and
> denominator into independent intervals -- yields an enclosure that is
> contained in the independent one, strictly so whenever the anchor enclosure
> has positive width.

Both statements are proved in the manuscript and instantiated by frozen
rational examples (`src/certrelex/examples.py`).

## 2. What is *not* claimed

* Neither statement is a new result in interval analysis. The dependency
  problem, and the fact that keeping shared variables inside a single
  expression tightens an enclosure, are textbook. What is new here is the
  identification of *which* shared quantities occur in this rule, the proof
  that the resulting corner formula is exact for the relaxation, and the
  measured consequence for certification on a prespecified benchmark.
* No claim is made that the certificate is tighter than what a general global
  optimiser or an SMT solver could establish given unlimited time.
* No claim of superiority in decision quality, regret, or calibration. Those
  belong to Tracks B and C, which were not run
  (`protocol/preregistration.md`, section 7).
* No claim that ReLexTail dominates other MCDA methods. Different methods solve
  different decision problems.

## 3. Closest work and what remains to be verified

Carried over from `Plan_for_Enhanced_Version.md` section 3. These records were
identified during planning; **full-text verification is an open work package**,
and the "consequence" column states an obligation, not a finding about the
paper.

| Line | Record | Obligation |
|---|---|---|
| Relative robustness with unknown criterion weights | Weber, *Relatively Robust Multicriteria Decisions*, Management Science (online 2025) | Mandatory recent comparator for Track B. Its native relative-performance guarantee must be reported separately from range-normalised regret. Not a Track A comparator: it does not certify a fixed rule over a bound box. |
| Approximate lexicographic fairness | Henzinger et al., *Leximax Approximations and Representative Cohort Selection*, FORC 2022 | Check whether its approximate-leximax definition coincides with fixed-cell categorical equality. If it does, the preorder is not new and only the certificate is. |
| Lexicographic alpha-robustness | *Lexicographic alpha-robustness: an alternative to min-max criteria*, EJOR 2012 | Fixed categories plus worst-first aggregation are not by themselves novel. Verify whether a bound-uncertainty certificate is present. |
| Necessary/possible winners, robust ordinal regression | Fifty years of MCDA, EJOR (2025 issue), used to locate primary sources | Locate any prior work that certifies a *lexicographic* winner over a normalisation-bound set rather than over a weight set. This is the single most important check. |
| Ordered optimisation foundations | Ogryczak and Sliwinski (2003) | Already cited. The ordered-sum LP identities are reused, not claimed. |

## 4. Searches run in this session, and their outcome

Recorded honestly in `search_log.csv`. Two cross-disciplinary searches were run
against an OpenAlex-backed index. Both returned off-field results: the index is
lexical, and the query vocabulary of this problem ("normalisation bounds",
"possible winners", "certified radius") collides with unrelated literatures.
**No usable novelty evidence was obtained in this session.** The searches are
logged so that the failure is visible rather than invisible, and the
publisher-database search described in the plan (EJOR, JMCDA, Management
Science, Operations Research, proceedings, preprint servers, with backward and
forward citation chasing) remains to be executed.

## 5. Gate decision

The novelty gate in the plan asks for one theorem or algorithmic result not
already supplied by the closest work under equivalent assumptions, *before* a
large benchmark run. The benchmark run performed here is small and is confined
to Track A, so the gate is not yet binding at full force. The honest position:

* the two statements in section 1 are proved and demonstrated;
* whether they are already known has **not** been established;
* accordingly the manuscript presents them as a strengthening of its own
  certification condition and its own enclosure, with the positioning claim
  scoped to that, and does not assert priority over the literature.

If full-text verification later shows either statement is already available
under equivalent assumptions, the correct response is to document the reduction
and reposition, not to rename the contribution.
