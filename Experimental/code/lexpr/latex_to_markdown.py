from __future__ import annotations

import argparse
import base64
import hashlib
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


THEOREM_NAMES = {
    "theorem": "Theorem",
    "lemma": "Lemma",
    "definition": "Definition",
    "proposition": "Proposition",
    "corollary": "Corollary",
    "remark": "Remark",
}

STYLE_COMMANDS = {
    "emph": ("*", "*"),
    "textit": ("*", "*"),
    "textbf": ("**", "**"),
}

GREEK_UNICODE = {
    r"\alpha": "α",
    r"\beta": "β",
    r"\gamma": "γ",
    r"\delta": "δ",
    r"\epsilon": "ε",
    r"\eta": "η",
    r"\theta": "θ",
    r"\lambda": "λ",
    r"\mu": "μ",
    r"\rho": "ρ",
    r"\sigma": "σ",
    r"\tau": "τ",
    r"\omega": "ω",
}


@dataclass(frozen=True)
class ConversionOptions:
    """Reusable conversion settings for scripts, packages, and CLIs."""

    project_root: Path | None = None
    image_mode: str = "reference"
    image_dir: str = "assets/images"
    render_tikz: bool = False


@dataclass(frozen=True)
class MarkdownQualityReport:
    image_count: int
    table_count: int
    missing_images: list[str]
    warnings: list[str]


def convert_latex_project(
    main_tex: str | Path,
    output_path: str | Path | None = None,
    options: ConversionOptions | None = None,
) -> str:
    """Convert a LaTeX project rooted at ``main_tex`` to AI-readable Markdown."""
    markdown = LatexProjectConverter(
        Path(main_tex),
        options=options or ConversionOptions(),
        output_path=Path(output_path) if output_path is not None else None,
    ).convert()
    if output_path is not None:
        Path(output_path).write_text(markdown, encoding="utf-8")
    return markdown


def inspect_markdown_quality(
    markdown: str,
    markdown_path: str | Path | None = None,
) -> MarkdownQualityReport:
    """Check that Markdown image tags and pipe tables are usable."""
    base_dir = (
        Path(markdown_path).resolve().parent if markdown_path is not None else None
    )
    images = re.findall(r"!\[([^\]]*)\]\(([^)]+)\)", markdown)
    missing_images: list[str] = []
    warnings: list[str] = []

    for alt, target in images:
        clean_target = target.strip()
        if len(alt.strip()) < 12:
            warnings.append(f"Image alt text is too short for {clean_target}")
        suffix = Path(clean_target.split("#", 1)[0].split("?", 1)[0]).suffix.lower()
        if not (
            clean_target.startswith(("http://", "https://", "data:"))
            or suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".pdf"}
        ):
            warnings.append(f"Image target may not render as an image: {clean_target}")
        if base_dir and not clean_target.startswith(("http://", "https://", "data:")):
            target_path = (base_dir / clean_target).resolve()
            if not target_path.exists():
                missing_images.append(clean_target)

    lines = markdown.splitlines()
    table_count = 0
    for index in range(len(lines) - 1):
        if "|" not in lines[index]:
            continue
        if re.match(
            r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$", lines[index + 1]
        ):
            table_count += 1

    return MarkdownQualityReport(
        image_count=len(images),
        table_count=table_count,
        missing_images=missing_images,
        warnings=warnings,
    )


