"""
identity.standard_refs for MPI: heuristic extraction from the .tex chapter
prose surrounding each function's \\begin{mpi-binding} block. apis.json (the
binding-tool's own output) carries neither this nor identity.desc -- confirmed
by direct inspection, see workflow/extract/mpi/adapter.py's module docstring
-- so this is the one place the MPI adapter reads the raw tex directly
instead of trusting the already-mechanical apis.json.

identity.since / identity.deprecated_in are NOT attempted here: chap-changes/
and chap-semantic-changes/ were checked directly and contain no per-function
machine-readable version-introduced marker, only prose that occasionally
names a function inline. Rather than build a fragile heuristic against prose
never designed to be machine-read for this purpose, both fields are left
null with a "note" (not "low_confidence" -- we didn't guess, there was
nothing to guess from). See the plan's open question #3.

identity.desc was ALSO attempted here until 2026-07-20 ("first complete
sentence of prose following the binding block"), then retired -- not because
it was buggy (one real bug, an orphaned-paren issue in the citation-stripping
regex, was found and fixed the same day across 43/571 functions first) but
on a more basic objection: MPI's function semantics routinely span multiple
sentences (confirmed while auditing this desc's output at scale -- see
docs/cross-ppm-analysis/known-gaps-and-open-questions.md), so "first
sentence" is not a defensible general summarization strategy, it's a
structural mismatch between what the field is supposed to hold and what a
one-sentence slice of arbitrary position in the prose can actually convey.
The same objection retired NVSHMEM's Description-block lookup for identity.desc
(workflow/extract/nvshmem/adapter.py) the same day, for the mirrored reason:
that lookup found the right block but it was never one sentence either.
Decision: identity.desc for MPI (and NVSHMEM) is null from Extract
unconditionally now, filled only via curated/supplement/supplement-<ppm>.json's
human-reviewed entries -- see curated/README.md. NCCL and
OpenSHMEM keep their own extraction (a short doc-page paragraph / the
purpose-built \\apisummary{} macro, respectively) -- neither showed this
problem at the same audit pass.

standard_refs, format changed 2026-07-21: each ref is now a plain-English
"<chapter title> - <top-level section title> (MPI-<version>)" string, not a
raw, unresolved LaTeX \\label. The original label-based design (kept in this
docstring's history below) required a real LaTeX build or a hand-maintained
chapter->number map to turn a label into the schema's own documented format
("MPI-4.1 Sec:5.4.2") -- neither exists here, so it settled for the raw
label instead, flagged unresolved. Chapter/section *titles*, unlike section
*numbers*, are plain text sitting directly in \\chapter{}/\\section{} --
no build step needed -- so citing by title sidesteps that blocker entirely.
This also fixed a real bug in the label-based version: the old algorithm
skipped "index-only" lines between a \\subsection{} and its \\label{} using
a regex that didn't recognize every index-macro variant this corpus actually
uses (\\mpitermtitleindexmainsub, \\mpitermtitleindexsubmain, \\MPIbindindexuse
-- anything with text after "index" before the brace), so it stopped
scanning before reaching the real label on functions whose subsection
happened to use one of those variants (confirmed: MPI_Isend). Reading the
title directly out of the \\section{} match itself needs no forward scan at
all, so that whole class of bug no longer exists. Only top-level \\section{}
is tracked (not \\subsection{}/\\subsubsection{}) -- deliberately coarser
than "nearest heading", since a chapter+section pair is precise enough to
locate the right passage without citing to subsection depth.
"""

import glob
import os
import sys
import re

_LAYOUT_COMMON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "common")
sys.path.insert(0, _LAYOUT_COMMON)
from layout import EXTERNAL_INPUTS_DIR  # noqa: E402

_TEX_ROOT = os.path.join(EXTERNAL_INPUTS_DIR, "mpi", "tex", "mpi-standard")
_REPORT_PATH = os.path.join(_TEX_ROOT, "mpi-report.tex")

_CHAPTER_RE = re.compile(r"\\chapter\{")
_SECTION_RE = re.compile(r"\\section\{")  # top-level only -- \subsection{}/\subsubsection{} deliberately not tracked
_FUNCTION_NAME_RE = re.compile(r'function_name\(\s*"([^"]+)"\s*\)')
_BEGIN_BINDING_RE = re.compile(r"\\begin\{mpi-binding\}")
_END_BINDING_RE = re.compile(r"\\end\{mpi-binding\}")

