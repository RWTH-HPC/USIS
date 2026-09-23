"""
Reads every curated/supplement/supplement-<ppm>.json (see curated/README.md)
and turns its entries into needs_approval field proposals against the full
corpus -- "proposals[entry_key][field_path] = {value, note}", which
workflow/assemble/assemble.py obtains by calling build_proposals() directly and
applies via its _apply_field_proposals. Nothing is written to disk: eligibility
depends entirely on which fields are still null in the corpus being merged, so
a materialized proposals file could only ever be a stale duplicate of its two
inputs (removed 2026-07-22). Run this module directly to inspect what it would
contribute; see run()'s docstring.

The precedence rule (curated/README.md): supplement never
overrides, it only fills a stage-confirmed null. This script is where that
rule is actually enforced, not just documented -- for every (entry_key,
field_path) in a supplement.json file, it reads the CURRENT value from
instances/1_syntactic-semantics-api.json and only proposes the supplement
value if that field is genuinely null there right now. An entry whose target
field already holds a real value (even a low-confidence one) is skipped and
recorded, not silently dropped -- if supplement.json and the pipeline ever
drift out of sync (e.g. a future Extract/Classify improvement fills a field
supplement.json still has an entry for), this script surfaces that as a
visible skip instead of quietly overriding or quietly proposing a redundant
duplicate.

field_path supports one bracket segment for addressing into a parameters[]
element by name (e.g. "parameters[buf].length"), via workflow/common/paths.py
-- shared with assemble.py's write side so the two can never disagree on
what a path means. get_path distinguishes a field that's ABSENT (its owning
stage hasn't run yet -- omitted, not eligible, see docs/overview/glossary.md (Staging schema)) from a field that's a real, considered `null` (eligible).

ABSENT is *also* eligible for one specific, narrow class of field, per
curated/field-provenance.json's "supplement" tier entry, 2026-07-21 exception:
fields marked `"stage_c_mechanism": "supplement"` there are the ~24 pure-prose
Stage C fields formerly proposed by a now-retired separate AI-Assisted
Classification stage (workflow/classify/ai_classify.py). Nothing else will
ever populate them, so for exactly these paths "omitted" doesn't mean "a real
stage hasn't run yet" (the ordinary reason ABSENT stays ineligible) -- it
means "supplement.json is the only mechanism left." Every other omitted field
(e.g. semantics.formal before Generate Formal runs) stays ineligible, since a
real stage genuinely is still going to run for those.

Run directly: python3 workflow/supplement/propose.py
"""

import argparse
import glob
import json
import os
import re
import sys

_HERE = os.path.dirname(__file__)
_ROOT = os.path.join(_HERE, "..", "..")

sys.path.insert(0, os.path.join(_ROOT, "workflow", "common"))
from paths import ABSENT, get_path  # noqa: E402
from layout import FIELD_PROVENANCE_PATH, OUT_DIR, SUPPLEMENT_DIR  # noqa: E402

_INPUTS_GLOB = os.path.join(SUPPLEMENT_DIR, "supplement-*.json")
_PROVENANCE_PATH = FIELD_PROVENANCE_PATH

_CORPUS_SEMANTICS_API_PATH = os.path.join(OUT_DIR, "1_syntactic-semantics-api.json")

_BRACKET_NAME_RE = re.compile(r"\[[^\[\]]+\]")


def _load_provenance_fields():
    with open(_PROVENANCE_PATH) as f:
        return json.load(f)["fields"]


def _stage_c_via_supplement(field_path, provenance_fields):
    """True iff field_path is marked stage_c_mechanism=supplement in
    field-provenance.json. Three ways a path can be covered:
      - an exact entry at this path (e.g. "relationships.superseded_by")
      - a ".*" wildcard covering a LEAF beneath it (e.g. "semantics.memory.*"
        covering "semantics.memory.buffer_reuse")
      - a ".*" wildcard covering the CONTAINER itself as one wholesale unit
        (e.g. "semantics.memory.*" also covering "semantics.memory" -- a
        proposal for the whole object being null, not one of its leaves;
        same "container governed by its only wildcard" idea as
        workflow/staging/derive_schema.py's _governing_tier)
    field_path's bracket segment (e.g. "parameters[buf]") is normalized to
    the empty-bracket form field-provenance.json itself uses ("parameters[]")
    before matching, since provenance is keyed by field shape, not by which
    named parameter a given proposal happens to target."""
    normalized = _BRACKET_NAME_RE.sub("[]", field_path)

    # Exact match wins outright, and must be tried on its own before the
    # container-wildcard form below. field-provenance.json deliberately
    # carries BOTH spellings for the conditional sub-objects -- e.g.
    # "semantics.atomic.*" (tier semantic_heuristic: the leaves, which the
    # naming-convention classifier owns) and "semantics.atomic" (tier
    # semantic, stage_c_mechanism supplement: the whole object being null,
    # which only supplement can state). Testing both spellings in one loop
    # let whichever appeared first in the file win, so a proposal for
    # "semantics.atomic" was resolved against the *.* entry's provenance and
    # judged ineligible -- silently skipping all 42 pilot entries' explicit
    # "this is not an atomic" null (found 2026-07-21).
    for f in provenance_fields:
        if f["path"] == normalized:
            return f.get("stage_c_mechanism") == "supplement"

    # A container addressed as one wholesale unit, governed by its own only
    # wildcard (e.g. "semantics.memory" covered by "semantics.memory.*") --
    # same "container governed by its only wildcard" idea as
    # workflow/staging/derive_schema.py's _governing_tier.
    for f in provenance_fields:
        if f["path"] == normalized + ".*":
            return f.get("stage_c_mechanism") == "supplement"

    # A leaf beneath a wildcard (e.g. "semantics.memory.buffer_reuse").
    for f in provenance_fields:
        if f["path"].endswith(".*") and normalized.startswith(f["path"][:-1]):
            return f.get("stage_c_mechanism") == "supplement"

    return False


