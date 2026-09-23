"""
Heuristic Classification's driver: reads instances/0_syntactic-api.json
(Extract's output -- no dependency on Generate Formal, see docs/workflow/
workflow/README.md), runs each PPM's heuristic classifier,
assembles the result via emit.assemble_classified_entry, validates each
against the same staging schema Extract itself validates against (see that
module's own docstring for why re-using api-schema.staging.post-extract.json
rather than minting a stricter stage is deliberate, not an oversight), and
writes:

  instances/1_syntactic-semantics-api.json -- the corpus, same "model:function_key"
                                          keying as 0_syntactic-api.json, with
                                          only the 12 Heuristic-Classification-
                                          owned field paths ever overwritten
  instances/classify-report.json      -- the run's status.Report (low_confidence
                                          flags for every heuristic guess made,
                                          plus one whole-run note about AI-
                                          Assisted Classification not being
                                          built -- see emit.py's docstring for
                                          the flagging policy)

Run directly: python3 workflow/classify/cli.py
"""

import datetime
import json
import os
import sys

_HERE = os.path.dirname(__file__)
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, "mpi"))
sys.path.insert(0, os.path.join(_HERE, "shmem"))
sys.path.insert(0, os.path.join(_HERE, "nccl"))
sys.path.insert(0, os.path.join(_HERE, "nvshmem"))
sys.path.insert(0, os.path.join(_HERE, "openmp"))
sys.path.insert(0, os.path.join(_HERE, "cuda"))
sys.path.insert(0, os.path.join(_HERE, ".."))

from emit import assemble_classified_entry  # noqa: E402
from common.status import Report, Flag  # noqa: E402
from common.ir import Confident  # noqa: E402

from classify_mpi import classify_mpi  # noqa: E402
from classify_shmem import classify_shmem  # noqa: E402
from classify_nccl import classify_nccl  # noqa: E402
from classify_nvshmem import classify_nvshmem  # noqa: E402
from classify_openmp import classify_openmp  # noqa: E402
from classify_cuda import classify_cuda  # noqa: E402

# validate_entry.py lives in workflow/extract/ and is itself bare-named
# (would collide with this package's own emit.py/heuristics.py if that
# whole directory were added to sys.path -- see workflow/extract/cli.py's
# own docstring for the identical "adapter" collision it already hit once).
# Loaded by explicit file path instead, the same workaround.
import importlib.util  # noqa: E402

_LAYOUT_COMMON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common")
sys.path.insert(0, _LAYOUT_COMMON)
sys.path.insert(0, os.path.join(_LAYOUT_COMMON, "..", "staging"))
from derive_schema import staging_schema_for  # noqa: E402
from layout import ALL_MODELS, OUT_DIR  # noqa: E402

_spec = importlib.util.spec_from_file_location("_classify_validate_entry", os.path.join(_HERE, "..", "extract", "validate_entry.py"))
_validate_entry_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_validate_entry_mod)
validate_entry = _validate_entry_mod.validate_entry
ValidationError = _validate_entry_mod.ValidationError

_ROOT = os.path.join(_HERE, "..", "..")
# Deliberately the same staging schema Extract validates against, not a new
# "post-classify-semantics" stage -- see this module's docstring for why: Heuristic Classification's semantic_heuristic fields are populated
# *when a heuristic fires*, still legitimately null otherwise, so they must
# stay nullable at this stage exactly like they are coming out of Extract.
_STAGING_SCHEMA_STAGE = "post-extract"
_SYNTACTIC_PATH = os.path.join(OUT_DIR, "0_syntactic-api.json")
_OUT_DIR = OUT_DIR
_ENTRIES_OUT = os.path.join(_OUT_DIR, "1_syntactic-semantics-api.json")
_REPORT_OUT = os.path.join(_OUT_DIR, "classify-report.json")

_AI_ASSISTED_CLASSIFICATION_NOTE = (
    "AI-Assisted Classification (LLM-assisted classification of the 23 pure-semantic "
    "fields -- most of execution.*, semantics.collective/point_to_point/"
    "one_sided/memory, return.possible_errors/possible_successes, all of "
    "tool_integration.*, identity.type_family, relationships.superseded_by/"
    "identity.api_group) is not built as a stage here -- retired 2026-07-21 and "
    "folded into curated/supplement/supplement-<ppm>.json. See "
    "curated/README.md. "
    "This is a single whole-run note, not repeated per entry -- see emit.py's "
    "docstring for why."
)



def _jsonable(value):
    if isinstance(value, Confident):
        return {"__confident__": True, "value": value.value, "confidence": value.confidence, "note": value.note}
    return value


def run():
    staging_schema = staging_schema_for(_STAGING_SCHEMA_STAGE)
    with open(_SYNTACTIC_PATH) as f:
        syntactic = json.load(f)

    by_model = {model: {} for model in ALL_MODELS}
    for entry_key, entry in syntactic.items():
        model, function_key = entry_key.split(":", 1)
        by_model[model][function_key] = entry

    report = Report()
    entries = {}

    classifiers = [
        ("mpi", classify_mpi),
        ("shmem", classify_shmem),
        ("nccl", classify_nccl),
        ("nvshmem", classify_nvshmem),
        ("openmp", classify_openmp),
        ("cuda", classify_cuda),
    ]

    for model, classify_fn in classifiers:
        model_entries = by_model[model]
        results = classify_fn(model_entries)
        report.ppm_counts[model] = len(results)

        for ir, _ir_flags in results:
            function_key = ir["function_key"]
            entry_key = f"{model}:{function_key}"
            source_entry = model_entries[function_key]

            entry, flags = assemble_classified_entry(source_entry, ir)

            try:
                validate_entry(entry, staging_schema)
            except ValidationError as e:
                report.add(Flag(entry_key=entry_key, field=None, severity="skipped",
                                 reason=f"classified entry fails staging-schema validation: {e}"))
                continue

            entries[entry_key] = entry
            report.extend(flags)

    report.add(Flag(entry_key=None, field=None, severity="note", reason=_AI_ASSISTED_CLASSIFICATION_NOTE))

    os.makedirs(_OUT_DIR, exist_ok=True)

    entries_jsonable = json.loads(json.dumps(entries, default=_jsonable))
    with open(_ENTRIES_OUT, "w") as f:
        json.dump(entries_jsonable, f, indent=2, sort_keys=True)
        f.write("\n")

    report.write(_REPORT_OUT, datetime.datetime.now(datetime.timezone.utc).isoformat())

    summary = report.summary()
    print(f"wrote {len(entries)} entries to {_ENTRIES_OUT}")
    print(f"per-PPM counts: {report.ppm_counts}")
    print(f"report: {summary['entries_skipped']} skipped, "
          f"{summary['low_confidence_fields']} low-confidence fields, "
          f"{summary['notes']} notes -- see {_REPORT_OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(run())
