"""
Provenance: one record per value in the corpus, saying how it was derived and
whether a human has approved it.

Runs after validate, before split:

    extract -> classify -> assign [curated] -> assemble -> validate ->
    THIS SCRIPT -> split

Why a stage rather than a field on the entry: the workflow's confidence wrapper
(common/ir.py's Confident) is deliberately unwrapped on the way into a
checkpoint, so a shipped entry holds values and nothing else. That keeps the
consumer contract to the eight sections and their closed vocabularies -- a tool
reading semantics.formal never has to step around a provenance envelope. The
derivation record is real and needed, so it ships, but it ships beside the
corpus rather than inside it, keyed by the same model-qualified keys.

Before this existed the same information was spread over three files that were
each a by-product of one stage: extract-report.json's flags, classify-report.json's
flags, and 4_final-api.json's promotion_log. Answering "where did this value come
from" meant joining all three by hand, and the fields no stage ever flagged --
the plainly mechanical majority -- appeared in none of them. This consolidates
them and fills in that majority.

The unit is the AUTHORED FAMILY, not the concrete entry. Provenance is a
property of how a value was derived, and Concretize copies a family's values
unchanged into each of its per-type entries, so 25 concrete broadcast entries
share one derivation. Records are therefore keyed by the generic key -- the same
key the promotion log and both stage reports already use.

Each record:

    { "entry":      "mpi:mpi_bcast",
      "path":       "execution.launch",
      "tier":       "semantic_heuristic",   # from curated/field-provenance.json
      "state":      "populated" | "confirmed_null" | "no_candidate",
      "stage":      "extract" | "classify" | "assign" | "supplement" | "assemble",
      "method":     "mechanical" | "standard_passage" | "model_assisted",
      "confidence": "static" | "pattern" | "needs_approval",
      "approved":   true | false | null,
      "note":       "..." }

method is the three-way distinction WR1 asks for:
  mechanical       read off a signature, a type qualifier, or another field of
                   the same entry. No interpretation.
  standard_passage read out of the standard's or the vendor documentation's
                   prose (identity.desc, standard_refs, parameters[].desc).
  model_assisted   came from a curated input a model drafted -- the shape
                   catalog via an assignment, or the per-PPM supplement.

approved is true only where a review record says so. Every model_assisted value
starts unreviewed, so approved is false until a human sets a group's status in
curated/review/. Mechanical values carry null: there is no review gate on them
and pretending otherwise would inflate the approved count.

Run directly: python3 workflow/provenance/report.py [--summary]
"""

import argparse
import datetime
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_LAYOUT_COMMON = os.path.join(_HERE, "..", "common")
sys.path.insert(0, _LAYOUT_COMMON)
sys.path.insert(0, os.path.join(_HERE, "..", "staging"))
from layout import CURATED_DIR, FIELD_PROVENANCE_PATH, OUT_DIR, REVIEW_DIR, ROOT  # noqa: E402
from paths import ABSENT, get_path  # noqa: E402
from derive_schema import _governing_tier, _tier_for  # noqa: E402

_MERGED_IN = os.path.join(OUT_DIR, "3_syntactic-semantics-formal-supplement-api.json")
_FINAL_IN = os.path.join(OUT_DIR, "4_final-api.json")
_EXTRACT_REPORT = os.path.join(OUT_DIR, "extract-report.json")
_CLASSIFY_REPORT = os.path.join(OUT_DIR, "classify-report.json")
_FORMAL_REVIEW = os.path.join(REVIEW_DIR, "formal-assignments.review.json")
_SUPPLEMENT_REVIEW = os.path.join(REVIEW_DIR, "supplement.review.json")
_OUT = os.path.join(OUT_DIR, "provenance-report.json")

# Fields Extract reads out of prose rather than off a declaration. Everything
# else Extract produces comes from a signature, a macro, or a type qualifier.
# Kept as an explicit list rather than inferred from a flag's wording: the
# distinction is a property of the field, not of whether that particular value
# happened to get flagged.
_PROSE_FIELDS = {
    "identity.desc",
    "identity.standard_refs",
    "identity.since",
    "identity.deprecated_in",
    "parameters[].desc",
}

