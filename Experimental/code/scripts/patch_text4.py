import re
import os

def flex_replace(text, old_text, new_text):
    # Escape everything
    escaped_old = re.escape(old_text.strip())
    # Replace any sequence of literal spaces, newlines, or punctuation with a class that matches any of them
    # First unescape the punctuation we want to be flexible about
    pattern = re.sub(r'(\\\s|\\\.|\\,|\\:|\\;|\-)+', r'[\\s\\.\\,\\:\\;\\-]+', escaped_old)
    
    new_text_fixed, count = re.subn(pattern, new_text.replace('\\', '\\\\'), text, count=1)
    if count == 0:
        print(f"FAILED to find:\n{old_text[:80]}...")
    return new_text_fixed

replacements = {
    "main.tex": [
        (r"""ASF is thus LexPR's closest scalarisation rival, and LexPR indeed recovers an
ASF-style rule as the special case of a singleton probe family. The two rules
are nevertheless not equivalent in general, even with singleton probes: LexPR
refines the worst regret lexicographically through the entire sorted regret
vector, whereas the augmented Chebyshev ASF breaks worst-case ties by a small
additive term, and these tie-breakers can select different alternatives.
Section~\ref{sec:exp-knapsack} quantifies where the selections agree and diverge
in practice.""", 
r"""ASF is one of LexPR's closest scalarisation comparators. If the declared family
contains a single probe,
\[
\Q=\{q\},
\]
then LexPR is order-equivalent to minimising that probe, because
\[
\reg_q(x)
=
\frac{q(r(x))-q^\star}{q^{\mathrm w}-q^\star}
\]
is a positive affine transformation of $q(r(x))$. Consequently, if $q$ is a
complete augmented achievement scalarising function, one-probe LexPR induces
exactly the same preorder and the same optimal set as that ASF. A genuinely new
lexicographic refinement arises only when several probes are declared. In that
case LexPR first minimises the largest normalised probe disappointment and then
refines ties through the remaining sorted disappointments. Section~\ref{sec:exp-knapsack}
reports empirical agreement and disagreement between the multi-probe LexPR rule
and the specified ASF baseline."""),

        (r"""LexPR is most appropriate when stakeholders can defend a finite set of monotone
questions, accept worst-first comparison across those questions, and can support
the governance required to freeze and version the shortlist, bounds, anchors,
and probe family.""",
r"""LexPR is most appropriate when stakeholders cannot defend a single precise
global trade-off vector but can defend a finite set of monotone questions,
including their mathematical forms, overlaps, multiplicities, and aggregation
interpretations. They must also accept worst-first comparison across those
questions and support the governance required to freeze and version the
shortlist, criterion bounds, probe anchors, and probe family."""),

        (r"\begin{proposition}[Sufficiency of the full profile record]",
         r"\begin{proposition}[Sufficiency of the full audit record]"),
        
        (r"\textbf{Input:} polyhedral feasible set $\X$, affine criteria $f_i$, canonical probes, tolerance $\tau$.\\",
         r"\textbf{Input:} polyhedral feasible set $\X$, affine criteria $f_i$, and a fixed retained family of canonical probes.\\"),

        (r"\item Retain only probes with $q^{\mathrm w}-q^\star>\varepsilon$, and flag degenerate probes",
         r"\item Retain only probes with $q^{\mathrm w}-q^\star>\varepsilon$, and flag degenerate probes as non-informative for that run. If no probe is retained ($K=0$), return $W_0=W_\tau=A$, report that all alternatives are tied under the declared family, issue a ``no informative retained probe'' warning, and stop."),

        (r"whereas LexPR always returns a complete order with a labelled certificate",
         r"whereas the exact LexPR rule induces a complete preorder with a labelled decision profile. The optional tolerance relation is not generally transitive and does not induce a complete preorder"),

        (r"""Before final submission, the DOI and all scripts should be verified from a clean
environment, and the manuscript values should be checked automatically against
the archived \texttt{CSV} and \texttt{JSON} outputs.""",
r"""The archived release corresponding to this manuscript has been executed from a
clean environment. Its metadata use the same title and version as the submitted
manuscript. A regression test compares every generated table and figure value
against the archived \texttt{CSV} and \texttt{JSON} outputs. The exact archive
version, software environment, and source commit are:
\[
\texttt{archive version: \ArchiveVersion,\quad commit: \ArchiveCommit}.
\]"""),

        (r"""This supplement collects the proofs omitted from the main text (Section~S1), the
sampled interval and continuous algorithm listings (Section~S2), the compact
definitions of the baseline selection rules (Section~S3), the probe declaration
protocol template (Section~S4), and the illustrative figures referenced from the
main text (Section~S5).""",
r"""This supplement collects the proofs omitted from the main text (Section~S1), the
sampled interval and continuous algorithm listings (Section~S2), the baseline
rules and complete empirical evaluation protocol (Section~S3), the probe
declaration protocol (Section~S4), and the additional empirical tables,
convergence checks, runtime results, and illustrative figures (Section~S5)."""),

        (r"""\caption{Adaptive probe construction. Positively correlated (redundant) criteria
are grouped into clusters by thresholding the signed correlation at $\theta$.
Each nontrivial cluster contributes one mean and one max aggregate in place of
the exponential subcoalition aggregates, and singleton probes remain for
separation. Together with the two grand probes, the family has $m+2+2c$ probes,
where $c$ is the number of nontrivial clusters.}""",
r"""\caption{Optional cluster-level probe augmentation. Positive correlation flags
possible overlap but does not establish normative redundancy. Each
substantively validated nontrivial cluster may contribute one mean and one
maximum probe in addition to the retained singleton probes. The resulting
family has $m+2+2c$ probes, where $c$ is the number of clusters for which the
additional questions are explicitly approved. Because the singleton probes
remain, this construction augments rather than compresses the selection
profile.}"""),

        (r"\scriptsize(separation)",
         r"\scriptsize(criterion-level reporting; sufficient for separation)"),

        (r"Criterion redundancy & Correlation cluster map and realised within-cluster correlation $\rho$.",
         r"Potential criterion overlap & Correlation map, sample size, linkage rule, realised within-cluster correlations, cluster-probe status, and no-clustering ablation. Correlation is treated as a diagnostic rather than proof of normative redundancy."),

        (r"Explanation can be slower & Short binding-probe certificate plus a full audit certificate.",
         r"Winner profile alone cannot verify optimality & Short labelled decision profile for interpretation, plus a full audit certificate containing all candidate profiles and modelling metadata.")
    ],

    "theory_core.tex": [
        (r"\subsection{The redundancy problem and correlation clustering}",
         r"\subsection{Correlation diagnostics and optional cluster-level probes}"),
        
        (r"""Real criteria are frequently redundant, several of them tracking one underlying
concern. An averaging rule then over-weights that concern by counting it once per
member. We propose an adaptive probe family that summarises coalition redundancy
with a linear number of probes, bound in mean square the discrepancy of the
cluster-mean summary, and assess the bias effect empirically in the ablation of
Section~\ref{sec:supplier-ablation}.""",
r"""Real criteria may be positively associated because they partly measure the same
underlying concern. We use correlation clustering as a diagnostic for such
overlap and, when substantively justified by stakeholders, add a cluster mean
and a cluster maximum as explicit cluster-level questions. Because the
implemented family retains all singleton probes and adds these cluster probes,
the construction is not a mathematical redundancy-reduction mechanism. It may
increase the representation of the clustered concern in the sorted profile.
Cluster probes must therefore be interpreted as deliberate additional emphasis,
and their influence must be evaluated through deletion, overlap, and threshold
sensitivity analyses."""),

        (r"""Redundancy is treated as positive correlation: two criteria that rise and fall
together carry duplicate information, whereas negatively correlated criteria
represent genuine trade-offs and must remain separate.""",
r"""Positive correlation is treated only as a diagnostic of possible informational
overlap, not as proof that two criteria are normatively redundant. Two highly
correlated criteria may still represent distinct institutional obligations.
Negatively correlated criteria generally indicate an observed trade-off, but
their substantive interpretation must likewise be assessed independently of the
correlation coefficient."""),

        (r"""Thus the discrepancy induced by summarising a redundant cluster by its mean is
controlled by the correlation gap $1-\rho$ and vanishes as $\rho\to1$.""",
r"""Thus, if the standardised criteria of a cluster were replaced by their empirical
cluster mean, the resulting mean-square descriptive discrepancy would be
controlled by the correlation gap $1-\rho$ and would vanish as $\rho\to1$.
This statement concerns a hypothetical compression operation. It does not by
itself justify adding cluster probes while retaining all singleton probes, and
it does not establish a reduction in ranking bias."""),

        (r"""This is a computational reduction of the exponential coalition family, and any
reduction of redundancy bias relative to the canonical family is an empirical
claim rather than a theorem.""",
r"""The implemented family is smaller than an illustrative family containing mean
and maximum probes for every nonempty coalition. However, that exponential
coalition family is not a normative baseline required by LexPR. Relative to the
canonical family, the implemented construction adds cluster-level coordinates
and can therefore increase the influence of a clustered concern. No reduction
of redundancy bias follows from Proposition~\ref{prop:redund}."""),

        (r"""A redundant group now contributes two aggregate questions, one mean and one
maximum, instead of a larger family of coalition aggregates, a containment of
the coalition-level representation whose effect on redundancy bias is assessed
empirically, since the individual singletons stay in place.""",
r"""Each declared nontrivial cluster contributes two additional questions: a cluster
mean and a cluster maximum. These probes provide compensatory and protective
readings of the cluster, respectively. Because the individual singletons remain
in the selection family, this is an augmentation rather than a compression.
The cluster probes are retained only when their additional institutional meaning
is documented and their influence is assessed by an ablation analysis."""),

        (r"""The adaptive construction of \S\ref{sec:probes} extends F2 from exact to
approximate redundancy by grouping criteria whose pairwise correlation over $A$
exceeds the declared threshold $\theta$ and adding, per nontrivial cluster, one
mean and one maximum aggregate rather than the exponential family of subcoalition
aggregates.""",
r"""The construction of \S\ref{sec:probes} uses correlation to flag possible
approximate overlap. For each substantively validated nontrivial cluster, it may
add one mean and one maximum probe. Since all singleton probes are retained,
this construction does not remove approximate duplicates and should not be
described as redundancy-freeness. It instead provides a linear-size set of
optional cluster-level questions whose influence is explicitly tested."""),

        (r"""Near-duplicate probes are handled by the correlation clustering above, with the
realised within-cluster correlation $\rho$ reported alongside the threshold
$\theta$.""",
r"""Potentially overlapping criteria are diagnosed through the correlation map, with
the realised within-cluster correlations reported alongside the threshold
$\theta$ and the linkage rule. Correlation clustering does not remove
near-duplicate singleton probes in the implemented family. Any additional
cluster probes are therefore treated as deliberate emphasis choices and are
examined through ablation and overlap sensitivity analyses."""),

        (r"""For $K=1$ a profile is a single number, and A2 states
$d\preceq_1 e\iff d\le e$,""",
r"""For $K=1$ a profile is a single number. If $d\le e$, A2 gives
$d\preceq_1 e$. If $d>e$, A2 gives $e\prec_1 d$, which excludes
$d\preceq_1 e$. Hence $d\preceq_1 e\iff d\le e$,""")
    ],

    "experiments_new.tex": [
        (r"""the adaptive construction of \S\ref{sec:probes} recovers exactly one redundant
cluster and summarises the environmental pair with a single mean and a single max
aggregate, instead of letting redundant coalition aggregates proliferate, while
the two singletons are retained for separation.""",
r"""the declared correlation diagnostic of \S\ref{sec:probes} identifies one
candidate overlap cluster, $\{\text{GHG},\text{Energy}\}$. The implemented family
retains both environmental singletons and adds a cluster mean and a cluster
maximum as two additional environmental questions. This augmentation does not
remove redundancy and may increase the representation of the environmental
concern. Its influence is therefore reported through the no-clustering ablation."""),

        (r"""Removing the correlation clustering leaves the recommendation and the held-out
loss unchanged: the redundancy benefit of clustering manifests as
redundancy-bias control, not as a winner change here where the singletons already
carry the decision, which indicates that clustering is a safe addition rather
than a liability on this instance.""",
r"""Removing the two cluster-level probes leaves the recommendation and the reported
held-out losses unchanged on this constructed instance. Therefore, this example
provides no evidence that the cluster augmentation improves decision quality or
reduces redundancy bias. It shows only that the two additional environmental
questions do not alter the selected supplier under the declared data and
settings."""),

        (r"Only the full adaptive family combines a discriminating, readable certificate with competitive tail loss.",
         r"Both the full family and the no-clustering family select S7 and produce the same reported held-out losses. The full family additionally reports two cluster-level environmental questions, whereas the no-clustering family provides the same selection with fewer probe coordinates."),

        (r"the recommendation is not an artefact of duplicate probes.",
         r"the recommendation is not an artefact of exact positive-affine duplicate probes in this instance. This check does not rule out influence from overlapping but non-identical probes."),

        (r"so the behaviour of LexPR on this instance comes from the declared structure of the family rather than from lexicographic sorting alone.",
         r"so this single diagnostic illustrates that LexPR outcomes can depend materially on the declared probe family. One randomly generated family is not sufficient to quantify general probe-family sensitivity, and the result should not be interpreted as validation of the chosen family."),

        (r"A near-zero value indicates a flat certificate in which no declared probe registers a binding concern.",
         r"A small value indicates that the selected alternative is relatively close to the active best value of every retained probe. It does not imply that no probe is binding: when the retained family is nonempty, at least one probe attains the maximum disappointment. Moreover, the maximum alone does not establish that the entire profile is flat."),

        (r"""re-evaluating LexPR over the box of plausible bounds, approximated by Monte Carlo
sampling ($M=500$ draws per uncertainty level, protocol in Section~S2 of the
online supplement), yields the sampled possible-winner set and the sampled
necessary-winner set.""",
r"""re-evaluating LexPR over the box of plausible bounds, approximated by Monte Carlo
sampling ($M=500$ draws per uncertainty level, protocol in Section~S2 of the
online supplement), yields the observed winner union
$\widehat S^{\mathrm{pos}}_\tau$, the strict sample intersection
$\widehat S^{\mathrm{nec}}_\tau$, and the separately reported near-necessity
frequency set $\widehat S^{0.99}_\tau$. The $0.99$ frequency set is not a
necessary-winner approximation."""),

        (r"with S7 modal in 98\% of draws and no necessary winner",
         r"with S7 modal in 98\% of draws under the declared sampling distribution, an empty strict sample intersection, and an empty reported $0.99$ near-necessity frequency set"),

        (r"the recommendation changes in 18\% of draws at $20\%$ bound error",
         r"the recommendation changes in 18\% of the $300$ point-flip trials at $20\%$ bound error. This estimate uses a separate seed and sample from the $500$ draws used to construct the observed winner union and modal-frequency summary, so the reported flip rate and modal frequency need not sum exactly to one."),

        (r"held-out preference families", r"researcher-declared evaluation families"),
        (r"held-out preference scenarios", r"held-out evaluation scenarios"),

        (r"The environmental singletons and cluster probes have zero disappointment under the nominal active anchors.",
         r"The environmental singletons and cluster anchors. This is a shortlist-relative statement and does not imply zero environmental impact or compliance with any external environmental target."),

        (r"They do not by themselves prove optimality without the rival profiles and audit data.",
         r"They form a candidate-level decision profile and do not by themselves verify optimality. Verification requires the rival profiles and the complete audit record specified in Proposition~\ref{thm:represent}."),

        (r"no probe registering a binding concern",
         r"no retained aggregate probe displaying a large disappointment under the chosen display threshold")
    ]
}

for filename, reps in replacements.items():
    filepath = f"../paper/build/{filename}"
    with open(filepath, "r") as f:
        text = f.read()

    for old_text, new_text in reps:
        text = flex_replace(text, old_text, new_text)

    with open(filepath, "w") as f:
        f.write(text)

print("Patching complete.")
