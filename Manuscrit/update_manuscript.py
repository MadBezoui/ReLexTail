import re

def update_theory():
    with open("theory_relex.tex", "r") as f:
        content = f.read()
    
    # 4.2 Define how vector is embedded
    content = content.replace(
        r"\[ \Psi(x) = \Bigl(C_M(x), C_{25}(x), C_{50}(x), C_{100}(x), T_{25}(x), T_{50}(x), T_{100}(x), M(x), D^\downarrow(x)\Bigr). \]",
        r"\[ \Psi(x) = \Bigl(C_M(x), C_{25}(x), C_{50}(x), C_{100}(x), T_{25}(x), T_{50}(x), T_{100}(x), M(x), D_{[1]}(x), \ldots, D_{[K]}(x)\Bigr). \]\n"
        r"Note that $M(x) = D_{[1]}(x)$ is repeated. This repetition is harmless but redundant, present because $M$ has a specific position in the hierarchy while the complete sorted profile is used only for terminal refinement."
    )
    
    # 4.3 Category convention & 4.4 Ignored vs Deprioritised
    # Let's add the convention explanation right after the definition of B_delta
    content = content.replace(
        r"\[ B_\delta(z) = \left\lceil \frac{z}{\delta} \right\rceil. \]",
        r"\[ B_\delta(z) = \left\lceil \frac{z}{\delta} \right\rceil. \]\n"
        r"Under this convention, $B_\delta(0) = 0$, and for $j \ge 1$, $B_\delta(z) = j \iff (j-1)\delta < z \le j\delta$. "
        r"Thus, the order is discontinuous at category boundaries. This intentional design distinguishes sensitivity within a category, sensitivity near a category boundary, and sensitivity of the exact-tail refinement."
    )
    
    # "differences below the resolution are ignored" -> check if exists in theory_relex or body
    # 4.5 Justify order of exact refinement
    content = content.replace(
        r"This defines a clear hierarchy: catastrophic-resolution protection, followed by tail categories, exact tail refinements, exact maximum refinement, and finally complete deterministic refinement via the exact leximax.",
        r"This defines a clear hierarchy: catastrophic-resolution protection, followed by tail categories, exact tail refinements, exact maximum refinement, and finally complete deterministic refinement via the exact leximax. "
        r"Every material category difference has priority over every within-category numerical difference. "
        r"Furthermore, putting exact $M$ immediately after $C_M$ would recreate the exact-leximax priority inside every maximum category. ReLexTail therefore postpones exact maximum comparison until after broader tail comparisons."
    )
    
    # 5.1 CVaR Definition & 5.2 Finite formula
    content = content.replace(
        r"For finite computation with $h = \alpha K$, $k = \lfloor h \rfloor$, and $\theta = h - k$:",
        r"The probe coordinates are treated as equally weighted atoms of an empirical disappointment distribution. "
        r"For finite computation with $h = \alpha K$, $k = \lfloor h \rfloor$, and $\theta = h - k$:"
    )
    content = content.replace(
        r"\[ T_\alpha(x) = \frac{\sum_{j=1}^{k} D_{[j]}(x) + \theta D_{[k+1]}(x)}{h}. \]",
        r"\[ T_\alpha(x) = \frac{\sum_{j=1}^{k} D_{[j]}(x) + \theta D_{[k+1]}(x)}{h}, \]\n"
        r"with the conventions that an empty sum is zero, if $\theta=0$ the $D_{[k+1]}$ term is omitted, and if $h<1$ then $k=0$, $\theta=h$, and $T_\alpha(x) = D_{[1]}(x) = M(x)$. Note also that $T_1(x) = \frac{1}{K}\sum_{q=1}^K D_q(x)$."
    )
    
    # 6.3 Theorem 3
    content = content.replace(
        r"\begin{theorem}[Weak and Strict Pareto compatibility]",
        r"\begin{theorem}[Profile monotonicity and Criterion-level Pareto compatibility]"
    )
    content = content.replace(
        r"If $D_q(x) \leq D_q(y)$ for all $q$, then $x \preceq_{\mathrm{ReLexTail}} y$. Furthermore, if $D(x) \leq D(y)$ and $D(x) \neq D(y)$, then $x \prec_{\mathrm{ReLexTail}} y$.",
        r"Profile monotonicity: If $D(x) \leq D(y)$, then $x \preceq_{\mathrm{ReLexTail}} y$. If strictly less somewhere, $x \prec_{\mathrm{ReLexTail}} y$. "
        r"Criterion-level Pareto compatibility: If $x$ Pareto-dominates $y$, retained probes are monotone, and the family separates criteria after degeneracy removal, then $x \prec_{\mathrm{ReLexTail}} y$."
    )
    content = content.replace(
        r"ensures strict preference.",
        r"ensures strict preference, since no earlier category can favour $y$ because all category maps are nondecreasing. Hence the strict mean difference will eventually decide in favour of $x$ if no earlier coordinate already does."
    )
    
    # 6.7 & 6.8 Theorem 5
    old_thm_5 = r"""\begin{theorem}[Bin-boundary stability]
If all compared alternatives remain within their nominal resolution cells and the exact tail margin at the first post-category decisive coordinate exceeds twice the perturbation bound, the ReLexTail winner is unchanged.
\end{theorem}"""
    
    new_thm_5 = r"""\begin{lemma}[Category stability]
Empirical upper-tail CVaR and the maximum are $1$-Lipschitz in the supremum norm. 
For any risk coordinate $R_\ell \in \{M, T_{25}, T_{50}, T_{100}\}$, define the distance to the nearest category boundary as $\mu_\ell(x) = \operatorname{dist}(R_\ell(x), \delta_\ell \mathbb{Z})$. Let $\mu_{\mathrm{cell}} = \min_{x\in A, \ell} \mu_\ell(x)$. If a perturbation satisfies $\eta < \mu_{\mathrm{cell}}$, then every candidate remains in the same category on every category coordinate.
\end{lemma}

\begin{theorem}[Winner stability]
Once categories are fixed, comparison proceeds through exact coordinates. 
If the winner $x^\star$ is separated from every rival $y$ at the first exact coordinate $j(y)$ after the category block, and $\Delta_{\mathrm{exact}} = \min_{y \neq x^\star} [\Psi_{j(y)}(y) - \Psi_{j(y)}(x^\star)]$, then if $2\eta < \Delta_{\mathrm{exact}}$ and all categories remain unchanged, the winner remains unchanged.
\end{theorem}"""
    content = content.replace(old_thm_5, new_thm_5)
    
    with open("theory_relex.tex", "w") as f:
        f.write(content)

