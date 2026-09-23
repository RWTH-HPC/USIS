"""
Per-model split -- the SOLE producer of instances/final-<ppm>-api.json.

Pure filter, no independent computation: reads the finished corpus artifacts and partitions
them by identity.model, unchanged. Runs LAST in the chain, after Validate and
Provenance:

    extract -> classify -> assign [curated] -> assemble -> validate ->
    provenance -> THIS SCRIPT

Why split at the end rather than running the chain once per model: exactly one
step in the workflow is corpus-wide rather than per-entry --
assemble.py's _derive_supersedes(), which populates relationships.supersedes by
inverting every entry's superseded_by across the whole corpus -- and two of the
curated inputs are deliberately single cross-PPM artifacts (the shape catalog
and the hand-corrected formal-assignments.json). Running the chain per model
would fragment those and change what _derive_supersedes sees. Splitting after
all of it is a filter, so a per-model file is byte-for-byte the corresponding
slice of the corpus file and the two can be diffed against each other.

What it writes, one per model present in the corpus:

    final-<ppm>-api.json        the shipped artifact. Same top-level shape as
                                4_final-api.json, with entries, validation_errors,
                                unfillable_required_fields and promotion_log
                                sliced to that model and summary recomputed,
                                plus a schema_version key (see below).
    provenance-<ppm>.json       the matching provenance report, if
                                instances/provenance-report.json exists.

and, under --split-intermediates, the generic checkpoints 0_-3_ as
<n>_...-<ppm>.json. Those are off by default: they are debugging aids, they
triple the output size, and nothing downstream reads a per-model checkpoint.

schema_version: the shipped document declares the format version it conforms
to, taken from the $id of curated/schemas/api-schema.json. It lives on the
document rather than on every entry because a consumer needs to know what it is
reading before it reads an entry, and 2893 copies of one string would be
redundant.

Every key in every one of these artifacts is model-qualified ("model:function_key"),
for concrete and generic keys alike, so the partition is a prefix split and
cannot disagree with itself between the entries and the logs that reference
them. identity.model is still what decides an entry's file; the prefix is
checked against it and a mismatch is an error rather than a silent
misfiling.

Run directly: python3 workflow/split/by_model.py [--split-intermediates]
"""

import argparse
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_LAYOUT_COMMON = os.path.join(_HERE, "..", "common")
sys.path.insert(0, _LAYOUT_COMMON)
from layout import OUT_DIR, SCHEMAS_DIR  # noqa: E402

_FINAL = "4_final-api.json"
_PROVENANCE = "provenance-report.json"
_API_SCHEMA = os.path.join(SCHEMAS_DIR, "api-schema.json")

# Plain {entry_key: entry} dicts. Split by key prefix, nothing else to slice.
_GENERIC_CHECKPOINTS = [
    "0_syntactic-api.json",
    "1_syntactic-semantics-api.json",
    "2_syntactic-semantics-formal-api.json",
    "3_syntactic-semantics-formal-supplement-api.json",
]

# Which top-level keys of 4_final-api.json are per-entry collections that have
# to be sliced, and which are whole-corpus scalars that every slice inherits
# unchanged. summary is neither -- it is recomputed.
_SLICED_DICTS = ["entries", "validation_errors", "unfillable_required_fields"]
_COPIED = ["generated_at", "review_status"]


def _load(path):
    with open(path) as f:
        return json.load(f)


def _write(name, obj):
    path = os.path.join(OUT_DIR, name)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write("\n")
    return path


def _model_of(entry_key):
    return entry_key.split(":", 1)[0]


def _schema_version():
    """The version the corpus was validated against, read out of the schema's
    own $id, which points at the file under its release tag:
    '.../RWTH-HPC/USIS/v0.1.0/curated/schemas/api-schema.json' -> 'v0.1.0'.
    Not split on '.', since the version itself contains one."""
    schema_id = _load(_API_SCHEMA).get("$id", "")
    match = re.search(r"/(v\d+(?:\.\d+)*)/", schema_id)
    if match:
        return match.group(1)
    # Fall back to the whole $id rather than inventing a version: a consumer can
    # still resolve it, and a wrong-looking value is better than a plausible one.
    return schema_id or None


def _check_prefixes(entries):
    """identity.model is what assigns an entry to a file; the key prefix is what
    the promotion log and the validation errors are keyed by. They are supposed
    to be the same string. If they ever aren't, entries and their log records
    would land in different files, so fail loudly instead."""
    bad = [k for k, e in entries.items()
           if (e.get("identity") or {}).get("model") != _model_of(k)]
    if bad:
        raise SystemExit(
            f"{len(bad)} entr{'y' if len(bad) == 1 else 'ies'} disagree with their own key "
            f"prefix about identity.model, e.g. {bad[0]!r}")


