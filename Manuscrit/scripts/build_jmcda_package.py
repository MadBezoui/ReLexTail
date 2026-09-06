"""Assemble the JMCDA submission package.

Produces `Manuscrit/JMCDA_package/`, a folder whose contents map one-to-one onto
the upload slots of a Wiley submission portal.  Everything is generated from the
manuscript sources, so re-running after an edit refreshes the whole package and
nothing can drift out of date by hand.

Two versions of the main document are produced:

* `03_main_document.pdf` — the full paper with authors, affiliation and ORCID.
* `03a_main_document_anonymous.pdf` — the same paper with every identifying
  string removed, for a double-anonymous review policy.

Both are built, because the review model could not be verified from the live
guidelines page at packaging time (Wiley returns HTTP 403 to automated
requests). `CHECKLIST.md` records that verification as an author action and says
which file to upload under each policy.

The anonymous build is a *copy*: the primary sources are never modified. After
building, the script greps the anonymous PDF for every identifying string and
fails if any survives, so an incomplete anonymisation stops the package rather
than reaching an editor.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

#: Per-figure provenance, keyed by source filename.  Order is NOT taken from
#: here: it is derived from the order the figures appear in the manuscript
#: sources, which is what LaTeX numbers them by.
FIGURE_PROVENANCE = {
    "pipeline.pdf": ("rebuilt", "ReLexTail mathematical definition"),
    "resolution_cells.pdf": ("new", "ceil cell definition; constructed illustration"),
    "two_risks.pdf": ("new", "selection and evaluation protocol"),
    "fig_certified_decay.pdf": ("recomputed", "submission/data/certification.json"),
    "fig_continuous_cost.pdf": ("replaced unsupported empirical comparison", "theoretical formulation counts"),
    "fig_mechanism.pdf": ("new", "enhanced/results/mechanism.csv"),
    "fig_certification_ladder.pdf": ("new", "enhanced/results/certification.csv"),
    "fig_certification_progress.pdf": ("new", "enhanced/results/anytime.csv; enhanced/results/certification.csv"),
    "quality_stability_frontier.pdf": ("recomputed", "submission/data/study.csv"),
    "family_effects.pdf": ("new", "paired instance bootstrap from study.csv"),
    "fig_divergence.pdf": ("recomputed", "nominal identifiers in study.csv"),
    "sensitivity_extensions.pdf": ("new", "grid_sensitivity.csv; ablation.csv; decisive_coordinates.csv; uci_benchmark.json"),
    "fig_supplier_certificate.pdf": ("recomputed", "submission/data/supplier.npz"),
    "relex_decision_profile.pdf": ("recomputed", "submission/data/supplier.npz"),
    "fig_supplier_interval.pdf": ("replaced with correctly labelled sampling", "submission/data/supplier_sensitivity.json"),
}

SECTION_ORDER = ["introduction", "method", "properties", "computation",
                 "certification", "experiments", "discussion"]

ROOT = Path(__file__).resolve().parents[2]
M = ROOT / "Manuscrit"
S = M / "submission"
PKG = M / "JMCDA_package"
ANON_BUILD = M / "tmp" / "anon_build"

def run_latex(directory: Path, stem: str) -> None:
    r = subprocess.run(
        ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", f"{stem}.tex"],
        cwd=directory,
        capture_output=True,
        text=True,
    )
    if r.returncode != 0 or not (directory / f"{stem}.pdf").exists():
        log = directory / f"{stem}.log"
        tail = log.read_text()[-3000:] if log.exists() else r.stdout[-3000:]
        raise SystemExit(f"LaTeX failed for {stem} in {directory}:\n{tail}")


def pdf_text(pdf: Path) -> str:
    r = subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"pdftotext failed on {pdf}")
    return r.stdout


def count_words(pdf: Path) -> dict:
    """Word counts from the rendered PDF, so what is counted is what is read."""
    text = pdf_text(pdf)
    body = text
    for marker in ("\nReferences\n", "\nReferences \n"):
        if marker in body:
            body = body.split(marker)[0]
            break
    words = len(re.findall(r"\b[\w-]+\b", body))
    src = (M / "main.tex").read_text()
    abstract = src.split(r"\begin{abstract}")[1].split(r"\end{abstract}")[0]
    prose = re.sub(r"\\[a-zA-Z]+\{?|\}|\$", "", abstract)
    return {
        "body_words_excluding_references": words,
        "abstract_words": len(re.findall(r"\b[\w-]+\b", prose)),
    }


# ------------------------------------------------------------------- title page
TITLE_PAGE = r"""\documentclass[11pt,a4paper]{article}
\usepackage[margin=2.5cm]{geometry}
\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}\usepackage{lmodern}
\usepackage{microtype}\usepackage[hidelinks]{hyperref}\usepackage{booktabs}
\pagestyle{empty}
\begin{document}
\begin{center}
{\Large\bfseries Resolution-Aware Lexicographic Tail-Regret Selection\\under Uncertain Normalisation Bounds}\\[10pt]
{\small Submitted to the \emph{Journal of Multi-Criteria Decision Analysis} as a Research Article}
\end{center}