def _ppm_from_path(supplement_path):
    # curated/supplement/supplement-<ppm>.json -> <ppm>
    stem = os.path.splitext(os.path.basename(supplement_path))[0]
    if not stem.startswith("supplement-"):
        raise ValueError(f"not a supplement input filename: {supplement_path}")
    return stem[len("supplement-"):]


def build_proposals(semantics_api=None, supplement_paths=None, provenance_fields=None, corpus_label="pilot corpus",
                    models=None):
    """-> (proposals: {entry_key: {field_path: {value, note}}}, skipped: [dict]).
    `semantics_api` is the 1_syntactic-semantics-api.json dict to check
    eligibility against -- the pilot subset or the full corpus; `corpus_label`
    only affects the human-readable skip messages; `models`, when given, reads
    only those models' supplement files. Exposed as a function (not just a
    script) so both run() modes reuse it."""
    if semantics_api is None:
        with open(_CORPUS_SEMANTICS_API_PATH) as f:
            semantics_api = json.load(f)
    if supplement_paths is None:
        supplement_paths = sorted(glob.glob(_INPUTS_GLOB))
    if models is not None:
        supplement_paths = [p for p in supplement_paths if _ppm_from_path(p) in models]
    if provenance_fields is None:
        provenance_fields = _load_provenance_fields()

    proposals = {}
    skipped = []

    for path in supplement_paths:
        ppm = _ppm_from_path(path)
        with open(path) as f:
            supplement = json.load(f)

        for function_key, fields in supplement.items():
            entry_key = f"{ppm}:{function_key}"
            entry = semantics_api.get(entry_key)
            if entry is None:
                skipped.append({
                    "entry_key": entry_key, "field": None, "reason":
                    f"not in the {corpus_label} -- no such entry to fill",
                })
                continue

            for field_path, sup_entry in fields.items():
                current = get_path(entry, field_path)
                if current is ABSENT and not _stage_c_via_supplement(field_path, provenance_fields):
                    skipped.append({
                        "entry_key": entry_key, "field": field_path, "reason":
                        "field/parameter doesn't resolve (missing key, or no parameters[] element with that "
                        "name) -- not the same as a stage-confirmed null, see "
                        "docs/overview/glossary.md (Staging schema)",
                    })
                    continue
                if current is not None and current is not ABSENT:
                    skipped.append({
                        "entry_key": entry_key, "field": field_path, "reason":
                        f"current value is not null (supplement never overrides a real value): {current!r}",
                    })
                    continue

                method = sup_entry["method"]
                source_url = sup_entry.get("source_url")
                note = f"[supplement.json, method={method}" + (f", source={source_url}" if source_url else "") + f"] {sup_entry['note']}"
                proposals.setdefault(entry_key, {})[field_path] = {
                    "value": sup_entry["value"],
                    "note": note,
                }

    return proposals, skipped


def source_files():
    return sorted(os.path.relpath(p, _ROOT) for p in glob.glob(_INPUTS_GLOB))


def run(argv=None):
    """Inspection CLI, not a workflow stage (2026-07-22): prints the proposals
    this module would contribute to a merge. workflow/assemble/assemble.py calls
    build_proposals() directly and applies the result in memory -- there is no
    intermediate supplement-proposals.json anymore, because the projection is a
    pure function of the curated supplement files and the current corpus, and a
    checked-in copy could only ever be a stale duplicate of both."""
    parser = argparse.ArgumentParser(
        description="Print the supplement values eligible to fill gaps in the current corpus. "
                    "Read-only: the build applies these itself, in memory.")
    parser.add_argument("--out", metavar="FILE", default=None,
                        help="write the proposals here instead of stdout")
    parser.add_argument("--summary", action="store_true",
                        help="print counts only, not the proposals themselves")
    args = parser.parse_args(argv)

    with open(_CORPUS_SEMANTICS_API_PATH) as f:
        semantics_api = json.load(f)

    proposals, skipped = build_proposals(semantics_api=semantics_api, corpus_label="full corpus")
    out = {"source_files": source_files(), "proposals": proposals, "skipped": skipped}

    n_fields = sum(len(v) for v in proposals.values())
    if args.summary:
        print(f"{n_fields} field proposal(s) across {len(proposals)} entries; "
              f"{len(skipped)} supplement entries skipped (target field already populated)")
        return 0
    if args.out:
        with open(args.out, "w") as f:
            json.dump(out, f, indent=2, sort_keys=True)
            f.write("\n")
        print(f"wrote {n_fields} field proposal(s) across {len(proposals)} entries to {args.out}")
        return 0
    json.dump(out, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(run())