# tier -> the stage that owns a value nothing else claims, and how it got there.
_TIER_DEFAULT = {
    "syntactic": ("extract", "mechanical", "static"),
    "derived": ("extract", "mechanical", "static"),
    "semantic_heuristic": ("classify", "mechanical", "pattern"),
    "semantic": ("extract", "mechanical", "static"),
    "formal": ("assign", "model_assisted", "needs_approval"),
}


def _load(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path) as f:
        return json.load(f)


def _generic_path(path):
    """A corpus path in field-provenance.json's notation. Two forms collapse
    onto the empty-bracket one: the list index the walk produces
    ('parameters.3.binding_type.c') and the by-name selector the promotion log
    uses ('parameters[comm].constraints.paired_with', see common/paths.py)."""
    path = re.sub(r"\.\d+(?=\.|$)", "[]", path)
    return re.sub(r"\[[^\]]+\]", "[]", path)


def _populated_paths(node, provenance_fields, prefix=""):
    """Every populated value under `node`, as (path, generic_path, tier).

    `path` addresses one specific value and is what a record reports; it uses
    the by-name selector common/paths.py defines, so the two parameters of a
    call are "parameters[buf].kind" and "parameters[count].kind" rather than
    two records that both read "parameters[].kind". `generic_path` is the
    empty-bracket form field-provenance.json uses, and is what the tier lookup
    resolves against. The promotion log already writes the by-name form, so the
    two sources join on `path` without translation.

    The recursion stops wherever curated/field-provenance.json names the path
    -- exactly ("semantics.formal") or through a wildcard one level up
    ("bindings.*" naming "bindings.c"). That table is this project's own
    statement of what one unit of derivation is, so descending past it would
    invent a finer granularity than any stage actually works at: a shape
    assignment produces a whole semantics.formal block, not each of its
    data_flow nodes independently.

    A null yields nothing. The shipped corpus is exhaustively null-filled, so a
    record per null would be one per field per entry, saying nothing about any
    of them; the nulls that are a *considered* answer are in the promotion log,
    and run() records those separately. An empty list or object is skipped for
    the same reason: an answer, but not a value.
    """
    generic = _generic_path(prefix)
    tier = _tier_for(generic, provenance_fields) if generic else None
    if tier is not None:
        if node is None or (isinstance(node, (list, dict)) and not node):
            return
        yield prefix, generic, tier
        return

    if isinstance(node, dict):
        for key, value in node.items():
            yield from _populated_paths(
                value, provenance_fields, f"{prefix}.{key}" if prefix else key)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            # A named element is addressed by its name, an anonymous one by
            # index -- the same rule common/paths.py's get_path resolves by.
            label = item["name"] if isinstance(item, dict) and item.get("name") else i
            yield from _populated_paths(item, provenance_fields, f"{prefix}[{label}]")
    elif node is not None:
        # No provenance entry covers this path. A real gap in the table rather
        # than something to paper over: reported with tier null so it shows up
        # in the summary's by_tier tally.
        yield prefix, generic, None


def _index_flags(report):
    """(entry_key, field) -> reason, for the flags that name a field. A field
    flagged more than once keeps the first reason; the reports do not currently
    produce duplicates, and joining them would only make the note unreadable."""
    index = {}
    for flag in (report or {}).get("flags") or []:
        field = flag.get("field")
        if not field:
            continue
        index.setdefault((flag.get("entry_key"), field), flag.get("reason"))
    return index


def _index_review(review, key_of):
    """(entry_key, field) -> approved, from a review record's groups. `key_of`
    says how a group's members map onto a field path, which is the one thing
    the two review records differ on: the formal record groups by outcome and
    is implicitly about semantics.formal, the supplement record carries an
    explicit field_path."""
    index = {}
    for group in (review or {}).get("groups") or []:
        approved = group.get("status") == "approved"
        for member in group.get("members") or []:
            index[key_of(group, member)] = approved
    return index


