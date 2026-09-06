# Numerical contract

**Frozen:** 6 September 2026. Any change to this file invalidates every result
produced before the change and requires a re-run, not a patch.

The plan requires four numerical layers to be specified separately, because
conflating them is how a machine tolerance quietly becomes a preference
parameter. This file names each layer, says which module implements it, and
says what is *not* claimed about it.

## 1. Reference mathematical rule

The declared rule is ReLexTail on the retained probe multiset. Its reference
semantics live in `src/certrelex/profile.py` and are evaluated entirely in
`fractions.Fraction`:

```
Psi(D) = ( C_M, C_25, C_50, C_100, T_25, T_50, T_100, M, sort_desc(D) )
C_z    = ceil(z / delta_z)          exact rational ceiling
T_a    = upper-tail mean at level a exact rational
```

No epsilon appears anywhere in this layer. A probe whose active range is at
most the retention threshold is **dropped**; nothing is ever added to a
denominator to keep it alive.

The `ceil` convention makes each cell closed on the right: a value sitting
exactly on `k*delta` belongs to cell `k`, not `k+1`. This is a decision of the
declared rule and is tested in `tests/test_numerical_contract.py`.

## 2. Floating-point selector (operational)

`Experimental/code/lexpr` selects in binary64, guards the disappointment
denominator with `EPS = 1e-9`, and snaps near-boundary categories by eight
machine epsilons for finite replay. That is a different mathematical object
from layer 1. It is retained for the study pipeline and is **not** certified.

`tests/test_numerical_contract.py` measures the agreement between the two
routes on the benchmark instead of assuming it, and
`certrelex.oracle.agrees_with_float_selector` reports any disagreement rather
than resolving it.

## 3. Certification arithmetic

`src/certrelex/interval.py`. Every elementary operation is evaluated in IEEE-754
binary64 under round-to-nearest and then pushed outward by exactly one
`numpy.nextafter` step. Round-to-nearest commits an error strictly below half
the local spacing and one `nextafter` step moves by the full local spacing, so
each directed result encloses the exact value; the property is maintained
inductively along a whole evaluation.

* **Subnormals are accepted.** The argument uses only the absolute
  round-to-nearest bound and the local spacing, both valid down to `2**-1074`.
  The relative error model `(1+delta)`, which does fail there, is not used.
* **Overflow and NaN are refused**, not widened: they break the enclosure.
* **Accumulation order is fixed.** `numpy.sum` is never used inside a certified
  path, because its pairwise association order depends on array length and on
  the build.
* **Comparison is exact.** Enclosure endpoints are binary64 numbers, hence
  exact rationals; profiles are compared in `Fraction` arithmetic with no tie
  tolerance.

## 4. Witness verifier

`src/certrelex/verify.py`. Independent by construction:

* it imports nothing from `interval.py` or `enclosure.py`;
* it is written entirely in exact `Fraction` arithmetic, so it cannot inherit a
  bug from the outward-rounded path;
* it knows nothing about gates, budgets or branching -- it is handed a leaf box
  and a claimed winner and recomputes the enclosure and the comparison;
* the singleton cancellation is **checked, not assumed**: the closed form is
  cross-checked against a direct evaluation at all four corners of the box, and
  the leaf is refused if any corner disagrees.

A leaf both routes accept has been certified twice, by different arithmetic.

## 5. What is not claimed

* The certified object is the exact rational rule of layer 1 applied to the
  stored binary64 criterion values. It is **not** a statement about the
  snapped operational rule of layer 2, and it is not a statement about the
  real-valued measurements those stored values approximate.
* "Not certified" always means "not certified within this budget". The engine
  is one-sided: a negative answer never bounds the radius from above. Upper
  bounds come only from verified switch witnesses (`certrelex.oracle`).
* Refusing a box (collapsed range, unretained probe, overflow) leaves it
  unresolved. Refusal never weakens soundness and never silently becomes
  positive stability.
* Tied nominal optima are recorded and skipped. A set-preservation contract for
  ties is not defined here and is not claimed.
