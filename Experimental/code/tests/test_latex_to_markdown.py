from pathlib import Path

from lexpr.latex_to_markdown import (
    ConversionOptions,
    LatexProjectConverter,
    convert_latex_project,
    inspect_markdown_quality,
)


def test_converts_frontmatter_inputs_figures_lists_and_math(tmp_path: Path):
    paper = tmp_path / "paper"
    (paper / "sections").mkdir(parents=True)
    (paper / "main.tex").write_text(
        r"""
\documentclass{article}
\newcommand{\R}{\mathbb{R}}
\newcommand{\X}{\mathcal{X}}
\begin{document}
\begin{frontmatter}
\title{\textbf{Demo Article}}
\author{A. Researcher}
\begin{abstract}
This is a \emph{short} abstract with $x^2$.
\end{abstract}
\begin{keyword}
Decision support \sep Robust selection
\end{keyword}
\end{frontmatter}
\input{sections/intro}
\bibliography{refs}
\end{document}
""",
        encoding="utf-8",
    )
    (paper / "sections" / "intro.tex").write_text(
        r"""
\section{Introduction}
\label{sec:intro}
Figure~\ref{fig:front} cites prior work \citep{doe2024}. See \S\ref{sec:intro}. Let $\X\subseteq\R^n$.

\begin{figure}
\centering
\includegraphics[width=0.4\textwidth]{fig_intro.png}
\caption{From a Pareto front to a regret certificate.}
\label{fig:front}
\end{figure}

\begin{equation}
z=x^2+\alpha
\label{eq:toy}
\end{equation}

\begin{itemize}
\item first point
\item second point with \textbf{bold}
\end{itemize}
""",
        encoding="utf-8",
    )

    markdown = convert_latex_project(paper / "main.tex")

    assert "\\documentclass" not in markdown
    assert markdown.startswith("# Demo Article")
    assert "## Abstract\n\nThis is a *short* abstract with x²." in markdown
    assert "**Keywords:** Decision support, Robust selection" in markdown
    assert "## Introduction" in markdown
    assert "Figure (fig:front) cites prior work (doe2024)." in markdown
    assert "See Section (sec:intro)." in markdown
    assert "$\\mathcal{X}\\subseteq\\mathbb{R}^n$" in markdown
    assert (
        "![Figure showing from a Pareto front to a regret certificate.](fig_intro.png)"
        in markdown
    )
    assert "$$\nz=x^2+\\alpha\n$$" in markdown
    assert "* first point" in markdown
    assert "* second point with **bold**" in markdown


def test_converts_theorem_proof_and_simple_booktabs_table(tmp_path: Path):
    paper = tmp_path / "paper"
    paper.mkdir()
    main = paper / "main.tex"
    main.write_text(
        r"""
\begin{document}
\section{Core}
Let $\hat\reg_q(x)$ be an estimator.
\begin{theorem}[Existence]
\label{thm:exist}
A finite set has a minimum.
\end{theorem}
\begin{proof}
Sort the candidates and choose the first.
\end{proof}

\begin{table}[t]
\centering\small
\caption{Toy benchmark.}
\label{tab:toy}
\newcommand{\reg}{D}
\begin{tabular}{p{1.5cm}cc}
\toprule
Method & mean loss & tail loss\\
\midrule
A & \textbf{0.10} & 0.20\\
B & 0.30 & 0.40\\
\bottomrule
\end{tabular}
\end{table}
\end{document}
""",
        encoding="utf-8",
    )

    markdown = LatexProjectConverter(main).convert()

    assert "## Core" in markdown
    assert "$\\hat{D}_q(x)$" in markdown
    assert "**Theorem (Existence).**" in markdown
    assert "A finite set has a minimum." in markdown
    assert "**Proof.**" in markdown
    assert "*Table: Toy benchmark. (tab:toy)*" in markdown
    assert "p{1.5cm}" not in markdown
    assert "| Method | mean loss | tail loss |" in markdown
    assert "| --- | --- | --- |" in markdown
    assert "| A | **0.10** | 0.20 |" in markdown


def test_converts_tikz_figure_input_to_markdown_image(tmp_path: Path):
    paper = tmp_path / "paper"
    (paper / "tikz").mkdir(parents=True)
    (paper / "main.tex").write_text(
        r"""
\begin{document}
\input{tikz/pipeline}
\end{document}
""",
        encoding="utf-8",
    )
    (paper / "tikz" / "pipeline.tex").write_text(
        r"""
\begin{figure}[t]
\centering
\begin{tikzpicture}
\node {Candidate set};
\end{tikzpicture}
\caption{The LexPR pipeline from candidate set to certificate.}
\label{fig:pipeline}
\end{figure}
""",
        encoding="utf-8",
    )

    markdown = convert_latex_project(paper / "main.tex")

    assert (
        "![Figure showing the LexPR pipeline from candidate set to certificate.](tikz/pipeline.tex)"
        in markdown
    )


def test_copy_image_mode_resolves_graphicspath_and_copies_assets(tmp_path: Path):
    paper = tmp_path / "article"
    figures = paper / "figures"
    out_dir = tmp_path / "converted"
    figures.mkdir(parents=True)
    (figures / "plot.png").write_bytes(b"fake-png")
    (paper / "main.tex").write_text(
        r"""
\graphicspath{{figures/}}
\begin{document}
\section{Results}
\begin{figure}
\includegraphics[width=0.7\textwidth]{plot.png}
\caption{Mean and tail loss comparison for benchmark methods.}
\label{fig:loss}
\end{figure}
\end{document}
""",
        encoding="utf-8",
    )

    markdown = convert_latex_project(
        paper / "main.tex",
        out_dir / "main.md",
        ConversionOptions(image_mode="copy", image_dir="media"),
    )

    assert (
        "![Figure showing mean and tail loss comparison for benchmark methods.](media/plot.png)"
        in markdown
    )
    assert (out_dir / "media" / "plot.png").read_bytes() == b"fake-png"


def test_quality_report_verifies_tables_images_and_missing_assets(tmp_path: Path):
    markdown_path = tmp_path / "main.md"
    (tmp_path / "media").mkdir()
    (tmp_path / "media" / "plot.png").write_bytes(b"fake-png")
    markdown = """
# Demo

![Figure showing a clear benchmark plot.](media/plot.png)

| Method | Loss |
| --- | --- |
| LexPR | 0.1 |
"""
    markdown_path.write_text(markdown, encoding="utf-8")

    report = inspect_markdown_quality(markdown, markdown_path)

    assert report.image_count == 1
    assert report.table_count == 1
    assert report.missing_images == []
    assert report.warnings == []
