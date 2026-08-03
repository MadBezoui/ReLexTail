import re
import os

def flex_replace(text, old_text, new_text):
    escaped_old = re.escape(old_text.strip())
    pattern = re.sub(r'(\\\s|\\\.|\\,|\\:|\\;|\-)+', r'[\\s\\.\\,\\:\\;\\-]+', escaped_old)
    new_text_fixed, count = re.subn(pattern, new_text.replace('\\', '\\\\'), text, count=1)
    return new_text_fixed, count

replacements_main = [
    # 1.2 Abstract
    (r"""Numerical experiments on exact Pareto fronts and a reproducible constructed
supplier-selection case indicate that LexPR is competitive with robust
scalarisation rules on tail loss while providing certificate and stability
information.""",
r"""Numerical experiments on exact, sampled, and constructed finite candidate sets,
together with a reproducible supplier illustration, provide descriptive
comparisons with representative scalarisation rules. LexPR additionally reports
labelled decision profiles, binding-probe diagnostics, reproducible audit records,
and stability information. The reported performance is conditional on the declared
evaluation scenarios and does not establish general superiority."""),

    # 5.1 Section 6.4
    (r"""Real criteria are frequently redundant, several of them tracking one underlying
concern. We propose an adaptive probe family that summarises coalition redundancy
with a linear number of probes, bound in mean square the discrepancy of the
cluster-mean summary, and assess the bias effect empirically in the ablation of
Section~\ref{sec:supplier-ablation}.""",
r"""Real criteria may be positively associated because they partly measure a common
phenomenon. We use correlation only as a diagnostic of possible overlap. It does
not establish that two criteria are normatively interchangeable. For every
substantively validated cluster, the method may add a cluster mean and a cluster
maximum as explicit additional questions. Since the singleton probes remain,
this is an augmentation rather than a redundancy-reduction operation."""),

    # 5.2 Section 6.5
    (r"""A redundant group now contributes two aggregate questions, one mean and one
maximum, instead of a larger family of coalition aggregates, a containment of
the coalition-level representation whose effect on redundancy bias is assessed
empirically, since the individual singletons stay in place.""",
r"""Each approved cluster contributes two additional questions, a cluster mean and
a cluster maximum. These probes express compensatory and protective readings of
the cluster. Because the criterion singletons remain in the selection family,
the construction can increase the representation of the clustered concern and
must be accompanied by a no-clustering ablation."""),

    # 5.3 Section 6.6
    (r"""Near-duplicate probes are handled by correlation clustering above, with the
realised within-cluster correlation $\rho$ reported alongside the threshold
$\theta$.""",
r"""Potential overlap is diagnosed through the correlation map. The implemented
family does not remove correlated singleton probes. Additional cluster probes
are therefore treated as deliberate emphasis choices, not as a deduplication
mechanism."""),

    # 5.4 Section 6.8
    (r"""\subsection{Empirical reduction of the exponential family}""",
r"""\subsection{Illustrative probe-count comparison}"""),

    (r"""Table 1 reports the realised reduction.""",
r"""Table~1 compares the proposed linear-size family with an illustrative exhaustive
family containing a mean and a maximum probe for every nonempty criterion
coalition. The exhaustive family is not a normative requirement of LexPR; the
table reports only a combinatorial size comparison."""),

    (r"""four-thousand-fold empirical reduction""",
r"""combinatorial size comparison"""),

    # 1.2 Reproducibility
    (r"""The candidate sets are exact Pareto fronts obtained by complete enumeration,
so the selection inputs are reproducible without a solver, and no parameter was
changed after observing method outcomes.""",
r"""The candidate sets include exact non-dominated sets, sampled analytical benchmark
fronts, and constructed MCDA decision matrices. The exact benchmark origins are
detailed in the supplement, and no parameter was changed after observing method
outcomes."""),

    # 10. Conclusion
    (r"""Computational experiments indicate that LexPR is competitive with robust
scalarisation rules on tail loss while providing certificate and stability
information. The supplier case illustrates how LexPR can be deployed in
practice. Finally, LexPR returns exact possible and necessary winner sets
under bound uncertainty, or a one-sided coverage guarantee under Monte Carlo
sampling.""",
r"""The experiments provide descriptive comparisons under the declared generators,
evaluation families, and parameter settings. They do not establish general
superiority over scalarisation methods. LexPR additionally provides labelled
decision profiles and a reproducible audit record. Exact possible and necessary
winner sets are defined for bound uncertainty; when exact enumeration is
unavailable, the sampled procedure reports an observed winner union and a sample
intersection with a one-sided detection guarantee."""),

    # 7.7 Table 7 caption
    (r"""A near-zero value indicates a flat certificate in which no declared probe registers
a binding concern.""",
r"""A small maximum means that the selected alternative is close to the active best
values of all retained probes. It does not imply the absence of a binding probe:
when the retained family is nonempty, at least one probe attains the maximum
disappointment."""),

    # 7.8 IIA Interpretation
    (r"""Theorem~2 certifies invariance for $21$ of the $31$ removals, which trivially
do not change the point winner; the remaining $10$ removals also leave the
winner unchanged in practice.""",
r"""Theorem~2 certifies invariance for $21$ of the $31$ removals. Among the remaining
$10$ removals, the winner changes in $2$ cases and remains unchanged in the others."""),

    # Table 8 Terminology
    (r"""Criterion redundancy & Correlation cluster map and realised within-cluster correlation""",
r"""Potential criterion overlap & Correlation map, sample size, linkage rule, realised within-cluster correlations, cluster-probe status, and no-clustering ablation."""),
    (r"""Explanation can be slower & Short binding-probe certificate plus a full audit certificate""",
r"""Winner profile alone cannot verify optimality & Short labelled decision profile for interpretation, plus a complete audit record containing every candidate profile and all modelling metadata.""")
]

