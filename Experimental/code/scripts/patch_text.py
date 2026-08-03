import sys

replacements = {
    "main.tex": [
        # 1.1 Related-work paragraph
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

        # 1.2 Final related-work summary
        (r"""With a singleton probe $q$, LexPR reduces to minimising the active-set normalised
disappointment induced by $q$, so any declared monotone scalar score, including
ASF-type scores \citep{wierzbicki1980}, can be represented as a one-probe LexPR
rule, and minimax-regret-type rules \citep{savage1951,kouvelis1997} are recovered
when the declared probe itself is the corresponding worst-regret functional.
With several probes, LexPR first minimises the maximum probe regret and then
applies a lexicographic refinement.""",
r"""With a singleton probe $q$, LexPR is order-equivalent to minimising $q$ itself,
because active-range normalisation is a positive affine transformation of the
probe values. Thus, any declared monotone scalar score, including an ASF
\citep{wierzbicki1980}, can be represented exactly as a one-probe LexPR rule.
Likewise, a minimax-regret rule \citep{savage1951,kouvelis1997} is recovered when
the unique declared probe is the corresponding worst-regret functional. With
several probes, LexPR differs from any one-probe scalarisation: it minimises the
largest normalised probe disappointment and then applies a lexicographic
refinement to the remaining sorted disappointments."""),

        # 2. Positioning against lexicographic minimax
        (r"""LexPR adopts the regret viewpoint but measures a dimensionless disappointment per
probe and aggregates these regrets lexicographically, rather than collapsing them
into a single worst-case scalar over a weight set.""",
r"""LexPR adopts the regret viewpoint but measures a dimensionless disappointment
per declared probe and compares the resulting profile lexicographically. The
lexicographic minimax operation is classical
\citep{ogryczak1997,ogryczak2006direct}, and lexicographic refinements have also
been studied in scenario-based robustness, including lexicographic
$\alpha$-robustness \citep{kalai2012lexicographic}. LexPR does not claim a new
lexicographic minimax operator. Its contribution is the decision-aiding
architecture built around that operator: an explicitly declared family of
monotone probes, independent active-range normalisation of each probe, labelled
decision profiles, a reproducible audit record, and bound-stability diagnostics.
Unlike scenario-regret methods, the probe coordinates need not represent states
of nature. They represent declared decision questions and therefore remain
substantive preference inputs."""),

        # 3.1 Background opening
        (r"""LexPR keeps their goal of returning a defensible single choice but replaces those
numerical commitments with a declared family of monotone questions.""",
r"""LexPR keeps their goal of returning a defensible choice but replaces a single
global cardinal trade-off specification with a declared family of monotone
questions. This does not eliminate preference modelling: probe definitions,
overlap, multiplicities, aggregation forms, and normalisation conventions all
affect the resulting order."""),

        # 3.2 Probe preference inputs
        (r"""We stress that the declared probes, their multiplicities, and their aggregation
forms are themselves preference inputs. LexPR avoids precise trade-off
\emph{weights}, but it does not avoid preference modelling: the equal-weight grand
mean encodes a utilitarian reading, the grand maximum an egalitarian one, and
duplicating a probe acts as an integer replication in the ordered regret profile,
affecting tie-breaking and lower-order lexicographic comparisons rather than
scaling a coordinate as a scalar weight would.""",
r"""We stress that probe definitions, overlaps, multiplicities, aggregation forms,
and normalisation conventions are substantive preference inputs. LexPR does not
require a single global cardinal trade-off vector, but it does not eliminate
weighting or preference modelling. The equal-weight grand mean encodes a
compensatory reading, the grand maximum encodes a protective reading, and
duplicating a probe acts as an integer-valued emphasis mechanism in the ordered
profile. Moreover, representing one institutional concern through several
overlapping probes can increase its influence even when no probe is formally
duplicated. The complete declared multiset and an overlap or ablation analysis
must therefore be reported."""),

        # 3.3 Conclusion
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

        # 4.1 Introduction
        (r"""In each case LexPR reports a labelled regret certificate that identifies the
binding probes.""",
r"""In each case LexPR reports a labelled decision profile that identifies the
binding probes. Verification of optimality additionally requires a full audit
record containing the profiles of all candidates and the modelling metadata
needed to reconstruct the comparison."""),

        # 4.2 Figure 1 caption
        (r"""\caption{From Pareto filtering to an auditable recommendation: the selected point
carries a sorted, labelled regret certificate.}""",
r"""\caption{From Pareto filtering to a documented recommendation: the selected
point carries a sorted, labelled decision profile. A complete audit certificate
must additionally contain the rival profiles and all modelling metadata required
to reconstruct the comparison.}"""),

        # 4.3 Introductory explanation
        (r"""Because the recommendation is determined by the sorted vector of probe
disappointments, the same quantities provide a labelled certificate of the
choice: an ordered list of the binding probes and the residual regret on each.
The certificate is computed from the data that drive the selection, not appended
after the fact.""",
r"""Because the recommendation is determined by the sorted vector of probe
disappointments, the selected alternative can be accompanied by a labelled
decision profile: an ordered list of declared probes and their residual
disappointments. This profile is endogenous to the selection rule rather than
being appended post hoc. It explains the selected alternative but does not, by
itself, prove optimality. A verifiable audit certificate must also contain every
candidate's labelled profile and the modelling metadata required to reconstruct
the exact LexPR preorder."""),

        # 4.4 Section title and opening
        (r"""\subsection{The decision certificate}
\label{sec:certificate}
The recommendation is reported together with a formal certificate.""",
r"""\subsection{Decision profile and audit certificate}
\label{sec:certificate}

The recommended alternative is reported with a labelled decision profile. This
candidate-level object explains which declared probes are binding, but it is not
sufficient by itself to verify optimality. A complete audit certificate contains
the profiles of all candidates together with the candidate set, declared probe
multiset, criterion bounds, probe anchors, retained-probe decisions, degeneracy
thresholds, and exact tie and tolerance conventions."""),

        # 4.5 Definition following the profile
        (r"""For the recommended $x$, order the labelled disappointments descending as
$\reg_{q_{(1)}}(x)\ge\cdots\ge\reg_{q_{(K)}}(x)$ and write
\begin{equation}
\mathcal C(x)=\big((q_{(1)},\reg_{q_{(1)}}(x)),\dots,(q_{(K)},\reg_{q_{(K)}}(x))\big).
\label{eq:certificate}
\end{equation}""",
r"""For the recommended $x$, order the labelled disappointments descending as
$\reg_{q_{(1)}}(x)\ge\cdots\ge\reg_{q_{(K)}}(x)$ and define its decision profile
\begin{equation}
\mathcal C_{\mathrm{prof}}(x)
=
\big((q_{(1)},\reg_{q_{(1)}}(x)),\dots,
(q_{(K)},\reg_{q_{(K)}}(x))\big).
\label{eq:certificate}
\end{equation}
When equal disappointment values occur, labels are ordered by the fixed probe
identifier recorded in the declaration file. This secondary ordering affects
only reproducible display, not the LexPR preorder.

The complete audit certificate is
\[
\mathcal C_{\mathrm{audit}}
=
\left(
A,\,
\{\mathcal C_{\mathrm{prof}}(x):x\in A\},\,
\Q,\,
b,\,
\{q^\star,q^{\mathrm w}\}_{q\in\Q},\,
\varepsilon_z,\varepsilon,\tau,\,
\mathcal T
\right),
\]
where $\mathcal T$ records the retained-probe, tie-breaking, rounding, and
tolerance-cycle conventions."""),

        # 4.6 Proposition title
        (r"\begin{proposition}[Sufficiency of the full profile record]",
         r"\begin{proposition}[Sufficiency of the full audit record]"),
        
        # 4.7 Abstract
        (r"""Numerical experiments on exact Pareto fronts and a reproducible
supplier-selection case indicate that LexPR is competitive with robust
scalarisation rules on tail loss while additionally providing native regret
certificates, binding-probe diagnostics, and stability information.""",
r"""Numerical experiments on exact Pareto fronts and a reproducible constructed
supplier-selection case provide descriptive comparisons with representative
scalarisation rules. LexPR additionally reports labelled decision profiles,
binding-probe diagnostics, reproducible audit records, and stability information.
The reported performance is conditional on the declared evaluation scenarios and
does not establish general superiority."""),

        # 5. Stability statement probe values
        (r"Membership in $B_\beta(x)$ is unchanged by any uniform perturbation of probe values smaller than $\mu_\beta(x)/2$.",
         r"Membership in $B_\beta(x)$ is unchanged by any uniform perturbation of the normalised disappointment values smaller than $\mu_\beta(x)/2$. A perturbation bound stated on raw probe values requires the additional range condition and the conversion supplied by Lemma~\ref{thm:approx}."),
        
        # 6.1 Adaptive-family opening
        (r"LexPR always includes the $m$ singletons (required for separation), the grand mean, and the grand maximum.",
         r"The proposed reported family includes the $m$ singletons, the grand mean, and the grand maximum. The singletons are included to provide exact criterion-specific entries and to guarantee separation transparently. They are sufficient but not logically necessary for separation: for example, a non-degenerate grand mean with strictly positive coefficients is strictly increasing in every criterion."),

        # 6.2 Practical declaration
        (r"""First the \emph{base} questions: the $m$ singletons, mandatory for separation and
the strict Pareto guarantee, the grand mean as the utilitarian reading, and the
grand maximum as the egalitarian one.""",
r"""First the \emph{base} questions: the $m$ singletons, included for exact
criterion-level reporting and as a transparent sufficient condition for
separation, the grand mean as a compensatory reading, and the grand maximum as
a protective reading. The singletons are not mathematically mandatory for
strict Pareto compatibility if another retained non-degenerate probe family
already separates every criterion."""),
        
        # 9. Do not recommend \theta=0.6
        (r"""Second the \emph{redundancy} structure: we recommend the threshold $\theta=0.6$
used throughout, followed by a sensitivity check at $\theta\pm0.3$""",
r"""Second, the facilitator examines possible overlap among criteria. The numerical
experiments use $\theta=0.6$ as a declared illustrative setting, followed by a
sensitivity analysis over alternative thresholds. This value is not proposed as
a generally valid threshold. In applications, the threshold, linkage rule, and
cluster interpretation must be justified using the sample size, measurement
quality, and domain meaning of the criteria"""),

        # 12. Correct probe protocol weighting
        (r"the multiplicity field exposes the only admissible weighting device under F3,",
         r"the multiplicity field exposes explicit integer-valued replication. It is not the only source of emphasis: probe overlap, aggregation forms, cluster augmentation, and active-range normalisation also affect the comparison,"),

        # 13.1 Main deployment paragraph
        (r"with externally fixed bounds, report the point winner and its certificate.",
         r"with a version-frozen shortlist, externally fixed criterion bounds, externally fixed probe anchors, a fixed retained probe family, and a certified positive winning margin, report the point winner and its decision profile together with the full audit record. Fixing only the criterion bounds is insufficient when probe anchors are recomputed on a changing candidate set."),

        # 16. Remove tolerance from continuous algorithm
        (r"\textbf{Input:} polyhedral feasible set $\X$, affine criteria $f_i$, canonical probes, tolerance $\tau$.\\",
         r"\textbf{Input:} polyhedral feasible set $\X$, affine criteria $f_i$, and a fixed retained family of canonical probes.\\"),

        # 17. Add K=0 branch
        (r"\item Retain only probes with $q^{\mathrm w}-q^\star>\varepsilon$, and flag degenerate probes",
         r"\item Retain only probes with $q^{\mathrm w}-q^\star>\varepsilon$, and flag degenerate probes as non-informative for that run. If no probe is retained ($K=0$), return $W_0=W_\tau=A$, report that all alternatives are tied under the declared family, issue a ``no informative retained probe'' warning, and stop."),

        # 18.1 Before Algorithm 1
        (r"""Because the tolerance relation $\prec_\tau$ of \eqref{eq:wtau} is in general not transitive, computing $W_\tau$ as the set of $\prec_\tau$-undominated alternatives requires pairwise comparisons. With naive probe evaluation this costs
\[
O(NKm+NK\log K+NK),
\]
where $m$ is the number of criteria, $K$ the number of declared probes, and $N=|A|$ the size of the filtered candidate set. The first term builds the data matrix $r(x)$, the second sorts the regret vectors, and the third tests dominance.""",
r"""Because the tolerance relation $\prec_\tau$ of \eqref{eq:wtau} is in general not transitive, computing $W_\tau$ as the set of $\prec_\tau$-undominated alternatives requires pairwise comparisons. With naive probe evaluation, let $C_{\Q}$ denote the cost of evaluating all declared probes for one alternative. Computing the optimal class costs
\[
O(NC_{\Q}+NK\log K+NK).
\]
For the canonical singleton, weighted-mean, and maximum probes evaluated naively, $C_{\Q}=O(Km)$, giving $O(NKm+NK\log K+NK)$."""),

        # 18.2 Theorem 8
        (r"""With naive probe evaluation, computing $W_0$ requires
\[
O(NKm + NK\log K + NK)
\]
operations""",
r"""If $C_{\Q}$ is the cost of evaluating all retained probes for one candidate,
computing $W_0$ requires
\[
O(NC_{\Q}+NK\log K+NK)
\]
operations. For the canonical probes under naive $O(m)$ evaluation per probe,
this becomes
\[
O(NKm+NK\log K+NK)
\]
operations"""),

        # 26. Nadir terminology
        (r"\label{eq:norm}",
         r"""\label{eq:norm}
For a generic screened shortlist, $\ideal_i$ and $\nadir_i$ are active
criterion-wise best and worst values. They need not coincide with the true ideal
and nadir of the feasible outcome set. We retain the conventional notation but
use the term \emph{active bounds} when the distinction matters."""),

        # 27. Exact completeness
        (r"whereas LexPR always returns a complete order with a labelled certificate",
         r"whereas the exact LexPR rule induces a complete preorder with a labelled decision profile. The optional tolerance relation is not generally transitive and does not induce a complete preorder"),

        # 28. Abstract possible/necessary claim
        (r"""we provide an invariance condition and an interval-stability procedure that
reports possible and necessary winners under uncertain bounds.""",
r"""we provide an invariance condition and define exact possible and necessary
winner sets under uncertain bounds. When exact enumeration is unavailable, the
sampled procedure reports an observed winner union and a sample intersection,
with a one-sided coverage guarantee for winning regions of sufficiently large
probability."""),

        # 29. Certified selector language
        (r"Otherwise the \emph{certified selector} returns the interval possible and necessary winner sets. When the equality regions of \eqref{eq:interval} can be enumerated exactly, this class is the exact possible-winner set $S^{\mathrm{pos}}_\tau$.",
         r"Otherwise the robust reporting procedure returns the exact possible and necessary winner sets when they can be computed. Under Monte Carlo evaluation, it instead returns the observed winner union and sample intersection, which are one-sided approximations and are not exact certificates of possibility or necessity. When the equality regions of \eqref{eq:interval} can be enumerated exactly, this class is the exact possible-winner set $S^{\mathrm{pos}}_\tau$."),

        # 30. Runtime claim
        (r"As a rule of thumb, keeping $K\le 3m$ holds the selection well under a second for $N\le 1000$ candidates on standard hardware.",
         r"In the reported runtime microbenchmark, the configurations with $K\le3m$ and $N\le1000$ are evaluated using the hardware, software versions, probe implementations, and repetition counts documented in Table~\ref{tab:runtime}. This observation is implementation-specific and is not a general complexity guarantee."),

        # 31. Reproducibility paragraph
        (r"""Before final submission, the DOI and all scripts should be verified from a clean environment, and the manuscript values should be checked automatically against the archived \texttt{CSV} and \texttt{JSON} outputs.""",
r"""The archived release corresponding to this manuscript has been executed from a
clean environment. Its metadata use the same title and version as the submitted
manuscript. A regression test compares every generated table and figure value
against the archived \texttt{CSV} and \texttt{JSON} outputs. The exact archive
version, software environment, and source commit are:
\[
\texttt{archive version: \ArchiveVersion,\quad commit: \ArchiveCommit}.
\]"""),

        # 32. Supplement intro
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

        # 33. Caption
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

        # 34. Table S3
        (r"Criterion redundancy & Correlation cluster map and realised within-cluster correlation $\rho$.",
         r"Potential criterion overlap & Correlation map, sample size, linkage rule, realised within-cluster correlations, cluster-probe status, and no-clustering ablation. Correlation is treated as a diagnostic rather than proof of normative redundancy."),

        # 34.1 Final row of Table S3
        (r"Explanation can be slower & Short binding-probe certificate plus a full audit certificate.",
         r"Winner profile alone cannot verify optimality & Short labelled decision profile for interpretation, plus a full audit certificate containing all candidate profiles and modelling metadata.")
    ],

    "theory_core.tex": [
        # 7.1 Section title
        (r"\subsection{The redundancy problem and correlation clustering}",
         r"\subsection{Correlation diagnostics and optional cluster-level probes}"),
        
        # 7.2 Opening paragraph
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

        # 7.3 Correlation interpretation
        (r"""Redundancy is treated as positive correlation: two criteria that rise and fall
together carry duplicate information, whereas negatively correlated criteria
represent genuine trade-offs and must remain separate.""",
r"""Positive correlation is treated only as a diagnostic of possible informational
overlap, not as proof that two criteria are normatively redundant. Two highly
correlated criteria may still represent distinct institutional obligations.
Negatively correlated criteria generally indicate an observed trade-off, but
their substantive interpretation must likewise be assessed independently of the
correlation coefficient."""),

        # 7.4 Proposition interpretation
        (r"""Thus the discrepancy induced by summarising a redundant cluster by its mean is
controlled by the correlation gap $1-\rho$ and vanishes as $\rho\to1$.""",
r"""Thus, if the standardised criteria of a cluster were replaced by their empirical
cluster mean, the resulting mean-square descriptive discrepancy would be
controlled by the correlation gap $1-\rho$ and would vanish as $\rho\to1$.
This statement concerns a hypothetical compression operation. It does not by
itself justify adding cluster probes while retaining all singleton probes, and
it does not establish a reduction in ranking bias."""),

        # 7.5 Qualification paragraph
        (r"""This is a computational reduction of the exponential coalition family, and any
reduction of redundancy bias relative to the canonical family is an empirical
claim rather than a theorem.""",
r"""The implemented family is smaller than an illustrative family containing mean
and maximum probes for every nonempty coalition. However, that exponential
coalition family is not a normative baseline required by LexPR. Relative to the
canonical family, the implemented construction adds cluster-level coordinates
and can therefore increase the influence of a clustered concern. No reduction
of redundancy bias follows from Proposition~\ref{prop:redund}."""),

        # 7.6 Adaptive-family description
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

        # 7.7 Section heading in the axiomatic core
        (r"\subsection{Correlation clustering as a redundancy-freeness heuristic}",
         r"\subsection{Correlation clustering as an overlap diagnostic}"),

        # 7.8 Axiomatic-core description
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

        # 7.9 Final sentence
        (r"""The clustering threshold $\theta$ is the only correlation parameter and is
reported with a sensitivity check, so the approximate redundancy control remains
as auditable as the exact family axioms.""",
r"""The clustering threshold $\theta$, linkage rule, realised within-cluster
correlations, and cluster-probe status are all reported. This makes the overlap
diagnostic reproducible, but it does not transform correlation clustering into
an axiomatic redundancy-control guarantee."""),

        # 8. Near duplicates
        (r"""Near-duplicate probes are handled by the correlation clustering above, with the
realised within-cluster correlation $\rho$ reported alongside the threshold
$\theta$.""",
r"""Potentially overlapping criteria are diagnosed through the correlation map, with
the realised within-cluster correlations reported alongside the threshold
$\theta$ and the linkage rule. Correlation clustering does not remove
near-duplicate singleton probes in the implemented family. Any additional
cluster probes are therefore treated as deliberate emphasis choices and are
examined through ablation and overlap sensitivity analyses."""),

        # 19. Proof of K=1
        (r"""For $K=1$ a profile is a single number, and A2 states
$d\preceq_1 e\iff d\le e$,""",
r"""For $K=1$ a profile is a single number. If $d\le e$, A2 gives
$d\preceq_1 e$. If $d>e$, A2 gives $e\prec_1 d$, which excludes
$d\preceq_1 e$. Hence $d\preceq_1 e\iff d\le e$,""")
    ],

    "experiments_new.tex": [
        # 10. Supplier cluster description
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

        # 11.1 Main ablation paragraph
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

        # 11.2 "Only the full family"
        (r"Only the full adaptive family combines a discriminating, readable certificate with competitive tail loss.",
         r"Both the full family and the no-clustering family select S7 and produce the same reported held-out losses. The full family additionally reports two cluster-level environmental questions, whereas the no-clustering family provides the same selection with fewer probe coordinates."),

        # 11.3 Deduplication
        (r"the recommendation is not an artefact of duplicate probes.",
         r"the recommendation is not an artefact of exact positive-affine duplicate probes in this instance. This check does not rule out influence from overlapping but non-identical probes."),

        # 11.4 Random-probe interpretation
        (r"so the behaviour of LexPR on this instance comes from the declared structure of the family rather than from lexicographic sorting alone.",
         r"so this single diagnostic illustrates that LexPR outcomes can depend materially on the declared probe family. One randomly generated family is not sufficient to quantify general probe-family sensitivity, and the result should not be interpreted as validation of the chosen family."),

        # 11.5 Ablation table caption
        (r"A near-zero value indicates a flat certificate in which no declared probe registers a binding concern.",
         r"A small value indicates that the selected alternative is relatively close to the active best value of every retained probe. It does not imply that no probe is binding: when the retained family is nonempty, at least one probe attains the maximum disappointment. Moreover, the maximum alone does not establish that the entire profile is flat."),

        # 14. Sampled necessity from near-necessity
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

        # 14.1 Supplier result
        (r"with S7 modal in 98\% of draws and no necessary winner",
         r"with S7 modal in 98\% of draws under the declared sampling distribution, an empty strict sample intersection, and an empty reported $0.99$ near-necessity frequency set"),

        # 15. Clarify separate seeds in Figure 6
        (r"the recommendation changes in 18\% of draws at $20\%$ bound error",
         r"the recommendation changes in 18\% of the $300$ point-flip trials at $20\%$ bound error. This estimate uses a separate seed and sample from the $500$ draws used to construct the observed winner union and modal-frequency summary, so the reported flip rate and modal frequency need not sum exactly to one."),

        # 24. Rename "held-out preferences"
        (r"held-out preference families", r"researcher-declared evaluation families"),
        (r"held-out preference scenarios", r"held-out evaluation scenarios"),

        # 25. Clarify supplier environmental zeros
        (r"The environmental singletons and cluster probes have zero disappointment under the nominal active anchors.",
         r"The environmental singletons and cluster probes have zero disappointment relative to the nominal active shortlist anchors. This is a shortlist-relative statement and does not imply zero environmental impact or compliance with any external environmental target."),

        # 35. Supplier certificate language
        (r"They do not by themselves prove optimality without the rival profiles and audit data.",
         r"They form a candidate-level decision profile and do not by themselves verify optimality. Verification requires the rival profiles and the complete audit record specified in Proposition~\ref{thm:represent}."),

        # 36. All probes bind
        (r"no probe registering a binding concern",
         r"no retained aggregate probe displaying a large disappointment under the chosen display threshold"),

        # 37. Exact Pareto-front/stress-front structure
        (r"\subsection{Selection after Pareto-front representation}",
         r"\subsection{Selection after exact Pareto-front enumeration}\label{sec:exp-knapsack}")
    ]
}

# Apply replacements
for filename, reps in replacements.items():
    filepath = f"../paper/build/{filename}"
    with open(filepath, "r") as f:
        text = f.read()

    for i, (old, new) in enumerate(reps):
        if old not in text:
            print(f"Warning: String not found in {filename} (Replacement {i+1}):\n{old[:100]}...")
        else:
            text = text.replace(old, new)

    with open(filepath, "w") as f:
        f.write(text)

print("Patching complete.")
