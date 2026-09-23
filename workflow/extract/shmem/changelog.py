"""
identity.since for OpenSHMEM: mechanical extraction from the standard's own
"Changes to this Document" chapter (external-inputs/shmem/tex/shmem-standard/content/
backmatter.tex, \\chapter{Changes to this Document}\\label{sec:changelog}) --
a real, structured, per-version changelog, unlike MPI's chap-changes/ (which
was checked directly and confirmed to have no per-function machine-readable
marker at all; see workflow/extract/mpi/prose.py's module docstring). This is
NOT the same kind of gap MPI has -- OpenSHMEM's source genuinely supports
mechanical since-extraction, it just needs a real parser, built here.

How it works, grounded directly in the real backmatter.tex text (checked
2026-07-20, not guessed):

1. The changelog chapter runs from "\\chapter{Changes to this Document}" to
   the next "\\chapter{" (a later, structurally different "Errata" chapter
   also has per-version \\section{}s but no \\ChangelogRef macros at all --
   excluded by this boundary, not by a name-based heuristic).
2. Within it, each "\\section{Version X.Y}" starts a version's own list of
   "\\item ... \\ChangelogRef{subsec:a, subsec:b}" entries -- oldest is
   Version 1.1 (the changelog's own earliest section; OpenSHMEM's actual
   first published standard was 1.0, one version before the changelog even
   starts -- confirmed against backmatter.tex's own "History of OpenSHMEM"
   chapter, which has no evidence of an earlier public standard version).
3. Not every item's first word means "this introduces something new" --
   confirmed by tallying every item's opening words across all 6 sections:
   "Clarified"/"Deprecated"/"Removed"/"Corrected"/"Revised"/"Renamed"/
   "Replaced"/"Split" are all real, common openings for items that are NOT
   introducing anything new. Only "Added" and "New" are treated as
   introduction markers here -- both appear repeatedly and unambiguously
   ("Added the session routines...", "New \\ac{API}...").
4. "Deprecated ..." items were considered for identity.deprecated_in too and
   deliberately NOT attempted: they routinely deprecate a specific type
   variant or constant of an otherwise-still-current function ("Deprecated
   short and unsigned short variants for shmem_wait_until and shmem_test" --
   shmem_wait_until/shmem_test themselves are not deprecated), and the
   ChangelogRef list mixes real subsec: targets with a separate dep: item
   namespace (pointing into \\chapter{Deprecated API} instead). Automating
   "is the WHOLE function deprecated, or just a variant" from this text
   alone risks a real false positive (marking a live function deprecated),
   which is worse than leaving deprecated_in null -- out of scope here.
5. Item boundaries must be found before searching for ChangelogRef, not the
   other way around: 7 of the changelog's 135 items have no ChangelogRef at
   all (pure prose notes, e.g. "Various fixes to OpenSHMEM code examples").
   A naive "\\item ... \\ChangelogRef" regex would let the search for one
   such item's (nonexistent) ChangelogRef run into the NEXT item's, silently
   misattributing it. Item spans are found by \\item position first, each
   bounded by the next \\item (or the version section's end), and
   ChangelogRef is only searched for inside that bounded span.
6. Each qualifying item's "subsec:X" tokens (dep:X and other non-subsec:
   tokens ignored) map directly to external-inputs/shmem/tex/shmem-standard/content/
   X.tex -- confirmed directly: every \\label{subsec:X} found in main_spec.tex
   is immediately followed by "\\input{content/X.tex}" (same X), not a
   separate lookup table.

Returns {content_filename: version_string}, joined by workflow/extract/
shmem/adapter.py against os.path.basename(path) for each content file it
already processes -- a file not in this map was never mentioned in an
"Added"/"New" item in any processed version, so it's inferred to predate the
changelog's own coverage: OpenSHMEM-1.0.
"""

import os
import sys
import re
_LAYOUT_COMMON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "common")
sys.path.insert(0, _LAYOUT_COMMON)
from layout import EXTERNAL_INPUTS_DIR  # noqa: E402

_BACKMATTER_PATH = os.path.join(
    EXTERNAL_INPUTS_DIR, "shmem", "tex", "shmem-standard", "content", "backmatter.tex",
)

_CHAPTER_RE = re.compile(r"\\chapter\{Changes to this Document\}(.*?)(?=\n\\chapter\{)", re.DOTALL)
_SECTION_RE = re.compile(r"\\section\{Version (\d+\.\d+)\}")
_ITEM_RE = re.compile(r"\\item\s")
_CHANGELOGREF_RE = re.compile(r"\\ChangelogRef\{([^}]*)\}", re.DOTALL)
_SUBSEC_TOKEN_RE = re.compile(r"subsec:(\w+)")
_INTRO_RE = re.compile(r"^(Added|New)\b")


def _version_key(v):
    return tuple(int(x) for x in v.split("."))


def build_since_map():
    with open(_BACKMATTER_PATH, encoding="utf-8", errors="replace") as f:
        text = f.read()

    chapter_match = _CHAPTER_RE.search(text)
    if not chapter_match:
        return {}
    chapter_text = chapter_match.group(1)

    section_matches = list(_SECTION_RE.finditer(chapter_text))
    since_map = {}  # filename -> earliest version seen introducing it

    sections = []
    for i, sm in enumerate(section_matches):
        version = sm.group(1)
        start = sm.end()
        end = section_matches[i + 1].start() if i + 1 < len(section_matches) else len(chapter_text)
        sections.append((version, chapter_text[start:end]))

    # Oldest first, so an earlier "Added" always wins over a later one.
    sections.sort(key=lambda pair: _version_key(pair[0]))

    for version, section_text in sections:
        item_positions = [m.start() for m in _ITEM_RE.finditer(section_text)]
        for i, pos in enumerate(item_positions):
            end = item_positions[i + 1] if i + 1 < len(item_positions) else len(section_text)
            item_text = section_text[pos:end]

            changelogref_match = _CHANGELOGREF_RE.search(item_text)
            if not changelogref_match:
                continue

            item_prose = item_text[:changelogref_match.start()].split("\\item", 1)[-1].strip()
            if not _INTRO_RE.match(item_prose):
                continue

            for subsec in _SUBSEC_TOKEN_RE.findall(changelogref_match.group(1)):
                filename = f"{subsec}.tex"
                if filename not in since_map:
                    # Hyphen, not a space -- "<PPM>-<version>" is the corpus-wide
                    # format, settled 2026-07-22 and now enforced by
                    # api-schema.json's own pattern. See identity.since there.
                    since_map[filename] = f"OpenSHMEM-{version}"

    return since_map