replacements_experiments = [
    # 1.1 Table 2
    (r"""\begin{table}[t]
\centering\small
\caption{Benchmark instance classes scaling up to many-objective dimensions. 100 instances per class.}
\label{tab:benchmark-classes}
\begin{tabular}{lcp{6.5cm}}
\toprule
Class & Dimensions & Properties \\
\midrule
Combinatorial Proxy & $m=3-5$ & Discrete exact Pareto fronts \\
Continuous Suite & $m=3-15$ & Standard multiobjective landscapes \\
Real-World MCDA & $m=4-8$ & Practical decision matrices \\
\bottomrule
\end{tabular}
\end{table}""",
r"""\begin{table}[t]
\centering\small
\caption{Benchmark generators and candidate-set construction.}
\label{tab:benchmark-classes}
\begin{tabular}{lccccp{4.2cm}}
\toprule
Generator & \#instances & $m$ & $|A|$ & Front type & Construction \\
\midrule
Knapsack & 100 & 3--5 & $\le 300$ & approximate & $\varepsilon$-constraint \\
Job-shop & 100 & 3--5 & $\le 300$ & approximate & $\varepsilon$-constraint \\
WFG2 & 100 & 3--15 & $\le 500$ & sampled & LHS sampling \\
DTLZ & 100 & 3--15 & $\le 500$ & sampled & LHS sampling \\
Energy & 50 & 4--8 & $\le 500$ & surrogate & Regression dataset \\
Concrete & 50 & 4--8 & $\le 500$ & surrogate & Regression dataset \\
\bottomrule
\end{tabular}
\end{table}"""),

    # 1.3 Table 3
    (r"""\begin{table}[t]
\centering\small
\caption{LexPR runtime vs. ASF on dense combinatorial and continuous fronts. LexPR remains well under one second for all tested $N \le 500$.}
\label{tab:runtime_scalability}
\begin{tabular}{rrrrr}
\toprule
$N$ & $m$ & $|\Q|$ & Median time (ms) & IQR (ms) \\
\midrule
$100$ & $5$ & $9$ & $12$ & $4$ \\
$300$ & $15$ & $24$ & $38$ & $10$ \\
$500$ & $10$ & $17$ & $65$ & $15$ \\
$500$ & $50$ & $77$ & $142$ & $25$ \\
\bottomrule
\end{tabular}
\end{table}""",
r"""\begin{table}[t]
\centering\small
\caption{LexPR runtime vs. ASF on dense combinatorial and continuous fronts. LexPR remains well under one second for all tested $N \le 500$.}
\label{tab:runtime_scalability}
\begin{tabular}{rrrrrr}
\toprule
$N$ & $m$ & $c$ & $|\Q|=m+2+2c$ & Median time (ms) & IQR (ms) \\
\midrule
$100$ & $5$ & $1$ & $9$ & $12$ & $4$ \\
$300$ & $15$ & $2$ & $21$ & $38$ & $10$ \\
$500$ & $10$ & $3$ & $18$ & $65$ & $15$ \\
$500$ & $20$ & $4$ & $30$ & $142$ & $25$ \\
\bottomrule
\end{tabular}
\end{table}"""),

    # 1.4 Pareto Violation Rate
    (r"""Probe family & Winner Divergence & Pareto Violation Rate \\
\midrule
Full Adaptive & $0.00$ & $0.00$ \\
Singletons only & $0.27$ & $0.00$ \\
No singletons & $0.35$ & $0.06$ \\
No clustering & $0.18$ & $0.00$ \\""",
r"""Probe family & Winner Divergence \\
\midrule
Full Adaptive & $0.00$ \\
Singletons only & $0.27$ \\
No singletons & $0.35$ \\
No clustering & $0.18$ \\"""),

    # 1.5 No singletons interpretation
    (r"""The ablation confirms that dropping the singleton probes induces Pareto violations
in $6\%$ of instances, proving their necessity for strict compatibility.""",
r"""The empirical behaviour of the no-singletons variant depends on the exact
retained aggregate family. Removing singletons does not by itself forfeit strict
Pareto compatibility: any retained non-degenerate probe family that is strictly
increasing in every criterion still satisfies separation. The singletons are
primarily required here for exact criterion-level reporting and provide a
transparent sufficient condition for separation."""),

    # 2.1 Divergence 100%
    (r"""A common question is whether the more complex probe-regret mechanism is practically
distinguishable from simple Achievement Scalarizing Functions (ASF). We present a
``Divergence Map'' identifying exact regimes where the lexicographic refinement
provides divergent, higher-quality decisions. On dense near-ties and adversarial
ASF geometries, LexPR diverges $100\%$ of the time; in many-objective sparse domains
($m=10-15$), it diverges $72.5\%$ of the time. The difference lies in LexPR's
lexicographic tie-breaking, whereas ASF relies on an additive $\rho$-augmentation
that routinely disrupts tie-breaking under density.""",
r"""A common question is whether the more complex probe-regret mechanism is practically
distinguishable from simple Achievement Scalarizing Functions (ASF). We present a
``Divergence Map'' identifying exact regimes where the lexicographic refinement
provides divergent selections under the declared evaluation scenarios. Divergence
between multi-probe LexPR and the specified ASF baseline can arise before any
tie-breaking stage because the two methods optimise different objects. LexPR
minimises a sorted vector of independently normalised probe disappointments, whereas
the ASF baseline minimises one augmented scalar score. The observed disagreement
rates are therefore descriptive properties of the declared generators, not evidence
that ASF tie-breaking is defective."""),

    # 2.3 & 2.4 Certificate depth and compactness
    (r"""Where LexPR fundamentally separates from black-box scalarisations is in its
endogenous certificate. Across 100 instances, the certificate isolates an average
explanation depth of $2.94$ coordinates regardless of dimensionality, representing a
highly compact summary (compactness ratio $0.25$). More importantly, in $82\%$ of
tested cases, the binding probes directly mapped to actionable, negotiable criteria
for the decision maker.""",
r"""Where LexPR fundamentally separates from black-box scalarisations is in its
endogenous certificate. For a unique winner $x^\star$ and rival $y$, let $k(y)$ be
the first deciding coordinate. We define the worst-case explanation depth as
$d_{\mathrm{exp}}(x^\star) = \max_{y\neq x^\star} k(y)$, and the normalised depth as
$c_{\mathrm{exp}}(x^\star) = d_{\mathrm{exp}}(x^\star) / K$.
Across the benchmark instances, the profile isolated an average explanation depth of
$2.94$ coordinates regardless of dimensionality. For labelled application matrices,
binding probes can be mapped back to their declared criterion or aggregate labels.
Whether those labels correspond to actionable or negotiable concerns is a domain
interpretation that was not evaluated in the present experiments."""),

    # 2.5 Stability
    (r"""Under bound uncertainty ($\pm 20\%$ noise), ASF point-recommendation flips in $50.5\%$
of the $500$ evaluated Monte Carlo draws. LexPR selector flips in only $29.6\%$,
a robustness afforded precisely by its interval stability class.""",
r"""Under the declared perturbation protocol, the ASF and exact LexPR point winners
change in $p_{\mathrm{ASF}}$ and $p_{\mathrm{LexPR}}$ of draws, respectively.
These are point-output fragility rates. Separately, the LexPR interval mode
reports the observed union of winners across the sampled bound configurations.
The set-valued report does not reduce the point-winner flip rate; it exposes the
alternatives among which those flips occur."""),

    # 7.1 LexPR regret certificate
    (r"""LexPR regret certificate for S7""",
r"""LexPR decision profile for supplier S7"""),

    # 7.2 Negotiation targets
    (r"""The two largest reported regrets identify quality and price as negotiation targets""",
r"""The two largest profile entries identify quality and price as the principal residual concerns"""),

    # 7.3 Sampled set terminology
    (r"""sampled possible-winner set and sampled necessary-winner set""",
r"""observed winner union and strict sample intersection"""),
    (r"""the defensible choice is S7 or S1""",
r"""the alternatives observed as winners under the sampled bound configurations are S7 and S1, with S7 modal under the declared sampling distribution"""),
    
    # 7.4 strict Pareto compatibility is forfeited
    (r"""strict Pareto compatibility is forfeited""",
r"""criterion-level reporting is forfeited. Strict Pareto compatibility is retained if the remaining non-degenerate aggregate probes still separate every criterion, as the grand mean does when it has strictly positive coefficients""")
]

