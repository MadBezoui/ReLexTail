# `enhanced/` — decision-focused certification for ReLexTail

This tree implements and tests **Track A** of
`Plan_for_Enhanced_Version.md`: fixed-rule certification. It does not change
the decision rule. On fixed inputs the engine here and the engine in
`Experimental/code/lexpr/certified.py` select the same alternative; what
differs is what can be proved about that alternative and at what cost.

The manuscript sections it feeds are `Manuscrit/submission/certification.tex`
and the claim register in `Manuscrit/submission/discussion.tex`.

## Reproduce

```bash
python enhanced/reproduce.py
```

Roughly 25 minutes on one core for the full run. `--quick` runs a reduced
benchmark for smoke-testing; its numbers must not reach the manuscript, and the
run environment file records the reduced budget so a quick run is visible in
the record rather than silent.

The final stage writes `Manuscrit/submission/generated_certrelex.tex`. Every
number the certification section prints comes from that file. If it is missing
or stale the LaTeX build fails on an undefined control sequence, which is the
intended behaviour.

## What is new, precisely

**1. Certify the decision, not every coordinate.** The condition used until now
requires every candidate to keep every risk coordinate inside its resolution
cell. That is sufficient and not necessary: a candidate not in contention, a
structurally invariant boundary coordinate, or a coordinate occurring after an
already decisive comparison can all move without touching the recommendation.
Proposition 1 of `src/certrelex/certify.py` shows the pairwise test
`Psi(D_hi(x0)) <_lex Psi(D_lo(y))` is sound on its own. Example E-A is a 5x4
rational instance where all five candidates leave their cells — so the old
condition certifies nothing — and the winner is certified over the whole box
with no branching.

**2. Keep the shared anchors inside one quotient.** In
`D_q = (q - q*) / (q^w - q*)` the anchors `q*(b)` and `q^w(b)` are shared by
every candidate at a common `b`. Widening numerator and denominator separately
lets the numerator take an extreme value against a denominator the same anchor
could not produce. `interval.quotient_range` evaluates the four corners of the
shared-anchor rectangle instead; the result is contained in the independent
quotient and strictly inside it whenever the anchors carry width. Example E-B
is a 4x3 rational instance where the joint enclosure resolves the root box in
one box and the independent enclosure leaves two thirds of it uncertified after
2,048.

**3. A two-sided bracket.** The search is one-sided: failing to certify at
level `p` means only that the budget ran out. Upper bounds come from
`oracle.witness_radius`, which searches for a bound vector at which the exact
rational oracle names a different unique winner. Example E-C brackets the
decision radius between a certified lower bound and a verified switch.

**4. Two independent numerical routes.** `verify.py` replays every certified
leaf in exact rational arithmetic, imports nothing from the search path, and
checks the singleton-cancellation identity at the box corners rather than
assuming it.

## Layout

```
protocol/      numerical contract; preregistered splits, arms and contrasts
literature/    search log, evidence matrix, novelty memo
src/certrelex/ interval, profile, enclosure, certify, oracle, verify,
               benchmark, examples
tests/         soundness, numerical contract, frozen examples
analysis/      experiment driver, report builder, macro emitter, tables, figures
results/       raw per-instance results, correctness log, run environment
```

## Honest limits

* Everything here is about **certification**. Nothing in it supports a claim
  about decision quality, external regret, or calibration. Tracks B and C of
  the plan were not run; `protocol/preregistration.md` section 7 says so and
  the manuscript's claim register lists them as unestablished.
* Instances are generated. The shortlist size is declared, not elicited. The
  two stress families test extrapolation and license no claim about arbitrary
  deployment shift.
* A certified radius of zero means "not certified within this budget", never
  "the radius is zero".
* Whether the two propositions are already available in the literature under
  equivalent assumptions has **not** been established;
  `literature/novelty_memo.md` records what would settle it and why the
  searches run so far did not.
* Tied nominal optima are recorded and skipped. No set-preservation contract
  for ties is defined or claimed.
