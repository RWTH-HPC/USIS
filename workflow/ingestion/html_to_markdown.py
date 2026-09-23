"""Convert rendered doc pages (NCCL/NVSHMEM/CUDA HTML) into Markdown.

docs.nvidia.com serves two renderings, and this script handles both. The
Sphinx theme family used for NCCL and NVSHMEM wraps page content in a single
``<div itemprop="articleBody">`` container; the archived CUDA toolkit docs
(``/cuda/archive/<version>/``) are DITA-generated and wrap it in a
``<div class="topic ..." id="...">`` instead (added 2026-09-11 for
``external-inputs/cuda/docs/``). NVIDIA's version archive
(``archive.docs.nvidia.com``) re-renders older Sphinx docs in the PyData theme,
which wraps content in ``<article class="bd-article">`` (added 2026-09-23 for
the NVSHMEM 3.7.0 archive; the Markdown differs in layout from the original
theme's, but Extract reads the same values from it). Any one starts capture, and because capture
only ever starts once, a nested DITA topic does not restart it. This script
extracts only that container and renders a readable Markdown transcript of it:
headings, prose, lists, tables, and code/signature blocks. It intentionally does not try to
recover structured per-parameter data (that is the job of the workflow's
Extract stage, not this conversion) -- the goal here is a faithful, greppable
text transcript of the source page, mirroring what a syntactic-extraction
pass would be given for a LaTeX standard chapter.

Deterministic, stdlib-only (html.parser) by design: no network calls, no
third-party dependencies, same input always produces the same Markdown.
"""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

ARTICLE_BODY_ATTR = ("itemprop", "articleBody")

# DITA pages carry no itemprop; their content sits in the outermost topic div,
# which always has an id (e.g. <div class="topic nested1" id="api-sync-behavior">).
DITA_TOPIC_CLASS = "topic"

# PyData-theme pages (NVIDIA's version archive) carry neither; their content is
# the one <article class="bd-article">.
PYDATA_ARTICLE_CLASS = "bd-article"

# Tags whose content should be dropped entirely (not just unwrapped).
SKIP_CONTENT_TAGS = {"script", "style"}

# Void elements: no matching end tag, never pushed onto the tag stack.
VOID_TAGS = {
    "br", "hr", "img", "input", "meta", "link", "col", "area", "base",
    "embed", "source", "track", "wbr",
}

HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}


