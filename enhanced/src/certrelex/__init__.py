"""CertReLex: decision-focused, dependency-preserving certification for ReLexTail.

Modules
-------
:mod:`certrelex.interval`
    Outward-rounded binary64 interval arithmetic and the shared-anchor
    quotient primitive.
:mod:`certrelex.profile`
    Exact rational ReLexTail profiles (the reference semantics).
:mod:`certrelex.enclosure`
    Sound enclosures of the disappointment matrix over a bound box, in a
    dependency-preserving mode and a baseline independent mode.
:mod:`certrelex.certify`
    Decision-focused branch and bound, certified sets and the radius bracket.
:mod:`certrelex.oracle`
    Exact rational evaluation at a fixed bound vector; counterexample search.
:mod:`certrelex.verify`
    Independent replay verifier, written in exact arithmetic and deliberately
    sharing no code with the search path.
:mod:`certrelex.examples`
    The three frozen rational examples the theory section relies on.

Nothing in this package changes the declared decision rule.  On fixed inputs
the enhanced engine and the current submission engine select the same winner;
the difference is what they can prove about it and how fast.
"""

__version__ = "0.1.0"

from . import certify, enclosure, interval, oracle, profile, verify  # noqa: F401

__all__ = ["certify", "enclosure", "interval", "oracle", "profile", "verify"]
