"""Referee point 3 (round 3): the selector, the audit record and the verifier
must implement ONE decision rule, and it must be the real-valued LexPR order of
the paper -- not a grid-quantised surrogate. Quantisation would make the
implemented rule a different rule: two distinct profiles can become tied, and
strict Pareto compatibility can fail."""
import numpy as np
from lexpr.methods import leximax_argmin
from lexpr.verify import _lex_cmp
from lexpr.audit import _lex_argmin_class


def test_no_quantisation_anywhere():
    """A profile pair that a 1e-9 grid would tie but the exact order separates."""
    D = np.array([[0.5 + 0.4e-9, 0.1],
                  [0.5,          0.2]])
    # descending-sorted rows are [0.5+4e-10, 0.1] and [0.5, 0.2]. On a 1e-9
    # grid both leading coordinates round to 0.5, the grid falls through to the
    # second coordinate and picks row 0. The exact order compares the leading
    # coordinates, finds 0.5 < 0.5+4e-10, and picks row 1.
    assert leximax_argmin(D) == 1, "selector still quantises"
    srt = [sorted(r, reverse=True) for r in D]
    assert _lex_cmp(srt[1], srt[0]) == -1, "verifier still quantises"
    winners, _ = _lex_argmin_class(D)
    assert winners == [1], "audit record still quantises"


def test_strict_pareto_survives_a_tiny_margin():
    """Under quantisation a dominator separated by less than half a grid step
    would tie with the dominated alternative. Under the exact rule it wins."""
    D = np.array([[0.30, 0.20],
                  [0.30 + 1e-12, 0.20 + 1e-12]])
    assert leximax_argmin(D) == 0
    winners, _ = _lex_argmin_class(D)
    assert winners == [0], "dominated alternative tied with its dominator"


def test_verifier_agrees_with_selector_and_audit_record():
    rng = np.random.default_rng(7)
    for _ in range(300):
        D = rng.random((5, 4))
        # force near-ties at the scale where a grid would have mattered
        D[1] = D[0] + rng.choice([0.0, 0.4e-9, 1.6e-9], size=4)
        sel = leximax_argmin(D)
        aud, _ = _lex_argmin_class(D)
        srt = [sorted(row, reverse=True) for row in D]
        ver = [i for i in range(len(srt))
               if all(_lex_cmp(srt[i], srt[j]) <= 0 for j in range(len(srt)))]
        assert sel in aud, "selector and audit record disagree"
        assert sel in ver, "verifier and selector disagree"
