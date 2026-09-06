# Status against `Plan_for_Enhanced_Version.md`

Updated 6 September 2026. One row per plan item. `Plan_for_Enhanced_Version.md` is an
internal research proposal and is deliberately **not** part of the submission
archive; this file is written to be readable without it. "Done" means the artefact
exists and is exercised by `enhanced/reproduce.py` or by the manuscript build;
"partial" says exactly what is missing; "not started" is not softened.

## Section 4 — proposed original contribution

| Plan item | Status | Where |
|---|---|---|
| 4.1 Certify the decision region, not every coordinate | **done** | `src/certrelex/certify.py`; Proposition 1 in `Manuscrit/submission/certification.tex` |
| 4.1 Certified inner region plus explicit counterexample bounds | **done** | `certify_winner`, `oracle.witness_radius` |
| 4.1 Report "no unique-winner certificate" rather than positive stability | **done** | refusal path in `enclosure.d_enclosure`, unresolved leaves in `certify_winner` |
| 4.1 Tied nominal optima need a separate set-preservation contract | **partial** | ties are detected, recorded and skipped; no contract is defined or claimed |
| 4.2.1 Singleton cancellation used once, never branched on | **done** | `enclosure._singleton_column`; rechecked at box corners by `verify._singleton_column` |
| 4.2.2 Shared-anchor cancellation in pairwise differences | **done** | `interval.quotient_range`; Proposition 2 |
| 4.2.3 Equivalent parameterisations / quotient representation | **not started** | no reparameterisation is claimed; the plan's warning against an unjustified independent box is respected by not attempting it |
| 4.2.4 Decision-relevant branching | **done** | `certify._split_decision`; measured as an exploratory contrast |
| 4.2 Rational polyhedral / affine-arithmetic / McCormick relaxations | **not started** | corner-exact interval enclosure only |
| 4.3 Output contract: point with certificate, enclosure, or abstention | **partial** | certificate and unresolved enclosure are implemented; the abstention *policy* is not |
| 4.3 Engine must not change winners | **done** | asserted in `tests/test_soundness.py::test_engine_does_not_change_the_declared_winner` |
| 4.4 Finite-library calibration guarantee | **not started** | Track C not run; recorded as unestablished in the claim registry |

## Section 5 — theory work package

| Result | Status |
|---|---|
| Sound joint elimination, boundaries included | **done** (Proposition 1; no tie tolerance anywhere in the certified path) |
| Decision-focused stability certifies cases the all-coordinate condition excludes | **done** (Proposition 3, frozen example E-A) |
| Strict computational improvement | **partial** — an exhibited family (E-B) and measured gains; no complexity theorem |
| Anytime validity | **done** (certified and unresolved leaves both retained with their volume) |
| Finite convergence conditions | **partial** — no finite exact recovery is claimed; tie and boundary obstructions are stated |
| Numerical soundness: outward arithmetic, exact category comparisons, replayable witnesses | **done** (`protocol/numerical_contract.md`, `verify.py`) |
| Independent rational reference implementation | **done** (`oracle.py`, `verify.py`) |
| Representation equivalence for quotient transformations | **not started** (see 4.2.3) |
| Snapping convention treated as a distinct object from the exact rule | **done** — the certified path never snaps; the operational rule is measured against the exact one in `tests/test_numerical_contract.py` |

## Section 6 — data programme

| Plan item | Status |
|---|---|
| Six development families + two stress families | **done** (`src/certrelex/benchmark.py`) |
| Frozen split manifest fixed before the run | **done** (deterministic in the replicate index; SHA-256 seeds) |
| 1,200 matrices, m up to 20, N in {50,200} | **partial** — 192 matrices of 40 candidates at m in {3,6,10}, certified on a shortlist of 10. Reduced to fit the available compute; the reduction is declared in the manuscript and in `run_environment.json` |
| Exact-oracle suite of 100–200 small rational problems | **partial** — three frozen rational examples plus 11,072 oracle draws inside certified leaves; no separate rational suite |
| Scaling suite to N = 10,000, m = 50 | **not started** |
| 6.2 External preference populations | **not started** — Track B |
| 6.3 Public and measured data with repeated observations | **not started** — the existing UCI check remains a simulated dataset and is labelled as such |
| 6.4 Provenance contract per episode | **partial** — instance id, family, criterion count, replicate, split, seeds and environment are recorded; criterion units, directions and licences do not apply to generated data |