_VERSION_RE = re.compile(r"Version\s+([\d.]+)")
_TEXORPDFSTRING_START_RE = re.compile(r"\\texorpdfstring")
_MACRO_WITH_ARG_RE = re.compile(r"\\[a-zA-Z]+\{([^{}]*)\}")
_BARE_SLASH_MACRO_RE = re.compile(r"\\([a-zA-Z]+)/")  # e.g. \MPI/, \wpm/
_BARE_MACRO_RE = re.compile(r"\\[a-zA-Z]+")


def _extract_braced(text, open_brace_index):
    """text[open_brace_index] must be '{'. Returns the content between it
    and its matching '}', tracking nesting depth so a macro argument that
    itself contains braced sub-macros (e.g. \\texorpdfstring{\\code{x}}{x})
    is captured whole rather than truncated at the first inner '}'.
    """
    depth = 0
    for i in range(open_brace_index, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[open_brace_index + 1:i]
    return text[open_brace_index + 1:]


def _resolve_texorpdfstring(text):
    """Replace every \\texorpdfstring{pdf}{plain} with just its plain-text
    (second) argument, brace-depth aware in both arguments.
    """
    out = []
    i = 0
    while True:
        m = _TEXORPDFSTRING_START_RE.search(text, i)
        if not m:
            out.append(text[i:])
            break
        out.append(text[i:m.start()])
        pos = m.end()
        while pos < len(text) and text[pos] != "{":
            pos += 1
        if pos >= len(text):
            out.append(text[m.start():])
            break
        pdf_arg = _extract_braced(text, pos)
        pos += len(pdf_arg) + 2
        while pos < len(text) and text[pos] != "{":
            pos += 1
        if pos >= len(text):
            out.append(pdf_arg)
            break
        plain_arg = _extract_braced(text, pos)
        out.append(plain_arg)
        i = pos + len(plain_arg) + 2
    return "".join(out)


def _clean_title(raw):
    text = _resolve_texorpdfstring(raw)
    text = _BARE_SLASH_MACRO_RE.sub(lambda m: m.group(1), text)
    prev = None
    while prev != text:
        prev = text
        text = _MACRO_WITH_ARG_RE.sub(r"\1", text)
    text = _BARE_MACRO_RE.sub("", text)
    text = text.replace("\\_", "_")
    return re.sub(r"\s+", " ", text).strip()


def _standard_version():
    with open(_REPORT_PATH, encoding="utf-8", errors="replace") as f:
        text = f.read()
    m = _VERSION_RE.search(text)
    return f"MPI-{m.group(1)}" if m else None


def _chapter_files():
    pattern = os.path.join(_TEX_ROOT, "chap-*", "*.tex")
    return sorted(f for f in glob.glob(pattern) if not f.endswith("-rendered.tex"))


def build_prose_index():
    """Scan every non-rendered chapter .tex file once; return
    {function_key: {"standard_refs": [str]}}, each ref a plain-English
    "<chapter> - <section> (MPI-<version>)" citation.
    """
    version = _standard_version()
    index = {}

    for path in _chapter_files():
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        current_chapter_title = None
        current_section_title = None
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            if not stripped.startswith("%"):
                m = _CHAPTER_RE.search(line)
                if m:
                    current_chapter_title = _clean_title(_extract_braced(line, m.end() - 1))
                    current_section_title = None

                m = _SECTION_RE.search(line)
                if m:
                    current_section_title = _clean_title(_extract_braced(line, m.end() - 1))

            if _BEGIN_BINDING_RE.search(line):
                block_start = i
                block_end = block_start
                while block_end < len(lines) and not _END_BINDING_RE.search(lines[block_end]):
                    block_end += 1
                block_text = "".join(lines[block_start:block_end + 1])

                fn_match = _FUNCTION_NAME_RE.search(block_text)
                if fn_match:
                    fn_name = fn_match.group(1)
                    function_key = fn_name.lower()

                    parts = [p for p in (current_chapter_title, current_section_title) if p]
                    if parts:
                        ref = " - ".join(parts)
                        if version:
                            ref = f"{ref} ({version})"
                    else:
                        ref = None

                    entry = index.setdefault(function_key, {"standard_refs": []})
                    if ref and ref not in entry["standard_refs"]:
                        entry["standard_refs"].append(ref)

                i = block_end

            i += 1

    return index
