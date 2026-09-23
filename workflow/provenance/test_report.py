"""
Coverage and vocabulary check for the provenance report.

WR1 is a claim about completeness: *every* value records how it was derived and
whether a human has approved it. A report that silently omits a field still
looks fine -- it is smaller, and nothing about it is wrong. So the checks here
are about what must be present rather than about what is:

  1. every promotion-log record for an entry in this corpus has a record --
     the merge is the one source that knows about deliberate nulls, which the
     corpus walk cannot see
  2. no (entry, path) is recorded twice, so a reader never has two answers to
     "where did this come from"
  3. every record uses the closed vocabularies, and every path resolves to a
     tier in curated/field-provenance.json -- an unresolved tier means the
     provenance table has a gap, which is a finding, not a shrug
  4. approved is non-null exactly for the model-assisted values, since those
     are the only ones with a review gate

Plus one unit check of the path normalization, which is the piece most likely
to break silently: the walk emits parameters[buf].kind and the promotion log
writes the same, and both have to fold onto field-provenance's
parameters[].kind for the tier lookup while staying distinct as records.

Runs against whatever is in instances/; a missing report is a skip.

Run directly: python3 workflow/provenance/test_report.py
"""

import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, "..", "common"))
sys.path.insert(0, os.path.join(_HERE, "..", "staging"))
from layout import FIELD_PROVENANCE_PATH, OUT_DIR  # noqa: E402
from report import _generic_path  # noqa: E402
from derive_schema import _governing_tier  # noqa: E402

_REPORT = os.path.join(OUT_DIR, "provenance-report.json")
_FINAL = os.path.join(OUT_DIR, "4_final-api.json")

_STATES = {"populated", "confirmed_null", "no_candidate"}
_STAGES = {"extract", "classify", "assign", "supplement", "assemble"}
_METHODS = {"mechanical", "standard_passage", "model_assisted"}
_CONFIDENCES = {"static", "pattern", "needs_approval"}


def _load(path):
    with open(path) as f:
        return json.load(f)


def _check_path_normalization():
    cases = [
        ("parameters[buf].kind", "parameters[].kind"),
        ("parameters[0].binding_type.c", "parameters[].binding_type.c"),
        ("parameters.3.name", "parameters[].name"),
        ("semantics.formal", "semantics.formal"),
        ("bindings.c", "bindings.c"),
    ]
    return [f"_generic_path({raw!r}) -> {_generic_path(raw)!r}, expected {want!r}"
            for raw, want in cases if _generic_path(raw) != want]


def run():
    failures = _check_path_normalization()
    checked = 0

    if not os.path.exists(_REPORT):
        print(f"skipped the corpus checks: {_REPORT} not on disk")
    else:
        report = _load(_REPORT)
        records = report["records"]
        checked = len(records)
        provenance_fields = _load(FIELD_PROVENANCE_PATH)["fields"]

        seen = set()
        for record in records:
            key = (record["entry"], record["path"])
            if key in seen:
                failures.append(f"{record['entry']} {record['path']}: recorded more than once")
            seen.add(key)

            for field, vocabulary in (("state", _STATES), ("stage", _STAGES),
                                      ("method", _METHODS), ("confidence", _CONFIDENCES)):
                if record.get(field) not in vocabulary:
                    failures.append(f"{record['entry']} {record['path']}: "
                                    f"{field}={record.get(field)!r} is outside the vocabulary")

            if record.get("tier") is None:
                failures.append(f"{record['entry']} {record['path']}: no tier -- "
                                f"curated/field-provenance.json does not cover this path")
            elif _governing_tier(_generic_path(record["path"]), provenance_fields) != record["tier"]:
                failures.append(f"{record['entry']} {record['path']}: tier={record['tier']!r} "
                                f"disagrees with field-provenance.json")

            model_assisted = record.get("method") == "model_assisted"
            if model_assisted and record.get("confidence") != "needs_approval":
                failures.append(f"{record['entry']} {record['path']}: model-assisted but "
                                f"confidence={record.get('confidence')!r}")
            if not model_assisted and record.get("approved") is not None:
                failures.append(f"{record['entry']} {record['path']}: approved is set on a "
                                f"{record.get('method')} value, which has no review gate")

        if os.path.exists(_FINAL):
            final = _load(_FINAL)
            absent = set(report.get("supplement_entries_not_in_corpus") or [])
            for record in final.get("promotion_log") or []:
                if record.get("entry_key") in absent:
                    continue
                if (record.get("entry_key"), record.get("field")) not in seen:
                    failures.append(f"{record.get('entry_key')} {record.get('field')}: in the "
                                    f"promotion log but absent from the provenance report")

    print(f"{checked} provenance record(s) checked.")
    if failures:
        print(f"\n{len(failures)} FAILURE(S):")
        for f in failures[:20]:
            print(f"  - {f}")
        if len(failures) > 20:
            print(f"  ... and {len(failures) - 20} more")
        return 1

    print("Every value is accounted for, once, in the closed vocabulary.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