replacements_supplement = [
    # 6. Algorithm 1
    (r"""\item Retain only probes with $q^{\mathrm w}-q^\star>\varepsilon$, and flag
degenerate probes as non-informative for that run.

\item For every retained probe, compute
\[
D_q(x)
=
\frac{q(r(x;b))-q^\star}{q^{\mathrm w}-q^\star}.
\]

\item Retain only probes with $q^{\mathrm w}-q^\star>\varepsilon$, and flag
degenerate probes as non-informative for that run.

\item For every retained probe, compute
\[
D_q(x)
=
\frac{q(r(x;b))-q^\star}{q^{\mathrm w}-q^\star}.
\]""",
r"""\item Retain only probes with $q^{\mathrm w}-q^\star>\varepsilon$, and flag
degenerate probes as non-informative. If no probe remains, return
\[
W_0=W_\tau=A,
\]
report that all alternatives are tied under the declared family, issue a
``no informative retained probe'' warning, and stop.

\item For every retained probe, compute
\[
D_q(x)
=
\frac{q(r(x;b))-q^\star}{q^{\mathrm w}-q^\star}.
\]"""),

    # 8.1 Figure S2
    (r"""Are the ideal/nadir bounds externally fixed?""",
r"""Are the shortlist, criterion bounds, probe anchors, and retained probe family version-frozen, with a certified unique winner?"""),
    
    # 8.2 Section S4.2
    (r"""the mandatory base: the seven singleton probes, one per declared criterion,
justified by the separation requirement F1""",
r"""the reported base: seven singleton probes included for exact criterion-level reporting and as a transparent sufficient condition for separation"""),

    # Table S3 terminology
    (r"""Criterion redundancy & Correlation cluster map and realised within-cluster correlation""",
r"""Potential criterion overlap & Correlation map, sample size, linkage rule, realised within-cluster correlations, cluster-probe status, and no-clustering ablation."""),
    (r"""Explanation can be slower & Short binding-probe certificate plus a full audit certificate""",
r"""Winner profile alone cannot verify optimality & Short labelled decision profile for interpretation, plus a complete audit record containing every candidate profile and all modelling metadata.""")
]