## Section 7 — baselines

| Track | Status |
|---|---|
| A: fixed-rule certification (old engine, new engine, ablations) | **done** — four arms, matched budget, same rule and arithmetic |
| A: dense sampling labelled noncertifying | **partial** — the oracle sampler plays this role for falsification but is not reported as a timed arm |
| A: general global optimiser / SMT reference | **not started** |
| B: decision quality against 10+ named baselines | **not started** |
| C: recommendation policies at matched coverage | **not started** |

## Section 8 — experiments

| Experiment | Status |
|---|---|
| E0 numerical correctness | **done** — 0 falsified certificates, 0 replay failures |
| E1 mechanism | **done** — paired enclosure widths, per mode |
| E2 fixed-budget certification | **done** — certified radius, volume, boxes, on locked splits |
| E3 held-out decision quality | **not started** |
| E4 calibration | **not started** |
| E5 robustness to grid shifts and misspecification | **partial** — grid-origin and ablation sensitivity already in the manuscript; the stress families add correlated heavy tails and near-tied margins |
| E6 measured external data | **not started** |
| E7 scale and interruption | **partial** — anytime progression at three budgets; no scaling suite, no timing study |
| E8 human interpretation | **not started** |

### Against the plan's own success targets

1. *Correctness — zero false certificates:* **met** on what was searched (11,072 oracle draws, 5,029 replayed leaves, zero failures). This is evidence of the absence of the errors searched for, not a substitute for the proofs.
2. *Certification — a 20 percentage-point increase in certified instances at equal budget, or a threefold median speed-up:* **met on the certified-instance reading.** At the focal level and a matched budget of 300 boxes, the share of locked test instances fully certified is 0.0% for A0, 41.7% for A1, 56.9% for A2 and 58.3% for A3 — a 41.7-point gain from decision focus alone and 58.3 points overall. Mean certified volume moves correspondingly, by 0.427 [0.315, 0.544] for P1 and a further 0.164 [0.089, 0.247] for P2. The speed-up reading is not reported: A0 certifies no instance at this budget, so there is no median time-to-certificate to divide by.
3. *Decision quality — 5% relative reduction in upper-tail regret:* **not tested.**
4. *Reliability — selective risk at a coverage target:* **not tested.**
5. *External evidence on two measured contexts:* **not tested.**

Per the plan's own instruction, the title, abstract and claims are scoped to the
gates actually passed: the algorithmic contribution is claimed and the decision-quality
and calibration claims are not made.

## Sections 9–12 — infrastructure and process

| Plan item | Status |
|---|---|
| Separate `enhanced/` tree, manuscript outputs preserved | **done** |
| `protocol/`, `literature/`, `src/`, `tests/`, `configs/`, `results/`, `analysis/` | **done**. `baselines/` holds only a README saying why it is empty: no Track B or C comparison has been run, so no external method has been adapted or version-pinned |
| Explicit numerical contract | **done** (`protocol/numerical_contract.md`) |
| Verifier simpler than the search and independent of it | **done** |
| Every manuscript number generated from result files; build fails on stale data | **done** (`analysis/make_macros.py`, checked by `Manuscrit/scripts/validate_submission.py`) |
| `reproduce.py`, `MANIFEST.sha256` | **done** |
| `environment.lock` | **partial** — pinned versions in `Manuscrit/requirements.txt` and the resolved environment in `results/run_environment.json`; no lockfile |
| Literature search log, evidence matrix, novelty memo | **done as registries**; the searches themselves returned nothing usable and that failure is recorded rather than hidden |
| Novelty gate passed before scaling the benchmark | **not met** — full-text verification of the closest work is outstanding. The benchmark run here is small and confined to Track A, and the manuscript does not assert priority |
| Claim-to-evidence table before drafting the abstract | **done** (`claim_registry.csv`; mirrored as a manuscript table) |
| Resumable per-instance jobs, cached losses, separate calibration/test directories | **not started** — the run is a single sequential pass |
| Preregistration with a third party | **not done** — splits, arms, outcomes and contrasts were fixed in source before the confirmatory run, and p-values are reported as descriptive |