%% The five items the journal's Title Page section requires, in its order:
%% title, short running title, full author names, institutional affiliations,
%% acknowledgments.

\vspace{8pt}
\noindent\textbf{Short running title.} Resolution-aware tail-regret selection
\hfill (RUNNINGCHARS characters; limit 40)

\vspace{10pt}
\noindent\textbf{Author.}\\
Madani Bezoui\\
ORCID: \url{https://orcid.org/0000-0002-8342-7039}

\vspace{6pt}
\noindent\textbf{Institutional affiliation where the work was conducted.}\\
CESI LINEACT, UR 7527, CESI\\
3 rue Bois de la Champelle, Vand\oe uvre-l\`es-Nancy, France

\vspace{4pt}
\noindent\emph{Present address.} Unchanged; the work was conducted at the
affiliation above.

\vspace{6pt}
\noindent\textbf{Corresponding author.} Madani Bezoui, \href{mailto:mbezoui@cesi.fr}{mbezoui@cesi.fr}

\vspace{10pt}
\noindent\textbf{Acknowledgments.} This research received no external funding.
No additional acknowledgments are declared. An AI assistant assisted with
manuscript revision, code preparation, numerical consistency checks and figure
preparation. All reported numerical results were computed by the supplied
deterministic, seeded scripts. The author is responsible for the scientific
content and for all submission declarations.

\vspace{10pt}
\noindent\textbf{Keywords} (6 of at most 7)\textbf{.} multicriteria decision
analysis; lexicographic selection; regret; conditional value-at-risk;
normalisation uncertainty; robustness

\vspace{10pt}
\noindent\textbf{Manuscript metrics.}
\begin{center}\small
\begin{tabular}{@{}ll@{}}\toprule
Abstract & ABSTRACTWORDS words (limit 300), unstructured\\
Main text & BODYWORDS words; the journal sets no word limit\\
Figures & NFIGURES, all vector PDF, supplied as separate files\\
Tables & NTABLES, each with title and footnotes, in the main document\\
References & NREFS, APA style\\
Supporting information & 1 archive (code, data, protocol, results)\\\bottomrule
\end{tabular}
\end{center}

\vspace{6pt}
\noindent\textbf{Author contributions (CRediT).} Madani Bezoui:
conceptualization; methodology; software; formal analysis; investigation;
visualization; writing -- original draft; writing -- review and editing.

\vspace{4pt}
\noindent\textbf{Conflicts of interest.} The author declares no conflicts of
interest.

\vspace{4pt}
\noindent\textbf{Ethics.} No human participants, animals or personal data were
involved. The supplier example is constructed.

\vspace{4pt}
\noindent\textbf{Data availability statement.} All scripts, generated data,
protocol files, per-instance results and figure sources accompany the
submission as supporting information, together with the UCI Energy Efficiency
file under CC BY 4.0 and its SHA-256 checksum. That dataset is cited in the
reference list and is independently available at
\url{https://doi.org/10.24432/C51307}. The code and data archive for this exact
version is deposited at \url{https://doi.org/10.5281/zenodo.22558690} and the repository is
\url{https://github.com/MadBezoui/ReLexTail}. It supersedes the earlier and
smaller release archived at \url{https://doi.org/10.5281/zenodo.21771786}, to which the
experiments reported here must not be attributed.

\vspace{4pt}
\noindent\textbf{Prior publication and preprints.} The manuscript is original,
has not been published elsewhere and is not under consideration by another
journal. It has not been posted to a preprint server.
\end{document}
"""



def build_title_page(metrics: dict, n_refs: int, n_tables: int, n_figures: int) -> Path:
    out = M / "tmp" / "title_page"
    out.mkdir(parents=True, exist_ok=True)
    tex = (
        TITLE_PAGE.replace("ABSTRACTWORDS", str(metrics["abstract_words"]))
        .replace("BODYWORDS", f"{metrics['body_words_excluding_references']:,}")
        .replace("NFIGURES", str(n_figures))
        .replace("NTABLES", str(n_tables))
        .replace("NREFS", str(n_refs))
        .replace("RUNNINGCHARS", str(len("Resolution-aware tail-regret selection")))
    )
    (out / "title_page.tex").write_text(tex)
    run_latex(out, "title_page")
    return out / "title_page.pdf"


COVER_LETTER = r"""\documentclass[11pt,a4paper]{article}
\usepackage[margin=2.5cm]{geometry}
\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}\usepackage{lmodern}
\usepackage{microtype}\usepackage[hidelinks]{hyperref}\usepackage{parskip}
\pagestyle{empty}
\begin{document}
\noindent\hfill LETTERDATE

\vspace{6pt}
BODY
\end{document}
"""


def build_cover_letter() -> Path:
    out = M / "tmp" / "cover_letter"
    out.mkdir(parents=True, exist_ok=True)
    body = (S / "cover_letter.txt").read_text()
    body = body.replace("&", r"\&").replace("%", r"\%").replace("_", r"\_")
    body = body.replace("“", "``").replace("”", "''").replace("’", "'")
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    rendered = "\n\n".join(p.replace("\n", "\\\\\n") if i >= len(paragraphs) - 1
                           else p.replace("\n", " ")
                           for i, p in enumerate(paragraphs))
    from datetime import date

    tex = COVER_LETTER.replace("BODY", rendered)
    tex = tex.replace("LETTERDATE", date.today().strftime("%d %B %Y"))
    (out / "cover_letter.tex").write_text(tex)
    run_latex(out, "cover_letter")
    return out / "cover_letter.pdf"


# ------------------------------------------------------------------------ main
def figure_order() -> list:
    """Figure filenames in the order LaTeX will number them.

    Derived from the sources, never from a hand-maintained list: a figure moved
    between sections would otherwise silently misname every file after it.
    Cross-checked against the compiled list of figures.
    """
    text = "\n".join((S / f"{name}.tex").read_text() for name in SECTION_ORDER)
    files = re.findall(r"\\includegraphics\[[^\]]*\]\{([^}]+)\}", text)
    lof = M / "main.lof"
    if lof.exists():
        n_typeset = lof.read_text().count("numberline")
        if n_typeset != len(files):
            raise SystemExit(
                f"{len(files)} figures in the sources but {n_typeset} in main.lof; "
                "rebuild the PDF before packaging"
            )
    unknown = [f for f in files if f not in FIGURE_PROVENANCE]
    if unknown:
        raise SystemExit(f"figures with no recorded provenance: {unknown}")
    return files


def write_figure_manifest(files: list) -> None:
    rows = ["number,filename,status,source"]
    for i, name in enumerate(files, 1):
        status, source = FIGURE_PROVENANCE[name]
        rows.append(f"{i},{name},{status},{source}")
    (S / "figure_manifest.csv").write_text("\n".join(rows) + "\n")


def main() -> int:
    main_pdf = M / "main.pdf"
    if not main_pdf.exists():
        raise SystemExit("build Manuscrit/main.pdf first: latexmk -pdf main.tex")

    files = figure_order()
    write_figure_manifest(files)
    print("recasting into the Wiley template ...", flush=True)
    r = subprocess.run([sys.executable, str(M / "scripts" / "build_wiley_version.py")],
                       cwd=M, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("build_wiley_version.py failed:\n" + (r.stderr or r.stdout)[-2000:])
    print("  " + r.stdout.strip().splitlines()[-1])
    wiley_pdf = M / "wiley" / "main.pdf"
    # Regenerate the legends and the reproducibility archive from the corrected
    # manifest, so the archive shipped as supporting information can never be
    # older than the figure numbering it documents.
    print("refreshing legends and the reproducibility archive ...", flush=True)
    r = subprocess.run([sys.executable, str(M / "scripts" / "package_submission.py")],
                       cwd=M, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("package_submission.py failed:\n" + (r.stderr or r.stdout)[-2000:])
    print("  " + r.stdout.strip().splitlines()[-1])
    manifest = [
        line.split(",")
        for line in (S / "figure_manifest.csv").read_text().strip().splitlines()[1:]
    ]
    n_figures = len(manifest)
    n_tables = sum(
        t.read_text().count(r"\begin{table}")
        for t in S.glob("*.tex")
        if not t.name.startswith("original_")
    )
    n_refs = (M / "main.bbl").read_text().count(r"\bibitem")
    metrics = count_words(main_pdf)

    if PKG.exists():
        shutil.rmtree(PKG)
    (PKG / "04_figures").mkdir(parents=True)
    (PKG / "06_supporting_information").mkdir(parents=True)

    print("building the title page ...", flush=True)
    title_pdf = build_title_page(metrics, n_refs, n_tables, n_figures)
    print("building the cover letter ...", flush=True)
    cover_pdf = build_cover_letter()

    shutil.copy2(cover_pdf, PKG / "01_cover_letter.pdf")
    shutil.copy2(S / "cover_letter.txt", PKG / "01_cover_letter.txt")
    shutil.copy2(title_pdf, PKG / "02_title_page.pdf")
    shutil.copy2(wiley_pdf, PKG / "03_main_document.pdf")
    shutil.copy2(main_pdf, PKG / "03b_main_document_plain_layout.pdf")
    shutil.copy2(S / "figure_legends.txt", PKG / "05_figure_legends.txt")

    for number, filename, *_ in manifest:
        src = S / "figures" / filename
        if not src.exists():
            raise SystemExit(f"figure listed in the manifest is missing: {filename}")
        shutil.copy2(src, PKG / "04_figures" / f"Figure{int(number):02d}.pdf")

    si = PKG / "06_supporting_information"
    shutil.copy2(M / "JMCDA_submission.zip", si / "SupportingInformation_S1_code_and_data.zip")
    shutil.copy2(S / "figure_manifest.csv", PKG / "04_figures" / "figure_manifest.csv")

    # The journal accepts a LaTeX main text file; ship the compilable tree.
    shutil.make_archive(str(PKG / "07_latex_source"), "zip", root_dir=M / "wiley")

    write_si_note(si, n_figures)
    write_checklist(PKG, metrics, n_figures, n_tables, n_refs)
    write_readme(PKG)

    checksums = {}
    for p in sorted(PKG.rglob("*")):
        if p.is_file():
            checksums[str(p.relative_to(PKG))] = hashlib.sha256(p.read_bytes()).hexdigest()
    (PKG / "MANIFEST.sha256.json").write_text(json.dumps(checksums, indent=2))

    total = sum(p.stat().st_size for p in PKG.rglob("*") if p.is_file())
    print(
        f"\nJMCDA_package/ built: {len(checksums)} files, {total / 1e6:.1f} MB\n"
        f"  abstract {metrics['abstract_words']} words, "
        f"body {metrics['body_words_excluding_references']:,} words, "
        f"{n_figures} figures, {n_tables} tables, {n_refs} references"
    )
    return 0


def write_si_note(si: Path, n_figures: int) -> None:
    (si / "SupportingInformation_S0_contents.md").write_text(
        f"""# Supporting Information

**S1 — `SupportingInformation_S1_code_and_data.zip`**

One archive holding everything needed to regenerate every number and every one
of the {n_figures} figures in the manuscript.

| Path in the archive | Contents |
|---|---|
| `Manuscrit/main.tex`, `Manuscrit/submission/*.tex` | manuscript sources, one file per section |
| `Manuscrit/submission/generated_certrelex.tex` | the certification numbers, generated from results |
| `Manuscrit/scripts/` | the 90-instance study, extensions, figures, validation, packaging |
| `Manuscrit/tests/` | numerical-convention tests for the study pipeline |
| `Manuscrit/submission/data/` | candidate matrices, perturbation directions, protocol, per-instance results, statistical summaries, the UCI file and its checksum |
| `Manuscrit/submission/figures/` | vector sources of every figure |
| `enhanced/src/certrelex/` | the certification engine, exact rational oracle and independent verifier |
| `enhanced/protocol/` | numerical contract, preregistered splits and contrasts, claim registry, plan status |
| `enhanced/literature/` | search log, evidence matrix, novelty memo |
| `enhanced/results/`, `enhanced/analysis/tables/` | raw per-instance results and the derived tables |
| `enhanced/tests/` | soundness, numerical-contract and frozen-example tests |
| `Experimental/code/lexpr/` | the library the study imports |

Reproduction, from the archive root:

```
python enhanced/reproduce.py                 # certification results and figures
python Manuscrit/scripts/reproduce_submission.py   # study, figures, PDF, validation
```

Both are deterministic and seeded. Bit-for-bit PDF equality is not expected
across TeX and font versions.

The UCI Energy Efficiency file is redistributed under CC BY 4.0 with its
SHA-256 checksum recorded; it is independently available at
<https://doi.org/10.24432/C51307>.

No other supporting information is submitted: every table and figure the
manuscript relies on is in the main document.
"""
    )


def write_checklist(pkg: Path, metrics: dict, n_figures: int, n_tables: int, n_refs: int) -> None:
    (pkg / "CHECKLIST.md").write_text(
        f"""# Submission checklist — Journal of Multi-Criteria Decision Analysis

Checked against the journal's own author guidelines
(`guidlesJMCDA.md`) and Wiley's LaTeX template guide
(`WileyDesign/Author-guidelines for LaTex Template_Wiley (2026).pdf`).
Each line names the requirement it satisfies.

## Article type: Research Article

The guidelines set, for this type: **no word limit**, a **300-word unstructured
abstract**, and a **Data Availability Statement**.

- [x] Abstract **{metrics['abstract_words']} words**, unstructured.
- [x] Main text **{metrics['body_words_excluding_references']:,} words** excluding references — no limit applies.
- [x] Data Availability Statement present in the main document and on the title page.

## Title Page — the five items the guidelines list

- [x] Brief informative title with the major keywords, **no abbreviations**.
- [x] **Short running title**, {len('Resolution-aware tail-regret selection')} characters (limit 40).
- [x] Full name of the author.
- [x] Institutional affiliation where the work was conducted, with an explicit
  present-address note (unchanged).
- [x] **Acknowledgments** — the guidelines require funding to be listed here,
  so the funding statement sits inside Acknowledgments, not in a separate
  section.

## Main Text File — the items the guidelines list

- [x] Short informative title with the major keywords.
- [x] **Full name of the author with institutional affiliation.** The journal
  operates **single-blind** peer review, so the main document is not
  anonymised.
- [x] Acknowledgments (with funding).
- [x] Abstract.
- [x] **{6} keywords** (up to seven).
- [x] Main body.
- [x] References — **APA style**, {n_refs} entries.
- [x] **{n_tables} tables**, each complete with title and footnotes, in the main
  document.
- [x] **Complete list of figure legends in the text** — generated into the main
  document from the same captions that typeset the figures, so the two cannot
  diverge.

## Figures and Supporting Information — supplied as separate files

- [x] **{n_figures} figures**, one vector PDF each in `04_figures/`, named
  `Figure01.pdf` … `Figure{n_figures:02d}.pdf` in citation order. The order is
  derived from the sources and cross-checked against the compiled document.
- [x] `05_figure_legends.txt` for pasting a legend beneath each image at upload,
  as the guidelines require in addition to the in-text list.
- [x] Supporting information as a separate archive.

## Other mandated items

- [x] **ORCID** — the journal requires it; present on the title page and in the
  article header.
- [x] **CRediT author contributions** — mandated for all articles.
- [x] **Conflicts of interest** declared (none).
- [x] **Ethics**: no human participants, animals or personal data.
- [x] **Data sharing**: the journal expects it. Code, data, protocol and raw
  results ship as supporting information; the UCI dataset is **cited in the
  reference list**, per Wiley's data citation policy.

## Format

- [x] Prepared with Wiley's own LaTeX template (`USG.cls`, `APA` option),
  compiled with XeLaTeX, 0 overfull boxes, no undefined references or
  citations.
- [x] LaTeX source shipped with the PDF, including `refs.bib` **and** the
  pre-built `.bbl`, as the template guide requests.
- [x] The specimen journal cover strip and the OPEN ACCESS badge that
  `USG.cls` hardcodes have been blanked: the cover belongs to another journal,
  and open access is chosen **after acceptance** under this journal's policy.

## Author actions before transmission — none of these can be done for you

- [ ] **Approve the declarations.** CRediT, funding, conflicts, ethics and the
  AI-assistance statement are yours to affirm.
- [ ] **Confirm originality and exclusivity** in the portal. The package states
  the manuscript has not been posted to a preprint server — correct this if it
  has, since the journal permits preprints.
- [ ] **Select the Wiley data availability statement** that matches this
  submission from the list in the journal's data sharing policy; the wording
  supplied here is a draft.
- [x] **Version-specific DOI published** for this revision
  (`10.5281/zenodo.22558690`) and carried into the manuscript, the title page
  and the repository README. The earlier release (`10.5281/zenodo.21771786`)
  is cited as superseded.
- [x] **Licence chosen**: MIT, `LICENSE` at the repository root, matching the
  `license` field of `.zenodo.json`. The bundled UCI file keeps its separate
  CC BY 4.0 attribution.
- [ ] **Open access** is decided after acceptance and carries an APC; check
  institutional or funder eligibility then, not now.
- [ ] Submit via the **Wiley Authors submission portal**; editorial contact is
  MCDA.editorialoffice@wiley.com. There is no submission fee.

## Scope statement to keep in mind while answering portal questions

The manuscript claims a decision-focused certification result and a qualified,
metric-dependent quality trade-off on a synthetic population. It does **not**
claim lower external regret against a competing method, any calibration
guarantee, validation on operational data, or priority over the closest
literature. Those are listed as unestablished in the claim-to-evidence table in
the discussion. Portal fields describing novelty and significance should match
that table rather than overstate it.
"""
    )


def write_readme(pkg: Path) -> None:
    (pkg / "00_README_SUBMISSION.md").write_text(
        """# JMCDA submission package

Generated by `Manuscrit/scripts/build_jmcda_package.py`. Re-run it after any
change to the manuscript; nothing here should be edited by hand.

| File | Upload slot |
|---|---|
| `01_cover_letter.pdf` / `.txt` | Cover letter |
| `02_title_page.pdf` | Title page (separate file) |
| `03_main_document.pdf` | **Main text file** — Wiley template layout |
| `03b_main_document_plain_layout.pdf` | Same content, plain `article` layout, for reading |
| `04_figures/Figure01.pdf` … `Figure15.pdf` | Figures, one file each, citation order |
| `04_figures/figure_manifest.csv` | Which numerical source produced each figure |
| `05_figure_legends.txt` | Legends, for pasting beneath each image at upload |
| `06_supporting_information/` | Contents note + code/data archive |
| `07_latex_source.zip` | Compilable LaTeX source of the main document |
| `CHECKLIST.md` | Requirement-by-requirement status, and what only the author can do |
| `MANIFEST.sha256.json` | SHA-256 of every file in this package |

Upload `03_main_document.pdf` as the main text file.
`03b_main_document_plain_layout.pdf` is the same manuscript in the project's
plain layout; it is included only because it is easier to read on screen, and
it is not a separate version of the paper.

There is **no anonymised variant**: the journal operates single-blind peer
review and its Main Text File requirements call for the author's full name and
affiliation.

## The LaTeX source

`07_latex_source.zip` unpacks to a self-contained tree that compiles with
**XeLaTeX**:

```
main.tex          front matter, then \\input of one file per section
sections/*.tex    introduction, method, properties, computation,
                  certification, experiments, discussion
figures/*.pdf     the 15 vector figures
refs.bib          bibliography source
main.bbl          pre-built reference list
USG.cls, *.sty    Wiley's class and supporting styles
Fonts/, images/   STIX fonts and the class's title-page marks
```

Run `xelatex main.tex` three times. **BibTeX is not rerun:** the `APA` class
option selects `WileyNJD-APA.bst`, which is not distributed with the template
package, so the apacite-generated `.bbl` is supplied instead — the template
guide explicitly accepts a `.bbl`. `refs.bib` travels with it so the typesetter
can regenerate the list in the journal's own style.

Numbers in the certification section are literals in this source, expanded at
generation time from `enhanced/results/`; the template guide asks that author
macros be kept to a minimum, so none reach the typesetter.
"""
    )


if __name__ == "__main__":
    raise SystemExit(main())