def _classify_record(entry_key, path, generic, tier, extract_flags, classify_flags):
    """Which stage put a merge-untouched value where it is, how, and with what
    confidence. The stage reports flag by field path, so a flag is checked
    before falling back to the tier's default -- a value Classify flagged is a
    heuristic result whatever tier the field nominally sits in."""
    reason = classify_flags.get((entry_key, path)) or classify_flags.get((entry_key, generic))
    if reason is not None:
        return "classify", "mechanical", "pattern", reason

    method = "standard_passage" if generic in _PROSE_FIELDS else "mechanical"
    reason = extract_flags.get((entry_key, path)) or extract_flags.get((entry_key, generic))
    if reason is not None:
        return "extract", method, "static", reason

    stage, default_method, confidence = _TIER_DEFAULT.get(
        tier, ("extract", "mechanical", "static"))
    return stage, method if generic in _PROSE_FIELDS else default_method, confidence, None


def build(entries, final, provenance_fields, extract_report, classify_report,
          formal_review, supplement_review):
    extract_flags = _index_flags(extract_report)
    classify_flags = _index_flags(classify_report)

    formal_approved = _index_review(
        formal_review, lambda g, m: (m, "semantics.formal"))
    supplement_approved = _index_review(
        supplement_review, lambda g, m: (m, g.get("field_path")))

    # The supplement is authored per PPM against the full API surface, so a
    # build that covers only some models -- or one whose supplement names a
    # function the extractor never produced -- logs records for entries that
    # are not in this corpus. They are a fact about the supplement, not
    # provenance for any shipped value, so they are counted and dropped rather
    # than written as records for entries a reader cannot look up.
    applied, non_applied, absent = [], [], []
    for record in (final or {}).get("promotion_log") or []:
        if record.get("entry_key") not in entries:
            absent.append(record)
        elif record.get("status") == "applied":
            applied.append(record)
        else:
            non_applied.append(record)

    records = []
    covered = set()

    def emit(entry_key, path, tier, state, stage, method, confidence, approved, note):
        covered.add((entry_key, path))
        record = {
            "entry": entry_key,
            "path": path,
            "tier": tier,
            "state": state,
            "stage": stage,
            "method": method,
            "confidence": confidence,
            "approved": approved,
        }
        if note:
            record["note"] = note
        records.append(record)

    # Pass 1: the promotion log, which is the authority for every field the
    # merge touched. It has to come first because a value it applied can be a
    # deliberate null -- the supplement asserting that a call is not atomic, say
    # -- and the corpus walk below cannot see those: a null in the entry is
    # indistinguishable from a null the final null-fill put there.
    _STATE = {"confirmed_null": "confirmed_null",
              "no_candidate": "no_candidate",
              "supplement_ineligible": "no_candidate"}
    # The merge addresses whole containers as one field ("semantics.collective"),
    # which field-provenance.json only ever names through a wildcard one level
    # down ("semantics.collective.*"). _governing_tier resolves that case;
    # _tier_for alone would report those as uncovered.
    def tier_of(path):
        return _governing_tier(_generic_path(path), provenance_fields)

    for record in non_applied:
        entry_key, path = record.get("entry_key"), record.get("field") or ""
        tier = tier_of(path)
        stage, method, confidence = _TIER_DEFAULT.get(
            tier, ("extract", "mechanical", "static"))
        emit(entry_key, path, tier, _STATE.get(record.get("status"), "no_candidate"),
             stage, method, confidence, None,
             record.get("reason") or record.get("note"))

    for record in applied:
        entry_key, path = record.get("entry_key"), record.get("field") or ""
        tier = tier_of(path)
        value = get_path(entries.get(entry_key) or {}, path)
        state = "confirmed_null" if value is None or value is ABSENT else "populated"
        if record.get("derived_by") == "assemble":
            # Derived during the merge from other fields of the same entry
            # (workflow/assemble/array_shape.py): a rule, not a curated input.
            emit(entry_key, path, tier, state, "assemble", "mechanical", "pattern", None,
                 record.get("note"))
        elif record.get("shape_ref"):
            emit(entry_key, path, tier, state, "assign", "model_assisted",
                 "needs_approval", formal_approved.get((entry_key, "semantics.formal")),
                 f"shape {record['shape_ref']}")
        else:
            # The supplement review records field_path in the same by-name form
            # the promotion log uses, so `path` is the key that hits; the
            # empty-bracket form is a fallback for any group written the other way.
            approved = supplement_approved.get((entry_key, path))
            if approved is None:
                approved = supplement_approved.get((entry_key, _generic_path(path)))
            emit(entry_key, path, tier, state, "supplement", "model_assisted",
                 "needs_approval", approved,
                 record.get("note") or record.get("reason"))

    # Pass 2: everything the merge never touched -- the mechanical majority,
    # which appears in no log and is exactly what made the three per-stage
    # reports insufficient on their own.
    for entry_key in sorted(entries):
        for path, generic, tier in _populated_paths(entries[entry_key], provenance_fields):
            if (entry_key, path) in covered:
                continue
            stage, method, confidence, note = _classify_record(
                entry_key, path, generic, tier, extract_flags, classify_flags)
            emit(entry_key, path, tier, "populated", stage, method, confidence, None, note)

    records.sort(key=lambda r: (r["entry"], r["path"], r["state"]))
    return records, sorted({r.get("entry_key") for r in absent})