@dataclass
class LatexProjectConverter:
    main_tex: Path
    options: ConversionOptions = field(default_factory=ConversionOptions)
    output_path: Path | None = None
    macros: dict[str, str] = field(default_factory=dict)
    figure_sources: dict[str, str] = field(default_factory=dict)
    figure_source_files: dict[str, Path] = field(default_factory=dict)
    graphic_paths: list[Path] = field(default_factory=list)
    copied_images: dict[Path, Path] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.main_tex = Path(self.main_tex).resolve()
        self.main_dir = self.main_tex.parent
        self.latex_preamble = ""
        self.root = (
            Path(self.options.project_root).resolve()
            if self.options.project_root is not None
            else self.main_dir
        )
        if self.output_path is not None:
            self.output_path = Path(self.output_path).resolve()
        if self.options.image_mode not in {"reference", "copy", "embed"}:
            raise ValueError("image_mode must be one of: reference, copy, embed")

    def convert(self) -> str:
        raw = self._read_file(self.main_tex)
        self.latex_preamble = self._preamble(raw)
        raw = self._resolve_if_file_exists(raw, self.root)
        self._collect_graphic_paths(raw, self.main_dir)

        macro_source = self._expand_inputs(raw, self.root)
        self._collect_newcommands(macro_source)

        body = self._document_body(raw)
        body = self._expand_inputs(body, self.root)
        self._collect_newcommands(body)

        body = self._remove_comments(body)
        body = self._expand_macros(body)
        body = self._remove_newcommands(body)
        body = self._convert_frontmatter(body)
        body = self._convert_block_environments(body)
        body = self._convert_inline_markup(body)
        body = self._cleanup_markdown(body)
        return body

    def _read_file(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def _document_body(self, text: str) -> str:
        match = re.search(
            r"\\begin\{document\}(.*?)(?:\\end\{document\}|$)", text, re.S
        )
        return match.group(1) if match else text

    def _preamble(self, text: str) -> str:
        return text.split(r"\begin{document}", 1)[0]

    def _resolve_if_file_exists(self, text: str, current_dir: Path) -> str:
        position = 0
        while True:
            found = self._find_command_args(text, "IfFileExists", position, count=3)
            if found is None:
                return text
            start, end, args = found
            file_name, present_branch, absent_branch = args
            branch = (
                present_branch
                if self._resolve_input_path(file_name, current_dir)
                else absent_branch
            )
            text = text[:start] + branch + text[end:]
            position = start + len(branch)

    def _expand_inputs(
        self, text: str, current_dir: Path, active: set[Path] | None = None
    ) -> str:
        active = set() if active is None else active

        def replace(match: re.Match[str]) -> str:
            input_name = match.group(1).strip()
            input_path = self._resolve_input_path(input_name, current_dir)
            if input_path is None:
                return f"\n<!-- Missing LaTeX input: {input_name} -->\n"
            input_path = input_path.resolve()
            if input_path in active:
                rel = self._relative_path(input_path)
                return f"\n<!-- Skipped recursive LaTeX input: {rel} -->\n"
            content = self._read_file(input_path)
            content = self._resolve_if_file_exists(content, input_path.parent)
            self._collect_graphic_paths(content, input_path.parent)
            self._register_figure_sources(content, input_path)
            return self._expand_inputs(
                content, input_path.parent, active | {input_path}
            )

        return re.sub(r"\\(?:input|include)\{([^}]+)\}", replace, text)

    def _resolve_input_path(self, name: str, current_dir: Path) -> Path | None:
        clean_name = name.strip()
        candidates: list[Path] = []
        raw = Path(clean_name)
        if raw.is_absolute():
            candidates.append(raw)
        else:
            candidates.extend([current_dir / raw, self.main_dir / raw, self.root / raw])
        expanded: list[Path] = []
        for candidate in candidates:
            expanded.append(candidate)
            if candidate.suffix == "":
                expanded.append(candidate.with_suffix(".tex"))
        for candidate in expanded:
            if candidate.exists():
                return candidate
        return None

    def _register_figure_sources(self, text: str, source_path: Path) -> None:
        rel = self._relative_path(source_path)
        for figure in re.finditer(
            r"\\begin\{figure\}(?:\[[^\]]*\])?(.*?)\\end\{figure\}", text, re.S
        ):
            figure_body = figure.group(1)
            for _, _, label in self._iter_command_args(figure_body, "label"):
                self.figure_sources[label.strip()] = rel
                self.figure_source_files[label.strip()] = source_path

    def _collect_graphic_paths(self, text: str, current_dir: Path) -> None:
        for match in re.finditer(r"\\graphicspath\{((?:\{[^{}]+\})+)\}", text):
            for item in re.findall(r"\{([^{}]+)\}", match.group(1)):
                raw = Path(item.strip())
                candidates = (
                    [raw]
                    if raw.is_absolute()
                    else [
                        current_dir / raw,
                        self.main_dir / raw,
                        self.root / raw,
                    ]
                )
                for candidate in candidates:
                    resolved = candidate.resolve()
                    if resolved not in self.graphic_paths:
                        self.graphic_paths.append(resolved)

    def _relative_path(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return path.name

    def _collect_newcommands(self, text: str) -> None:
        pattern = re.compile(
            r"\\(?:re)?newcommand\{\\([A-Za-z][A-Za-z0-9]*)\}"
            r"(?:\[[^\]]+\])?"
            r"\{((?:[^{}]|\{[^{}]*\})*)\}",
            re.S,
        )
        for name, value in pattern.findall(text):
            self.macros[name] = value.strip()

    def _remove_newcommands(self, text: str) -> str:
        return re.sub(
            r"\\(?:re)?newcommand\{\\[A-Za-z][A-Za-z0-9]*\}(?:\[[^\]]+\])?\{(?:[^{}]|\{[^{}]*\})*\}",
            "",
            text,
            flags=re.S,
        )

    def _expand_macros(self, text: str) -> str:
        for name, value in sorted(self.macros.items(), key=lambda item: -len(item[0])):
            literal_value = lambda _match, value=value: value
            text = re.sub(rf"\\{re.escape(name)}\s*\{{\}}", literal_value, text)
            text = re.sub(rf"\\{re.escape(name)}(?![A-Za-z])", literal_value, text)
        return text

    def _remove_comments(self, text: str) -> str:
        cleaned_lines = []
        for line in text.splitlines():
            cleaned_lines.append(self._strip_comment_from_line(line))
        return "\n".join(cleaned_lines)

    def _strip_comment_from_line(self, line: str) -> str:
        escaped = False
        for index, char in enumerate(line):
            if char == "\\" and not escaped:
                escaped = True
                continue
            if char == "%" and not escaped:
                return line[:index].rstrip()
            escaped = False
        return line

    def _convert_frontmatter(self, text: str) -> str:
        def replace(match: re.Match[str]) -> str:
            frontmatter = match.group(1)
            blocks: list[str] = []
            title = self._first_command_arg(frontmatter, "title")
            if title:
                blocks.append(f"# {self._plain_text(title)}")
            for _, _, author in self._iter_command_args(frontmatter, "author"):
                blocks.append(f"**Author:** {self._plain_text(author)}")
            address = self._first_command_arg(frontmatter, "address")
            if address:
                blocks.append(f"**Affiliation:** {self._plain_text(address)}")
            abstract = self._first_environment(frontmatter, "abstract")
            if abstract:
                blocks.append(
                    f"## Abstract\n\n{self._format_inline_text(abstract.strip())}"
                )
            keywords = self._first_environment(frontmatter, "keyword")
            if keywords:
                keyword_text = self._plain_text(keywords).replace(" sep ", ", ")
                keyword_text = re.sub(r"\s*,\s*", ", ", keyword_text)
                blocks.append(f"**Keywords:** {keyword_text}")
            return "\n\n".join(block for block in blocks if block.strip())

        return re.sub(
            r"\\begin\{frontmatter\}(.*?)\\end\{frontmatter\}",
            replace,
            text,
            flags=re.S,
        )

    def _convert_block_environments(self, text: str) -> str:
        text = self._convert_figures(text)
        text = self._convert_tables(text)
        text = self._convert_math_environments(text)
        text = self._convert_theorem_environments(text)
        text = self._convert_lists(text, "itemize", ordered=False)
        text = self._convert_lists(text, "enumerate", ordered=True)
        text = self._convert_headings(text)
        text = re.sub(r"\\bibliographystyle\{[^}]+\}", "", text)
        text = re.sub(r"\\bibliography\{([^}]+)\}", r"\n\n**References:** \1\n", text)
        return text

    def _convert_figures(self, text: str) -> str:
        def replace(match: re.Match[str]) -> str:
            figure_body = match.group(1)
            images = [
                image.strip()
                for _, _, image in self._iter_command_args(
                    figure_body, "includegraphics"
                )
            ]
            captions = [
                caption.strip()
                for _, _, caption in self._iter_command_args(figure_body, "caption")
            ]
            labels = [
                label.strip()
                for _, _, label in self._iter_command_args(figure_body, "label")
            ]
            if images:
                image_blocks = []
                for index, image in enumerate(images):
                    caption = (
                        captions[index]
                        if index < len(captions)
                        else (captions[0] if captions else image)
                    )
                    label = labels[0] if labels else ""
                    source_file = self.figure_source_files.get(label)
                    image_blocks.append(
                        self._markdown_image(caption, image, source_file)
                    )
                return "\n\n" + "\n\n".join(image_blocks) + "\n\n"

            caption = captions[0] if captions else "LaTeX figure"
            label = labels[0] if labels else ""
            rendered_tikz = self._render_tikz_target(figure_body, caption, label)
            if rendered_tikz is not None:
                return "\n\n" + rendered_tikz + "\n\n"
            source = self.figure_sources.get(label, self._source_from_label(label))
            return "\n\n" + self._markdown_image(caption, source) + "\n\n"

        return re.sub(
            r"\\begin\{figure\}(?:\[[^\]]*\])?(.*?)\\end\{figure\}",
            replace,
            text,
            flags=re.S,
        )

    def _markdown_image(
        self,
        caption: str,
        image_path: str,
        source_file: Path | None = None,
    ) -> str:
        caption_text = self._plain_text(caption).rstrip(".")
        if caption_text:
            caption_text = caption_text[:1].lower() + caption_text[1:]
        else:
            caption_text = image_path
        alt = f"Figure showing {caption_text}."
        alt = alt.replace("[", "(").replace("]", ")")
        target = self._image_target(image_path, source_file)
        return f"![{alt}]({target})"

    def _render_tikz_target(
        self, figure_body: str, caption: str, label: str
    ) -> str | None:
        if not self.options.render_tikz or self.output_path is None:
            return None
        if shutil.which("pdflatex") is None or shutil.which("pdftoppm") is None:
            return None
        visual_body = self._figure_visual_body(figure_body)
        if not visual_body:
            return None

        slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", label or "tikz_figure").strip("_")
        if not slug:
            slug = "tikz_figure"
        destination_dir = self.output_path.parent / self.options.image_dir
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / f"{slug}.png"

        document = self._standalone_tikz_document(visual_body)
        with tempfile.TemporaryDirectory(prefix="latex-md-tikz-") as tmp:
            tmp_path = Path(tmp)
            tex_path = tmp_path / "figure.tex"
            tex_path.write_text(document, encoding="utf-8")
            pdf_path = tmp_path / "figure.pdf"
            try:
                subprocess.run(
                    [
                        "pdflatex",
                        "-interaction=batchmode",
                        "-halt-on-error",
                        tex_path.name,
                    ],
                    cwd=tmp_path,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                subprocess.run(
                    [
                        "pdftoppm",
                        "-png",
                        "-singlefile",
                        str(pdf_path),
                        str(destination.with_suffix("")),
                    ],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except (OSError, subprocess.CalledProcessError):
                return None

        if self.options.image_mode == "embed":
            mime = "image/png"
            payload = base64.b64encode(destination.read_bytes()).decode("ascii")
            target = f"data:{mime};base64,{payload}"
        else:
            target = self._relative_to_output(destination)
        caption_text = self._plain_text(caption).rstrip(".")
        caption_text = (
            caption_text[:1].lower() + caption_text[1:]
            if caption_text
            else "TikZ figure"
        )
        alt = f"Figure showing {caption_text}."
        return f"![{alt}]({target})"

    def _figure_visual_body(self, figure_body: str) -> str:
        visual = self._replace_command_with_arg(figure_body, "caption", lambda _arg: "")
        visual = re.sub(r"\\label\{[^}]+\}", "", visual)
        visual = visual.strip()
        return visual

    def _standalone_tikz_document(self, tikz_picture: str) -> str:
        preamble = re.sub(
            r"\\documentclass(?:\[[^\]]*\])?\{[^}]+\}", "", self.latex_preamble
        )
        preamble = re.sub(r"\\usepackage(?:\[[^\]]*\])?\{geometry\}", "", preamble)
        return "\n".join(
            [
                r"\documentclass[tikz,border=3pt]{standalone}",
                preamble,
                r"\begin{document}",
                tikz_picture,
                r"\end{document}",
                "",
            ]
        )

    def _image_target(self, image_path: str, source_file: Path | None) -> str:
        resolved = self._resolve_graphic_path(image_path, source_file)
        if self.options.image_mode == "reference" or resolved is None:
            if resolved is not None and self.output_path is not None:
                return self._relative_to_output(resolved)
            return image_path
        if self.options.image_mode == "embed":
            mime = mimetypes.guess_type(resolved.name)[0] or "application/octet-stream"
            payload = base64.b64encode(resolved.read_bytes()).decode("ascii")
            return f"data:{mime};base64,{payload}"
        return self._copy_image(resolved)

    def _resolve_graphic_path(
        self, image_path: str, source_file: Path | None
    ) -> Path | None:
        raw = Path(image_path.strip())
        candidates: list[Path] = []
        if raw.is_absolute():
            candidates.append(raw)
        else:
            if source_file is not None:
                candidates.append(source_file.parent / raw)
            candidates.extend(
                [
                    self.main_dir / raw,
                    self.root / raw,
                    self.root.parent / raw,
                ]
            )
            candidates.extend(path / raw for path in self.graphic_paths)

        expanded: list[Path] = []
        suffixes = ["", ".pdf", ".png", ".jpg", ".jpeg", ".svg"]
        for candidate in candidates:
            if candidate.suffix:
                expanded.append(candidate)
            else:
                expanded.extend(candidate.with_suffix(suffix) for suffix in suffixes)
        for candidate in expanded:
            if candidate.exists():
                return candidate.resolve()
        return None

    def _copy_image(self, source: Path) -> str:
        if self.output_path is None:
            return self._relative_path(source)
        if source in self.copied_images:
            return self._relative_to_output(self.copied_images[source])

        destination_dir = self.output_path.parent / self.options.image_dir
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / source.name
        if destination.exists() and destination.resolve() != source:
            digest = hashlib.sha1(str(source).encode("utf-8")).hexdigest()[:8]
            destination = destination_dir / f"{source.stem}-{digest}{source.suffix}"
        shutil.copy2(source, destination)
        self.copied_images[source] = destination.resolve()
        return self._relative_to_output(destination)

    def _relative_to_output(self, path: Path) -> str:
        if self.output_path is None:
            return self._relative_path(path)
        return os.path.relpath(path, self.output_path.parent).replace(os.sep, "/")

    def _source_from_label(self, label: str) -> str:
        if not label:
            return "figure.tex"
        return re.sub(r"[^A-Za-z0-9_.-]+", "_", label).strip("_") + ".tex"

    def _convert_tables(self, text: str) -> str:
        def replace(match: re.Match[str]) -> str:
            table_body = match.group(1)
            caption = self._first_command_arg(table_body, "caption")
            label = self._first_command_arg(table_body, "label")
            table_markdown = self._convert_first_tabular(table_body)
            prefix = ""
            if caption:
                caption_text = self._plain_text(caption).rstrip(".")
                label_text = f" ({label.strip()})" if label else ""
                prefix = f"*Table: {caption_text}.{label_text}*\n\n"
            return "\n\n" + prefix + table_markdown + "\n\n"

        return re.sub(
            r"\\begin\{table\}(?:\[[^\]]*\])?(.*?)\\end\{table\}",
            replace,
            text,
            flags=re.S,
        )

    def _convert_first_tabular(self, text: str) -> str:
        match = re.search(
            r"\\begin\{tabular\}\{(?:[^{}]|\{[^{}]*\})*\}(.*?)\\end\{tabular\}",
            text,
            re.S,
        )
        if not match:
            return self._format_inline_text(text.strip())
        return self._tabular_to_markdown(match.group(1))

    def _tabular_to_markdown(self, tabular_body: str) -> str:
        body = re.sub(r"\\(?:toprule|midrule|bottomrule|hline)", "", tabular_body)
        body = re.sub(
            r"\\multicolumn\{[^}]+\}\{[^}]+\}\{((?:[^{}]|\{[^{}]*\})*)\}",
            lambda m: m.group(1),
            body,
        )
        rows = []
        for row in re.split(r"(?<!\\)\\\\", body):
            row = row.strip()
            if not row:
                continue
            cells = [self._format_inline_text(cell.strip()) for cell in row.split("&")]
            if cells:
                rows.append(cells)
        if not rows:
            return ""

        width = max(len(row) for row in rows)
        rows = [row + [""] * (width - len(row)) for row in rows]
        header = rows[0]
        lines = [
            "| " + " | ".join(self._escape_table_cell(cell) for cell in header) + " |",
            "| " + " | ".join("---" for _ in header) + " |",
        ]
        for row in rows[1:]:
            lines.append(
                "| " + " | ".join(self._escape_table_cell(cell) for cell in row) + " |"
            )
        return "\n".join(lines)

    def _escape_table_cell(self, cell: str) -> str:
        return cell.replace("|", r"\|").replace("\n", " ").strip()

    def _convert_math_environments(self, text: str) -> str:
        environments = ("equation", "align", "gather", "multline")
        for environment in environments:
            pattern = rf"\\begin\{{{environment}\*?\}}(.*?)\\end\{{{environment}\*?\}}"
            text = re.sub(pattern, self._math_environment_replacement, text, flags=re.S)
        return text

    def _math_environment_replacement(self, match: re.Match[str]) -> str:
        content = match.group(1)
        content = re.sub(r"\\label\{[^}]+\}", "", content)
        content = re.sub(r"\\(?:nonumber|notag)\b", "", content)
        content = re.sub(r"\\tag\{[^}]+\}", "", content)
        content = content.strip()
        return f"\n\n$$\n{content}\n$$\n\n"

    def _convert_theorem_environments(self, text: str) -> str:
        for environment, label in THEOREM_NAMES.items():
            pattern = rf"\\begin\{{{environment}\}}(?:\[([^\]]+)\])?(.*?)\\end\{{{environment}\}}"
            text = re.sub(
                pattern,
                lambda match, label=label: self._theorem_replacement(label, match),
                text,
                flags=re.S,
            )
        text = re.sub(
            r"\\begin\{proof\}(?:\[([^\]]+)\])?(.*?)\\end\{proof\}",
            self._proof_replacement,
            text,
            flags=re.S,
        )
        return text

    def _theorem_replacement(self, label: str, match: re.Match[str]) -> str:
        title = match.group(1)
        body = self._format_inline_text(match.group(2).strip())
        title_text = f" ({self._plain_text(title)})" if title else ""
        return f"\n\n**{label}{title_text}.**\n\n{body}\n\n"

    def _proof_replacement(self, match: re.Match[str]) -> str:
        title = match.group(1)
        body = self._format_inline_text(match.group(2).strip())
        title_text = self._plain_text(title) if title else "Proof"
        return f"\n\n**{title_text}.**\n\n{body}\n\n"

    def _convert_lists(self, text: str, environment: str, ordered: bool) -> str:
        pattern = rf"\\begin\{{{environment}\}}(.*?)\\end\{{{environment}\}}"

        def replace(match: re.Match[str]) -> str:
            content = match.group(1)
            raw_items = [
                item.strip() for item in re.split(r"\\item\b", content) if item.strip()
            ]
            lines = []
            for index, item in enumerate(raw_items, start=1):
                marker = f"{index}." if ordered else "*"
                lines.append(f"{marker} {self._format_inline_text(item)}")
            return "\n\n" + "\n".join(lines) + "\n\n"

        return re.sub(pattern, replace, text, flags=re.S)

    def _convert_headings(self, text: str) -> str:
        heading_levels = {
            "section": "##",
            "subsection": "###",
            "subsubsection": "####",
        }
        for command, hashes in heading_levels.items():
            text = self._replace_command_with_arg(
                text,
                command,
                lambda arg, hashes=hashes: f"\n\n{hashes} {self._plain_text(arg)}\n\n",
            )

        def paragraph_replacement(arg: str) -> str:
            title = self._plain_text(arg).rstrip(".")
            return f"\n\n**{title}.** "

        return self._replace_command_with_arg(text, "paragraph", paragraph_replacement)

    def _convert_inline_markup(self, text: str) -> str:
        text = self._format_inline_text(text)
        text = re.sub(r"\\label\{[^}]+\}", "", text)
        text = re.sub(r"\\begin\{[^}]+\}(?:\[[^\]]*\])?", "", text)
        text = re.sub(r"\\end\{[^}]+\}", "", text)
        text = re.sub(
            r"\\(?:centering|small|footnotesize|scriptsize|normalsize)\b", "", text
        )
        return text

    def _format_inline_text(self, text: str) -> str:
        text = self._expand_macros(text)
        text = self._replace_href(text)
        text = re.sub(
            r"\\cite[A-Za-z]*\*?(?:\[[^\]]*\]){0,2}\{([^}]+)\}",
            lambda match: f"({match.group(1).strip()})",
            text,
        )
        text = re.sub(
            r"\\(?:eqref|ref|autoref)\{([^}]+)\}",
            lambda match: f"({match.group(1).strip()})",
            text,
        )
        text = text.replace(r"\S", "Section ")
        text = self._replace_style_commands(text)
        text = self._replace_plain_wrappers(text)
        text = self._normalize_math_accents(text)
        text = self._simplify_inline_math(text)
        text = text.replace(r"\sep", ",")
        text = text.replace("~", " ")
        text = text.replace(r"\%", "%")
        text = text.replace(r"\_", "_")
        text = text.replace(r"\&", "&")
        text = text.replace(r"\#", "#")
        text = text.replace(r"\$", "$")
        text = text.replace(r"\\", "\n")
        text = re.sub(r"\\(?:quad|qquad|,|;|:|!|\s)", " ", text)
        text = re.sub(r"[ \t]+", " ", text)
        return text.strip()

    def _normalize_math_accents(self, text: str) -> str:
        return re.sub(r"\\(hat|tilde|bar|vec)([A-Za-z])", r"\\\1{\2}", text)

    def _replace_href(self, text: str) -> str:
        while True:
            found = self._find_command_args(text, "href", 0, count=2)
            if found is None:
                return text
            start, end, args = found
            url, label = args
            replacement = f"[{self._format_inline_text(label)}]({url})"
            text = text[:start] + replacement + text[end:]

    def _replace_style_commands(self, text: str) -> str:
        changed = True
        while changed:
            changed = False
            for command, (prefix, suffix) in STYLE_COMMANDS.items():
                new_text = self._replace_command_with_arg(
                    text,
                    command,
                    lambda arg, prefix=prefix, suffix=suffix: (
                        f"{prefix}{self._format_inline_text(arg)}{suffix}"
                    ),
                )
                changed = changed or new_text != text
                text = new_text
        return text

    def _replace_plain_wrappers(self, text: str) -> str:
        for command in ("text", "mathrm", "operatorname", "textsuperscript"):
            text = self._replace_command_with_arg(
                text,
                command,
                lambda arg: self._format_inline_text(arg),
            )
        return text

    def _simplify_inline_math(self, text: str) -> str:
        def replace(match: re.Match[str]) -> str:
            content = match.group(1).strip()
            simple_square = re.fullmatch(r"([A-Za-z])\^2", content)
            if simple_square:
                return f"{simple_square.group(1)}²"
            if content in GREEK_UNICODE:
                return GREEK_UNICODE[content]
            return f"${content}$"

        return re.sub(r"\$([^$\n]+)\$", replace, text)

    def _plain_text(self, text: str | None) -> str:
        if not text:
            return ""
        plain = self._format_inline_text(text)
        plain = plain.replace("$", "")
        plain = plain.replace("**", "")
        plain = plain.replace("*", "")
        plain = re.sub(r"\s+", " ", plain)
        return plain.strip()

    def _first_environment(self, text: str, environment: str) -> str | None:
        match = re.search(
            rf"\\begin\{{{environment}\}}(.*?)\\end\{{{environment}\}}", text, re.S
        )
        return match.group(1) if match else None

    def _first_command_arg(self, text: str, command: str) -> str | None:
        found = self._find_command_args(text, command, 0, count=1)
        return found[2][0] if found else None

    def _iter_command_args(self, text: str, command: str) -> list[tuple[int, int, str]]:
        found_items: list[tuple[int, int, str]] = []
        position = 0
        while True:
            found = self._find_command_args(text, command, position, count=1)
            if found is None:
                return found_items
            start, end, args = found
            found_items.append((start, end, args[0]))
            position = end

    def _replace_command_with_arg(self, text: str, command: str, replacement) -> str:
        position = 0
        while True:
            found = self._find_command_args(text, command, position, count=1)
            if found is None:
                return text
            start, end, args = found
            new_value = replacement(args[0])
            text = text[:start] + new_value + text[end:]
            position = start + len(new_value)

    def _find_command_args(
        self,
        text: str,
        command: str,
        position: int,
        count: int,
    ) -> tuple[int, int, list[str]] | None:
        marker = "\\" + command
        index = text.find(marker, position)
        while index != -1:
            after = index + len(marker)
            if after < len(text) and text[after].isalpha():
                index = text.find(marker, after)
                continue
            cursor = self._skip_latex_space(text, after)
            if cursor < len(text) and text[cursor] == "[":
                cursor = self._consume_balanced(text, cursor, "[", "]")[0]
                cursor = self._skip_latex_space(text, cursor)
            args = []
            valid = True
            for _ in range(count):
                cursor = self._skip_latex_space(text, cursor)
                if cursor >= len(text) or text[cursor] != "{":
                    valid = False
                    break
                cursor, arg = self._consume_balanced(text, cursor, "{", "}")
                args.append(arg)
            if valid:
                return index, cursor, args
            index = text.find(marker, after)
        return None

    def _skip_latex_space(self, text: str, position: int) -> int:
        while position < len(text) and text[position].isspace():
            position += 1
        return position

    def _consume_balanced(
        self, text: str, start: int, opener: str, closer: str
    ) -> tuple[int, str]:
        depth = 0
        escaped = False
        content_start = start + 1
        for index in range(start, len(text)):
            char = text[index]
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if char == opener:
                depth += 1
            elif char == closer:
                depth -= 1
                if depth == 0:
                    return index + 1, text[content_start:index]
        return len(text), text[content_start:]

    def _cleanup_markdown(self, text: str) -> str:
        lines = [line.rstrip() for line in text.splitlines()]
        text = "\n".join(lines)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert a LaTeX project rooted at main.tex to Markdown."
    )
    parser.add_argument("main_tex", type=Path, help="Path to the LaTeX entry point.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Markdown output path. If omitted, writes to stdout.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        help="Project root used to resolve modular includes and assets.",
    )
    parser.add_argument(
        "--image-mode",
        choices=["reference", "copy", "embed"],
        default="copy",
        help="How to write image targets when an output path is provided.",
    )
    parser.add_argument(
        "--image-dir",
        default="assets/images",
        help="Directory, relative to the Markdown output, for copied images.",
    )
    parser.add_argument(
        "--quality-report",
        action="store_true",
        help="Print a short image/table quality report to stderr.",
    )
    parser.add_argument(
        "--render-tikz",
        action="store_true",
        help="Render TikZ-only figure environments to PNG assets when TeX tools are available.",
    )
    args = parser.parse_args(argv)
    options = ConversionOptions(
        project_root=args.project_root,
        image_mode=args.image_mode if args.output is not None else "reference",
        image_dir=args.image_dir,
        render_tikz=args.render_tikz,
    )
    markdown = convert_latex_project(args.main_tex, args.output, options)
    if args.quality_report:
        report = inspect_markdown_quality(markdown, args.output)
        print(
            (
                f"Images: {report.image_count}; tables: {report.table_count}; "
                f"missing images: {len(report.missing_images)}; "
                f"warnings: {len(report.warnings)}"
            ),
            file=sys.stderr,
        )
        for item in report.missing_images:
            print(f"Missing image: {item}", file=sys.stderr)
        for item in report.warnings:
            print(f"Warning: {item}", file=sys.stderr)
    if args.output is None:
        print(markdown, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
