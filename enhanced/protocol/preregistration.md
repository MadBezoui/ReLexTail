# Protocol for the enhanced study (Track A)

**Frozen:** 6 September 2026, before the confirmatory run on the `test` and
`stress` splits.

This is a scoped protocol, not the full programme of
`Plan_for_Enhanced_Version.md`. It covers **Track A only** -- fixed-rule
certification -- because that is the part whose evidence can be produced and
verified here. Tracks B and C (decision quality against external preference
populations, and the calibrated recommendation policy) are **not** run; the
claim registry records them as unestablished rather than as pending successes.

## 1. What changes and what does not

The declared decision rule does not change. On fixed inputs the enhanced engine
and the current submission engine select the same candidate; `test_soundness.py`
asserts this. The contribution is what can be *proved* about that candidate and
at what cost.

## 2. Instances and splits

`src/certrelex/benchmark.py`. Six development families and two stress families,
`m` in {3, 6, 10}, 8 replicates each: 192 candidate sets of 40 non-dominated
alternatives. Certification runs on the first 10 rows of each set -- a
shortlist, which is the realistic size for a recommendation problem and is
declared, not chosen after seeing results.

The split is a deterministic function of the replicate index, fixed in source
before any run:

| replicate | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| split | dev | dev | dev | calibration | test | test | test | test |

The two stress families (`narrow`, `heavytail`) are locked out-of-distribution
in their entirety. They test extrapolation; they do not license any claim about
arbitrary deployment shift.

Seeds derive from SHA-256 of `(master seed, family, m, replicate)`. Python's
`hash` is deliberately not used: it is randomised per process, which would make
the benchmark depend on an environment variable.

The 90 instances of the current submission remain the **development baseline**.
They have been inspected and tuned against, so they are not used as
confirmatory evidence.

## 3. Arms

Each arm adds exactly one component to the arm above. All arms share the
declared rule, the probes, the uncertainty box, the arithmetic contract, the
box budget and the hardware.

| arm | gate | quotient | branching |
|---|---|---|---|
| A0 | all-candidate retention | independent | widest coordinate |
| A1 | decision-focused | independent | widest coordinate |
| A2 | decision-focused | joint (shared anchors) | widest coordinate |
| A3 | decision-focused | joint (shared anchors) | decision-relevant |

A0 is the current engine's condition. A3 is the proposal.

## 4. Primary outcomes, fixed in advance

1. **`rho_lower`** -- certified lower bound on the decision radius, by bisection
   at a matched box budget. Continuous, one per instance per arm. This is the
   primary endpoint.
2. **`focal_certified_volume`** -- certified fraction of `B(0.02)` at the
   matched budget.
3. **`focal_boxes`** -- boxes to certificate at the focal level, censored at
   the budget. Time-to-certificate is treated as censored, not dropped.

Mechanism outcome (E1): enclosure width of the decisive profile coordinate at
the root box, per quotient mode.

Correctness outcome (E0): count of certificates falsified by the exact rational
oracle, and count of certified leaves rejected by the independent replay
verifier. The target is zero; any non-zero count is reported as a failure and
not netted against successes.

## 5. Primary contrasts

Paired within instance, on the `test` split:

* **P1** A1 - A0 on `rho_lower` (does decision focus certify more?)
* **P2** A2 - A1 on `rho_lower` (does dependency preservation certify more?)

Secondary, labelled as such: A3 - A2 (branching), the same contrasts on the
`stress` split, and all contrasts on `focal_certified_volume`.

Holm correction within the family {P1, P2}. The independent unit is the
instance. Effect sizes and paired bootstrap intervals are reported, not only
significance. Family is a grouping factor; per-family effects are reported
before aggregation.

Because this study was not preregistered with a third party, p-values are
descriptive. The splits, arms, outcomes and contrasts in this file were
nevertheless fixed before the confirmatory run.

## 6. Stopping and honesty rules

* A negative or null result on P1 or P2 is published as such. There is no
  fallback contrast to promote.
* No instance is dropped because an arm times out, refuses a box, or loses.
  Refusals and budget exhaustion enter the denominator.
* If the exact oracle falsifies any certificate, the affected claim is
  withdrawn before anything else is reported.
* Targets from the plan (a 20-point certification increase, a threefold
  speed-up) are *targets*. Whether they are met is an outcome of the run, not a
  precondition for reporting it.

## 7. Explicitly out of scope here

* External decision regret against elicited or simulated preference
  populations (Track B, plan section 6.2).
* The calibrated recommendation policy and its finite-library risk/coverage
  bound (Track C, plan sections 4.3-4.4).
* Measured external data with repeated observations (plan section 6.3) and any
  human-subject component (plan section 6.4).

Nothing in this study licenses a claim about decision quality, regret, or
calibration. It is a claim about certification.