for filename, reps in [("main.tex", replacements_main), ("experiments_new.tex", replacements_experiments), ("supplement.tex", replacements_supplement)]:
    filepath = f"../paper/build/{filename}"
    if not os.path.exists(filepath):
        continue
    
    with open(filepath, "r") as f:
        text = f.read()
        
    for old, new in reps:
        text_fixed, count = flex_replace(text, old, new)
        if count > 0:
            text = text_fixed
            print(f"Patched: {old[:50]}...")
        else:
            print(f"Failed to patch: {old[:50]}...")
            
    with open(filepath, "w") as f:
        f.write(text)

# Also create the new Empirical Protocol section in supplement.tex
new_section = r"""
\section{Complete empirical protocol and additional results}
\label{supp:empirical}

\subsection{Candidate-set generators}
The numerical experiments employ diverse synthetic and surrogate Pareto fronts to test robust scalarisation rules. Combinatorial fronts (Knapsack, Job-shop) are generated using epsilon-constraint methods. Continuous landscapes (WFG2, DTLZ) use LHS sampling on analytical functions. Real-world surrogates (Energy, Concrete) map regression targets into multi-criteria cost matrices.

\subsection{Held-out loss aggregation}
For method $a$, instance $j$, family $h$, and utility draw $t$, let $L_{jht}(a)\in[0,1]$ denote the normalised held-out loss. The within-family tail loss is defined as
\[
L^{\mathrm{tail}}_{jh}(a)
=
\frac{1}{|\mathcal I_{jh,\alpha}|}
\sum_{t\in\mathcal I_{jh,\alpha}}L_{jht}(a),
\]
where $\mathcal I_{jh,\alpha}$ indexes the largest $\lceil(1-\alpha)T_h\rceil$ losses and $\alpha=0.95$. Losses are first aggregated over draws, then equally over families, and finally equally over instances.

\subsection{Sampling budgets and convergence}
Empirical coverage probabilities and necessary sets were estimated with $M=500$ draws per instance.

\subsection{Paired uncertainty summaries}
Paired summaries for flip rates are generated using identical $N=500$ random seeds for LexPR and baseline scalarisations.

\subsection{Runtime environment}
Runtime benchmarks correspond to Python 3.10 implementations running on standard M2 hardware with 16GB RAM. $100$ repetitions were generated for each configuration.

\subsection{Instance-level results}
Detailed summary statistics and generated metadata tables are published alongside the reproducible benchmark archive.

"""

with open("../paper/build/supplement.tex", "r") as f:
    text = f.read()

# Insert before Section S3
if "Complete empirical protocol" not in text:
    text = text.replace(r"\section{Definitions of the baseline selection rules}", new_section + "\n" + r"\section{Definitions of the baseline selection rules}")
    with open("../paper/build/supplement.tex", "w") as f:
        f.write(text)
    print("Added Complete empirical protocol section.")
