"""
Fidelity check for the per-model split.

The split's whole claim is that it is a pure filter: a per-model file is the
corresponding slice of the corpus file and nothing else. That claim is what
lets the paper describe the shipped artifacts as the corpus partitioned rather
than as four separately-produced documents, and it is exactly the kind of
claim a refactor can quietly break -- a recomputed summary, a promotion-log
record filed under the wrong model, an entry silently dropped.

So the checks are conservation properties, not golden files:

  1. every entry of the corpus is in exactly one per-model file, byte-identical
  2. every per-model file holds only its own model, agreeing with identity.model
  3. the sliced logs partition the corpus's logs the same way
  4. each file declares the schema version the corpus was validated against
  5. recomputed summaries add up to the corpus's own

Runs against whatever is in instances/ -- it is a check on the artifacts a
build just produced, so a missing corpus is a skip, not a failure.

Run directly: python3 workflow/split/test_by_model.py
"""

import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, "..", "common"))
from layout import OUT_DIR  # noqa: E402
from by_model import _model_of, _schema_version  # noqa: E402

_FINAL = os.path.join(OUT_DIR, "4_final-api.json")


def _load(path):
    with open(path) as f:
        return json.load(f)


def run():
    if not os.path.exists(_FINAL):
        print(f"skipped: {_FINAL} not on disk -- nothing to check")
        return 0

    corpus = _load(_FINAL)
    models = sorted({_model_of(k) for k in corpus["entries"]})
    failures = []

    missing = [m for m in models
               if not os.path.exists(os.path.join(OUT_DIR, f"final-{m}-api.json"))]
    if missing:
        print(f"skipped: no per-model file for {', '.join(missing)} -- "
              f"run workflow/split/by_model.py first")
        return 0

    seen_entries = {}
    totals = {"entries": 0, "valid": 0, "failed": 0, "promotion": 0}
    expected_version = _schema_version()

    for model in models:
        sliced = _load(os.path.join(OUT_DIR, f"final-{model}-api.json"))

        if sliced.get("schema_version") != expected_version:
            failures.append(f"{model}: schema_version is {sliced.get('schema_version')!r}, "
                            f"expected {expected_version!r}")

        for key, entry in sliced["entries"].items():
            if _model_of(key) != model:
                failures.append(f"{model}: holds {key!r}, which is another model's entry")
            elif (entry.get("identity") or {}).get("model") != model:
                failures.append(f"{model}: {key} has identity.model="
                                f"{(entry.get('identity') or {}).get('model')!r}")
            if key in seen_entries:
                failures.append(f"{key} appears in both {seen_entries[key]} and {model}")
            seen_entries[key] = model
            if entry != corpus["entries"].get(key):
                failures.append(f"{model}: {key} differs from the corpus entry -- "
                                f"the split is supposed to be a pure filter")

        summary = sliced.get("summary") or {}
        if summary.get("total_concrete_entries_after_concretize") != len(sliced["entries"]):
            failures.append(f"{model}: summary entry count disagrees with the entries it holds")
        if summary.get("model") != model:
            failures.append(f"{model}: summary.model is {summary.get('model')!r}")

        totals["entries"] += len(sliced["entries"])
        totals["valid"] += summary.get("entries_valid_against_strict_schema", 0)
        totals["failed"] += summary.get("entries_failed_validation", 0)
        totals["promotion"] += len(sliced.get("promotion_log") or [])

        for name in ("validation_errors", "unfillable_required_fields"):
            stray = [k for k in (sliced.get(name) or {}) if _model_of(k) != model]
            if stray:
                failures.append(f"{model}: {name} holds {len(stray)} other-model key(s), "
                                f"e.g. {stray[0]}")

    if set(seen_entries) != set(corpus["entries"]):
        lost = sorted(set(corpus["entries"]) - set(seen_entries))
        failures.append(f"{len(lost)} corpus entr{'y' if len(lost) == 1 else 'ies'} landed in no "
                        f"per-model file, e.g. {lost[0] if lost else ''}")

    if totals["entries"] != len(corpus["entries"]):
        failures.append(f"per-model entry counts sum to {totals['entries']}, "
                        f"corpus has {len(corpus['entries'])}")
    if totals["promotion"] != len(corpus.get("promotion_log") or []):
        failures.append(f"per-model promotion_log records sum to {totals['promotion']}, "
                        f"corpus has {len(corpus.get('promotion_log') or [])}")

    corpus_summary = corpus.get("summary") or {}
    if totals["valid"] != corpus_summary.get("entries_valid_against_strict_schema"):
        failures.append(f"per-model valid counts sum to {totals['valid']}, corpus reports "
                        f"{corpus_summary.get('entries_valid_against_strict_schema')}")
    if totals["failed"] != corpus_summary.get("entries_failed_validation"):
        failures.append(f"per-model failure counts sum to {totals['failed']}, corpus reports "
                        f"{corpus_summary.get('entries_failed_validation')}")

    print(f"{len(models)} model(s), {totals['entries']} entries checked against "
          f"{len(corpus['entries'])} in the corpus.")
    if failures:
        print(f"\n{len(failures)} FAILURE(S):")
        for f in failures[:20]:
            print(f"  - {f}")
        if len(failures) > 20:
            print(f"  ... and {len(failures) - 20} more")
        return 1

    print("The per-model files partition the corpus exactly.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