def update_part2():
    with open("part2.tex", "r") as f:
        content = f.read()
    
    # 7.1 Certified analysis
    content = content.replace(
        r"\reg^{\downarrow}\!\big(\reg^{U}(x;\beta)\big)\lex",
        r"\Psi\!\big(\reg^{U}(x;\beta)\big)\lex"
    )
    content = content.replace(
        r"\reg^{\downarrow}\!\big(\reg^{L}(y;\beta)\big)",
        r"\Psi\!\big(\reg^{L}(y;\beta)\big)"
    )
    
    # 3.2 Conclusion
    old_conclusion = r"The takeaway is not a new decision rule. The ordering is classical and we claim nothing for it."
    new_conclusion = r"This paper introduced a deterministic resolution-aware lexicographic order over upper-tail probe-disappointment profiles. The order differs from exact leximax by assigning priority to declared resolution categories before exact tail refinements."
    content = content.replace(old_conclusion, new_conclusion)
    
    with open("part2.tex", "w") as f:
        f.write(content)

def update_body():
    with open("body.tex", "r") as f:
        content = f.read()
        
    # 3.1 Abstract
    old_abstract = r"A study over five thousand instances demonstrates that ReLexTail provides a controlled quality--stability compromise absent in exact leximax or weighted sum scalarisations."
    new_abstract = r"The empirical study evaluates whether the resolution-aware order improves the quality--stability trade-off relative to exact leximax and scalar aggregations applied to the same disappointment representation."
    content = content.replace(old_abstract, new_abstract)
    
    # 4.4 "ignored"
    old_ignored = r"differences below the resolution are ignored"
    new_ignored = r"differences within the same resolution category do not receive category-level priority and are considered only during the exact refinement stages"
    content = content.replace(old_ignored, new_ignored)
    
    # 5.3 "worst quarter"
    old_quarter = r"exactly the worst quarter"
    new_quarter = r"the empirical upper 25\% tail, with fractional boundary weighting when necessary"
    content = content.replace(old_quarter, new_quarter)
    
    with open("body.tex", "w") as f:
        f.write(content)

update_theory()
update_part2()
update_body()