def _split_final(corpus, schema_version):
    _check_prefixes(corpus["entries"])
    models = sorted({_model_of(k) for k in corpus["entries"]})

    written = {}
    for model in models:
        keep = lambda k, m=model: _model_of(k) == m  # noqa: E731

        sliced = {name: {k: v for k, v in (corpus.get(name) or {}).items() if keep(k)}
                  for name in _SLICED_DICTS}
        promotion_log = [p for p in (corpus.get("promotion_log") or [])
                         if keep(p.get("entry_key", ""))]

        def _count(status):
            return sum(1 for p in promotion_log if p.get("status") == status)

        # Families, not entries: the promotion log is keyed by the generic key,
        # so its distinct keys are the authored families this model contributed.
        # Counting concrete entries instead would report the post-Concretize
        # number under a name that means the pre-Concretize one.
        families = {p["entry_key"] for p in promotion_log if "entry_key" in p}

        out = {
            "schema_version": schema_version,
            "note": (f"The {model} slice of the unified API specification, split from "
                     f"{_FINAL} by workflow/split/by_model.py. Entry keys are "
                     f"model-qualified, so references into another model's file resolve "
                     f"unchanged."),
            "summary": {
                "model": model,
                "total_function_families": len(families),
                "total_concrete_entries_after_concretize": len(sliced["entries"]),
                "entries_valid_against_strict_schema":
                    len(sliced["entries"]) - len(sliced["validation_errors"]),
                "entries_failed_validation": len(sliced["validation_errors"]),
                "entries_with_unfillable_required_fields": len(sliced["unfillable_required_fields"]),
                "fields_applied": _count("applied"),
                "fields_no_candidate": _count("no_candidate"),
                "fields_skipped_conflict": _count("skipped_conflict"),
                "formal_confirmed_null": _count("confirmed_null"),
            },
            "promotion_log": promotion_log,
            **sliced,
        }
        for name in _COPIED:
            if name in corpus:
                out[name] = corpus[name]

        _write(f"final-{model}-api.json", out)
        written[model] = len(sliced["entries"])
    return written


def _split_provenance(schema_version):
    path = os.path.join(OUT_DIR, _PROVENANCE)
    if not os.path.exists(path):
        return {}
    report = _load(path)
    records = report.get("records") or []
    models = sorted({_model_of(r.get("entry", "")) for r in records})

    written = {}
    for model in models:
        mine = [r for r in records if _model_of(r.get("entry", "")) == model]
        counts = {}
        for r in mine:
            counts[r.get("method")] = counts.get(r.get("method"), 0) + 1
        _write(f"provenance-{model}.json", {
            "schema_version": schema_version,
            "note": (f"The {model} slice of {_PROVENANCE}, split by "
                     f"workflow/split/by_model.py. One record per populated field of "
                     f"final-{model}-api.json."),
            "generated_at": report.get("generated_at"),
            "summary": {"model": model, "records": len(mine), "by_method": counts},
            "records": mine,
        })
        written[model] = len(mine)
    return written


def _split_checkpoints():
    written = {}
    for name in _GENERIC_CHECKPOINTS:
        path = os.path.join(OUT_DIR, name)
        if not os.path.exists(path):
            continue
        entries = _load(path)
        stem, ext = os.path.splitext(name)
        for model in sorted({_model_of(k) for k in entries}):
            subset = {k: v for k, v in entries.items() if _model_of(k) == model}
            _write(f"{stem}-{model}{ext}", subset)
            written[model] = written.get(model, 0) + len(subset)
    return written


def run(split_intermediates=False):
    final_path = os.path.join(OUT_DIR, _FINAL)
    if not os.path.exists(final_path):
        raise SystemExit(f"{final_path} not found -- run the assemble stage first")

    schema_version = _schema_version()
    corpus = _load(final_path)

    entry_counts = _split_final(corpus, schema_version)
    total = sum(entry_counts.values())
    if total != len(corpus["entries"]):
        raise SystemExit(f"split lost entries: {total} across the per-model files vs "
                         f"{len(corpus['entries'])} in {_FINAL}")

    print(f"split {total} entries from {_FINAL} into {len(entry_counts)} per-model file(s) "
          f"in {OUT_DIR}  [schema {schema_version}]")
    for model, n in sorted(entry_counts.items(), key=lambda kv: -kv[1]):
        print(f"  final-{model}-api.json: {n} entries")

    prov = _split_provenance(schema_version)
    if prov:
        print(f"split {sum(prov.values())} provenance records into "
              f"{len(prov)} per-model file(s)")
    else:
        print(f"no {_PROVENANCE} on disk -- skipped the provenance split")

    if split_intermediates:
        checkpoints = _split_checkpoints()
        print(f"split the generic checkpoints too: {sum(checkpoints.values())} entries "
              f"across {len(checkpoints)} model(s)")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="workflow/split/by_model.py",
        description="Partition the finished corpus into one shipped JSON document per PPM.")
    p.add_argument("--split-intermediates", action="store_true",
                   help="also partition the generic checkpoints 0_-3_ (debugging aid; "
                        "nothing downstream reads them)")
    args = p.parse_args(argv)
    return run(split_intermediates=args.split_intermediates)


if __name__ == "__main__":
    sys.exit(main())
