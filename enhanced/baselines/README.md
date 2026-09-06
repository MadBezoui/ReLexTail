# `baselines/` — deliberately empty

Track A compares four *certification* arms of the same declared rule; the
comparison lives in `analysis/run_experiments.py` and needs no external
adapter. Nothing has been reimplemented here, and no third-party method has
been version-pinned, because no Track B or Track C comparison has been run.

Plan section 7 lists what would go here when those tracks are attempted:

* **Track A**, still missing: a general global optimiser or SMT reference for
  small instances, and a dense-sampling arm labelled noncertifying and timed on
  the same budget.
* **Track B**: exact LexPR, fixed-resolution ReLexTail, raw-criterion leximax,
  mean/OWA or spectral aggregation, weighted sum, TOPSIS, VIKOR, minimax regret
  over the same admissible preference set, SMAA under a declared common prior,
  and Weber's relatively robust method — each with published implementations
  where they exist, validated against the source paper's own examples, with
  unsupported or problem-incompatible cases reported separately.
* **Track C**: the same calibration wrapper applied to the strongest competing
  methods, compared at equal point coverage, shortlist size and wall-clock
  budget.

An empty directory here is the honest state, not an oversight. See
`../protocol/plan_status.md`.