def _summarize(records, absent_entries):
    def tally(key):
        counts = {}
        for record in records:
            counts[record.get(key)] = counts.get(record.get(key), 0) + 1
        return {str(k): v for k, v in sorted(counts.items(), key=lambda kv: -kv[1])}

    reviewable = [r for r in records if r["approved"] is not None]
    return {
        "records": len(records),
        "families": len({r["entry"] for r in records}),
        "by_state": tally("state"),
        "by_stage": tally("stage"),
        "by_method": tally("method"),
        "by_tier": tally("tier"),
        "values_needing_approval": len(reviewable),
        "values_approved": sum(1 for r in reviewable if r["approved"]),
        "supplement_entries_not_in_corpus": len(absent_entries),
    }


def run(print_summary=False):
    entries = _load(_MERGED_IN)
    if entries is None:
        raise SystemExit(f"{_MERGED_IN} not found -- run the assemble stage first")
    final = _load(_FINAL_IN, {})
    provenance_fields = _load(FIELD_PROVENANCE_PATH)["fields"]

    records, absent_entries = build(
        entries=entries,
        final=final,
        provenance_fields=provenance_fields,
        extract_report=_load(_EXTRACT_REPORT, {}),
        classify_report=_load(_CLASSIFY_REPORT, {}),
        formal_review=_load(_FORMAL_REVIEW, {}),
        supplement_review=_load(_SUPPLEMENT_REVIEW, {}),
    )
    summary = _summarize(records, absent_entries)

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(_OUT, "w") as f:
        json.dump({
            "generated_at": datetime.datetime.now(datetime.timezone.utc)
                                     .replace(microsecond=0).isoformat(),
            "note": ("One record per value in the corpus: which stage produced it, how, and "
                     "whether a human has approved it. Keyed by authored family (the generic "
                     "key), since Concretize copies a family's values unchanged into each of "
                     "its per-type entries. Sources: extract-report.json, classify-report.json, "
                     "4_final-api.json's promotion_log, curated/field-provenance.json, and the "
                     "review records in curated/review/."),
            # Relative to the repository: the report is published, and an absolute
            # path would record the builder's home directory, not anything about
            # the corpus.
            "curated_dir": os.path.relpath(CURATED_DIR, ROOT),
            "summary": summary,
            "supplement_entries_not_in_corpus": absent_entries,
            "records": records,
        }, f, indent=2, sort_keys=True)
        f.write("\n")

    print(f"wrote {len(records)} provenance records for {summary['families']} families "
          f"to {_OUT}")
    if absent_entries:
        print(f"  {len(absent_entries)} supplement entr"
              f"{'y is' if len(absent_entries) == 1 else 'ies are'} not in this corpus "
              f"(listed, not recorded)")
    if print_summary:
        print(json.dumps(summary, indent=2))
    else:
        print(f"  by method: {summary['by_method']}")
        print(f"  approved:  {summary['values_approved']}/{summary['values_needing_approval']} "
              f"model-assisted values")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="workflow/provenance/report.py",
        description="Consolidate every stage's derivation record into one provenance report.")
    p.add_argument("--summary", action="store_true",
                   help="print the full per-stage/per-method/per-tier tally")
    args = p.parse_args(argv)
    return run(print_summary=args.summary)


if __name__ == "__main__":
    sys.exit(main())