class MarkdownRenderer(HTMLParser):
    def __init__(self, base_url: str | None = None):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.out: list[str] = []
        self.tag_stack: list[tuple[str, dict]] = []
        self.capture_depth: int | None = None  # index in tag_stack where articleBody started
        self.skip_depth = 0  # >0 while inside a SKIP_CONTENT_TAGS element
        self.pre_depth = 0  # >0 while inside <pre>
        self.list_stack: list[dict] = []  # {"type": "ul"/"ol", "n": int}
        self.link_href: list[str | None] = []
        self.table_rows: list[list[str]] = []
        self.table_row: list[str] | None = None
        self.table_cell: list[str] | None = None
        self.highlight_lang: list[str | None] = []

    # -- helpers ---------------------------------------------------------

    def _capturing(self) -> bool:
        return self.capture_depth is not None

    def _emit(self, text: str) -> None:
        if not self._capturing() or self.skip_depth:
            return
        if self.table_cell is not None:
            self.table_cell.append(text)
        else:
            self.out.append(text)

    def _blank_line(self) -> None:
        if self._capturing() and not self.skip_depth and self.table_cell is None:
            self.out.append("\n\n")

    def _has_class(self, attrs: dict, name: str) -> bool:
        classes = (attrs.get("class") or "").split()
        return name in classes

    # -- HTMLParser hooks --------------------------------------------------

    def handle_starttag(self, tag: str, attrs_list):
        attrs = dict(attrs_list)
        is_void = tag in VOID_TAGS
        if not is_void:
            self.tag_stack.append((tag, attrs))

        if tag in SKIP_CONTENT_TAGS:
            self.skip_depth += 1
            return

        if self.capture_depth is None:
            is_sphinx_body = attrs.get(ARTICLE_BODY_ATTR[0]) == ARTICLE_BODY_ATTR[1]
            is_dita_topic = tag == "div" and self._has_class(attrs, DITA_TOPIC_CLASS) and bool(attrs.get("id"))
            is_pydata_article = tag == "article" and self._has_class(attrs, PYDATA_ARTICLE_CLASS)
            if is_sphinx_body or is_dita_topic or is_pydata_article:
                self.capture_depth = len(self.tag_stack) - 1
            return

        if self.skip_depth:
            return

        # Skip Sphinx's "permalink to this heading" pilcrow anchors entirely.
        if tag == "a" and self._has_class(attrs, "headerlink"):
            self.skip_depth += 1
            return

        if tag in HEADING_TAGS:
            level = int(tag[1])
            self._blank_line()
            self._emit("#" * level + " ")
        elif tag == "p":
            self._blank_line()
        elif tag == "dt":
            self._blank_line()
        elif tag == "dd":
            self._blank_line()
        elif tag in ("ul", "ol"):
            self.list_stack.append({"type": tag, "n": 0})
        elif tag == "li":
            self._blank_line()
            if self.list_stack:
                entry = self.list_stack[-1]
                indent = "  " * (len(self.list_stack) - 1)
                if entry["type"] == "ol":
                    entry["n"] += 1
                    self._emit(f"{indent}{entry['n']}. ")
                else:
                    self._emit(f"{indent}- ")
        elif tag == "blockquote":
            self._blank_line()
            self._emit("> ")
        elif tag == "pre":
            self.pre_depth += 1
            lang = self.highlight_lang[-1] if self.highlight_lang else None
            self._blank_line()
            self._emit(f"```{lang or ''}\n")
        elif tag == "code" and self.pre_depth == 0:
            self._emit("`")
        elif tag in ("strong", "b"):
            self._emit("**")
        elif tag in ("em", "i"):
            self._emit("*")
        elif tag == "br":
            self._emit("  \n" if self.pre_depth == 0 else "\n")
        elif tag == "hr":
            self._blank_line()
            self._emit("---")
            self._blank_line()
        elif tag == "a":
            href = attrs.get("href")
            if href and self.base_url:
                href = urljoin(self.base_url, href)
            self.link_href.append(href)
            self._emit("[")
        elif tag == "table":
            self.table_rows = []
        elif tag == "tr":
            self.table_row = []
        elif tag in ("td", "th"):
            self.table_cell = []
        elif tag == "div" and self._has_class(attrs, "highlight"):
            m = re.search(r"highlight-(\S+)", attrs.get("class", ""))
            self.highlight_lang.append(m.group(1) if m else None)

    def handle_endtag(self, tag: str):
        if tag in VOID_TAGS:
            return
        if not self.tag_stack or self.tag_stack[-1][0] != tag:
            # Malformed/unbalanced markup: pop best-effort match if present.
            for i in range(len(self.tag_stack) - 1, -1, -1):
                if self.tag_stack[i][0] == tag:
                    del self.tag_stack[i:]
                    break
            return

        depth_before_pop = len(self.tag_stack) - 1
        self.tag_stack.pop()

        if tag in SKIP_CONTENT_TAGS:
            self.skip_depth -= 1
            return

        if self.capture_depth is not None and depth_before_pop == self.capture_depth and tag == "div":
            self.capture_depth = None
            return

        if self.capture_depth is None:
            return

        if self.skip_depth:
            if tag == "a":
                self.skip_depth -= 1
            return

        if tag in HEADING_TAGS or tag == "p" or tag == "dd" or tag == "dt" or tag == "blockquote":
            self._blank_line()
        elif tag in ("ul", "ol"):
            if self.list_stack:
                self.list_stack.pop()
            self._blank_line()
        elif tag == "pre":
            self.pre_depth -= 1
            self._emit("\n```")
            self._blank_line()
        elif tag == "code" and self.pre_depth == 0:
            self._emit("`")
        elif tag in ("strong", "b"):
            self._emit("**")
        elif tag in ("em", "i"):
            self._emit("*")
        elif tag == "a":
            href = self.link_href.pop() if self.link_href else None
            if href:
                self._emit(f"]({href})")
            else:
                self._emit("]")
        elif tag == "td" or tag == "th":
            cell_text = "".join(self.table_cell or []).strip()
            self.table_cell = None
            if self.table_row is not None:
                self.table_row.append(cell_text)
        elif tag == "tr":
            if self.table_row is not None:
                self.table_rows.append(self.table_row)
            self.table_row = None
        elif tag == "table":
            self._emit(self._render_table(self.table_rows))
            self.table_rows = []
            self._blank_line()
        elif tag == "div" and self.highlight_lang and self.pre_depth == 0:
            # Best-effort: pop highlight-lang tracking once its div closes.
            # (Approximate -- nested non-highlight divs inside won't double-push.)
            pass

    def handle_data(self, data: str):
        if self.capture_depth is None or self.skip_depth:
            return
        if self.pre_depth:
            self._emit(data)
            return
        # Collapse whitespace runs (source HTML is heavily indented) but
        # keep at least one space so words don't run together.
        collapsed = re.sub(r"[ \t\r\n]+", " ", data)
        if collapsed:
            self._emit(collapsed)

    @staticmethod
    def _render_table(rows: list[list[str]]) -> str:
        if not rows:
            return ""
        lines = ["| " + " | ".join(rows[0]) + " |"]
        lines.append("| " + " | ".join("---" for _ in rows[0]) + " |")
        for row in rows[1:]:
            lines.append("| " + " | ".join(row) + " |")
        return "\n" + "\n".join(lines) + "\n"

    def markdown(self) -> str:
        text = "".join(self.out)
        text = text.replace("\xa0", " ")
        # Lines that are only whitespace (leftover from empty <p>/<dd> etc.)
        # become truly empty so blank-line collapsing below can remove them.
        text = re.sub(r"(?m)^[ \t]+$", "", text)
        # Collapse 3+ blank lines down to 2 (one blank line between blocks).
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip() + "\n"


def convert_html(html: str, source_url: str | None = None) -> str:
    renderer = MarkdownRenderer(base_url=source_url)
    renderer.feed(html)
    return renderer.markdown()


def convert_tree(raw_dir: Path, out_dir: Path, base_url: str) -> list[Path]:
    """Convert every .html file under raw_dir into a mirrored .md file under out_dir."""
    written = []
    for html_path in sorted(raw_dir.rglob("*.html")):
        rel = html_path.relative_to(raw_dir)
        source_url = base_url.rstrip("/") + "/" + rel.as_posix()
        md_path = out_dir / rel.with_suffix(".md")
        md_path.parent.mkdir(parents=True, exist_ok=True)
        html = html_path.read_text(encoding="utf-8", errors="replace")
        md = convert_html(html, source_url=source_url)
        header = f"<!-- source: {source_url} -->\n\n"
        md_path.write_text(header + md, encoding="utf-8")
        written.append(md_path)
    return written


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("usage: html_to_markdown.py <raw_dir> <out_dir> <base_url>", file=sys.stderr)
        sys.exit(1)
    raw_dir, out_dir, base_url = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    files = convert_tree(raw_dir, out_dir, base_url)
    print(f"converted {len(files)} pages -> {out_dir}")
