"""Slice the OpenMP specification's runtime-library chapter into one Markdown
file per routine.

`external-inputs/openmp/docs/5.2/text/*.txt` is `pdftotext -layout` output of
the vendored specification PDF: the whole standard as one ~27k-line text file,
carrying the specification's own line numbers in a left-hand column and a page
header or footer every page. This script cuts it into `md/<routine>.md`, one
file per `omp_*` routine, so that Extract can read a single routine's Summary
and C prototype without carrying a PDF parser.

Like `workflow/ingestion/html_to_markdown.py`, it is deterministic, stdlib-only,
and deliberately dumb about structure: it preserves the section's own text
(Summary / Format / Binding / Effect / Restrictions / Cross References) and
leaves recovering per-parameter data to the Extract adapter.

**The line-number column is stripped before any heading is detected**, which is
load-bearing rather than cosmetic: the specification numbers its own body lines,
so `pdftotext` renders an ordinary line as "  25   Format" -- indistinguishable
from a chapter heading "25 OMPT Interface" while the column is still there.
Stripping first leaves real headings as "18.2.4 omp_get_thread_num" and turns
that body line into a bare "Format", which matches nothing.

Two shapes in the source need handling beyond "one heading, one routine":

  - **Shared sections.** Lock and allocator routines are documented in pairs,
    e.g. "18.9.1 omp_init_lock and omp_init_nest_lock" and "18.13.6 omp_alloc
    and omp_aligned_alloc". Every routine named in the heading gets its own
    file, all with the same body; each file says which routines share it.
  - **Headings that do not name the routine.** Chapter 18's single-routine
    sections -- "18.14 Tool Control Routine" (omp_control_tool) and "18.15
    Environment Display Routine" (omp_display_env) -- name the topic, not the
    function. Those sections are attributed by finding a C prototype for an
    `omp_*` routine in the section's own Format block.

Run when refreshing the vendored specification, not as part of a build:

    python3 workflow/ingestion/openmp_spec_text.py \\
        external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt \\
        external-inputs/openmp/docs/5.2/md
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# A page footer ("354 OpenMP API - Version 5.2 November 2021") or header
# ("CHAPTER 18. RUNTIME LIBRARY ROUTINES 439"): pure pagination, dropped.
_PAGE_FOOTER_RE = re.compile(r"^\s*\d*\s*OpenMP API\s+[–-]\s+Version\b.*$")
_PAGE_HEADER_RE = re.compile(r"^\s*(?:\d+\s+)?CHAPTER \d+\..*$")

# The specification numbers every line of its own body text; pdftotext keeps
# that column, so "  2   The omp_get_thread_num routine ..." starts with it.
_LINE_NUMBER_RE = re.compile(r"^\s{0,10}\d{1,2}\s{2,}")

# Table-of-contents rows carry dotted leaders to a page number.
_TOC_RE = re.compile(r"\.\s\.\s\.")

# Matched against line-number-stripped text: "18.2.4 omp_get_thread_num".
_HEADING_RE = re.compile(r"^(\d+(?:\.\d+){1,2})\s+(\S.*?)\s*$")
# A chapter start ("19 OMPT Interface"), which bounds the last section.
_CHAPTER_RE = re.compile(r"^(\d{1,2})\s+([A-Z]\S*(?:\s+\S+){0,5})\s*$")

_ROUTINE_RE = re.compile(r"omp_[a-z0-9_]+")
# A C prototype line inside a Format block: "int omp_control_tool(int command, ...);"
_PROTOTYPE_RE = re.compile(r"^\s*(?:const\s+)?[A-Za-z_]\w*(?:\s*\*)?\s*\*?\s*(omp_[a-z0-9_]+)\s*\(")


def _is_toc(line: str) -> bool:
    return bool(_TOC_RE.search(line))


def strip_noise(lines: list[str]) -> list[str]:
    """Page furniture dropped and the line-number column removed, with index
    alignment preserved so section boundaries stay valid (a dropped line
    becomes empty rather than disappearing)."""
    out = []
    for line in lines:
        if _PAGE_FOOTER_RE.match(line) or _PAGE_HEADER_RE.match(line):
            out.append("")
            continue
        out.append(_LINE_NUMBER_RE.sub("", line.rstrip()).rstrip())
    return out


def routine_names(title: str) -> list[str]:
    """The routines a heading names, or [] if it names something else.

    "omp_init_lock and omp_init_nest_lock" -> both; "Tool Control Routine" -> [].
    """
    text = title.replace("(Deprecated)", " ")
    names = _ROUTINE_RE.findall(text)
    if not names:
        return []
    # Everything the names, separators and filler words leave behind must be
    # empty, or the heading is prose that merely mentions a routine.
    residue = _ROUTINE_RE.sub(" ", text)
    residue = re.sub(r"\band\b|,|\s+", "", residue)
    return names if not residue else []


def prototyped_routines(body: str) -> list[str]:
    """The routines a section declares a real C prototype for.

    The terminating ');' is required, and a prototype pdftotext broke across
    lines is joined until it: without that, section 6.2's allocator table --
    whose rows read "omp_const_mem_alloc   omp_const_mem_space   (none)" --
    parses as a prototype for a memory-space *constant*.
    """
    lines = body.split("\n")
    found = []
    for i, line in enumerate(lines):
        m = _PROTOTYPE_RE.match(line)
        if not m:
            continue
        decl, j = line, i
        while ");" not in decl and j + 1 < len(lines) and len(decl) < 600:
            j += 1
            decl += " " + lines[j].strip()
        if re.search(rf"\b{re.escape(m.group(1))}\s*\(.*?\)\s*;", decl, re.DOTALL):
            found.append(m.group(1))
    return list(dict.fromkeys(found))


def section_body(lines: list[str]) -> str:
    text = "\n".join(line.rstrip() for line in lines)
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


def find_sections(lines: list[str]) -> list[dict]:
    """-> [{"line": int, "number": str, "title": str}] over noise-stripped lines."""
    sections: list[dict] = []
    for i, line in enumerate(lines):
        if _is_toc(line):
            continue
        m = _HEADING_RE.match(line)
        if m:
            number, title = m.group(1), m.group(2)
            # "18.9.2 omp_init_lock_with_hint and" continues on the next line.
            if title.endswith(" and"):
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines) and not _is_toc(lines[j]):
                    title = f"{title} {lines[j].strip()}"
            sections.append({"line": i, "number": number, "title": title})
            continue
        m = _CHAPTER_RE.match(line)
        if m:
            sections.append({"line": i, "number": m.group(1), "title": m.group(2)})
    return sections


def slice_routines(text: str) -> dict[str, dict]:
    """-> {routine: {"number", "title", "body", "shared_with"}}."""
    lines = strip_noise(text.replace("\f", "\n").split("\n"))
    sections = find_sections(lines)
    bodies = []
    for idx, sec in enumerate(sections):
        end = sections[idx + 1]["line"] if idx + 1 < len(sections) else len(lines)
        bodies.append(section_body(lines[sec["line"] + 1:end]))

    # The chapter each section sits under: its own number's first component,
    # resolved against the chapter headings found in the same pass. 5.2 puts
    # every routine in chapter 18; 6.0 spreads them over chapters 21-31, so the
    # consumer must read the chapter rather than assume it.
    chapters = {sec["number"]: sec["title"] for sec in sections if "." not in sec["number"]}

    def chapter_of(sec):
        number = sec["number"].split(".")[0]
        title = chapters.get(number)
        return f"{number} {title}" if title else None

    out: dict[str, dict] = {}

    def record(name, sec, body, shared):
        # A routine named in more than one place keeps the longest section,
        # which is the real one rather than a summary-table mention.
        if name not in out or len(body) > len(out[name]["body"]):
            out[name] = {"number": sec["number"], "title": sec["title"], "body": body,
                         "chapter": chapter_of(sec), "shared_with": [n for n in shared if n != name]}

    # Pass 1: headings that name their routines.
    for sec, body in zip(sections, bodies):
        names = routine_names(sec["title"])
        for name in names:
            record(name, sec, body, names)

    # Pass 2: sections whose heading names a topic rather than a routine, by
    # looking for a C prototype in the section's own text.
    for sec, body in zip(sections, bodies):
        if routine_names(sec["title"]):
            continue
        found = prototyped_routines(body)
        for name in found:
            record(name, sec, body, found)
    return out


def write_markdown(routines: dict[str, dict], out_dir: Path, source_rel: str) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, sec in sorted(routines.items()):
        header = [f"<!-- source: OpenMP API Specification, section {sec['number']} ({sec['title']}) -->",
                  f"<!-- sliced from {source_rel} by workflow/ingestion/openmp_spec_text.py -->"]
        if sec.get("chapter"):
            header.append(f"<!-- chapter: {sec['chapter']} -->")
        if sec["shared_with"]:
            header.append(f"<!-- section shared with: {', '.join(sec['shared_with'])} -->")
        path = out_dir / f"{name}.md"
        path.write_text("\n".join(header) + f"\n\n# {sec['number']} {sec['title']}\n\n" + sec["body"],
                        encoding="utf-8")
        written.append(path)
    return written


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: openmp_spec_text.py <spec_text_file> <out_dir>", file=sys.stderr)
        sys.exit(1)
    text_path, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    routines = slice_routines(text_path.read_text(encoding="utf-8", errors="replace"))
    files = write_markdown(routines, out_dir, text_path.as_posix())
    print(f"sliced {len(files)} routine section(s) -> {out_dir}")
