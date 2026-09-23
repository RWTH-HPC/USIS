"""
Extract's driver: runs every PPM adapter, assembles every function into a
full R1-compliant entry via emit.assemble_entry, validates each against
the post-extract staging schema, and writes:

  instances/0_syntactic-api.json  -- the corpus, keyed "model:function_key"
  instances/extract-report.json -- the run's status.Report (skipped/
                                     low_confidence/note flags), a side
                                     channel a human triages instead of
                                     reading the full corpus (see
                                     status.py's module docstring for the
                                     gap this addresses)

This is Extract's whole job per the interface contract (docs/workflow/
workflow/README.md): produce 0_syntactic-api.json, structured
identically to api-schema.json's entry shape, every non-syntactic/derived
field explicitly null, semantics.formal always null. Generate Formal
and Classify Semantics read this output next -- neither is this
script's concern.

Run directly: python3 workflow/extract/cli.py
"""

import datetime
import json
import os
import sys

_HERE = os.path.dirname(__file__)
sys.path.insert(0, _HERE)
# Each PPM subpackage's adapter.py needs its own sibling modules (mpi's
# "signature"/"prose", shmem's "type_tables", nvshmem's "macro_expand")
# importable by bare name -- but all 4 directories can't be on sys.path
# simultaneously when loading them by the literal name "adapter", or
# Python's import resolution just returns whichever was inserted last for
# every "import adapter" statement (found the hard way: the first attempt
# at this file bound all 4 adapter names to the same, wrong module). Load
# each by explicit file path instead, one sys.path entry active at a time.
import importlib.util  # noqa: E402


def _load_adapter(subpackage, module_name):
    subdir = os.path.join(_HERE, subpackage)
    sys.path.insert(0, subdir)
    try:
        spec = importlib.util.spec_from_file_location(f"_extract_{subpackage}_{module_name}", os.path.join(subdir, f"{module_name}.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(subdir)


from emit import assemble_entry  # noqa: E402
from validate_entry import validate_entry, ValidationError  # noqa: E402
from status import Report, Flag  # noqa: E402
from ir import Confident  # noqa: E402

_LAYOUT_COMMON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common")
sys.path.insert(0, _LAYOUT_COMMON)
sys.path.insert(0, os.path.join(_LAYOUT_COMMON, "..", "staging"))
from derive_schema import staging_schema_for  # noqa: E402
from layout import MODELS, OUT_DIR  # noqa: E402

mpi_adapter = _load_adapter("mpi", "adapter")
mpi_prose = _load_adapter("mpi", "prose")
shmem_adapter = _load_adapter("shmem", "adapter")
nccl_adapter = _load_adapter("nccl", "adapter")
nvshmem_adapter = _load_adapter("nvshmem", "adapter")
openmp_adapter = _load_adapter("openmp", "adapter")
cuda_adapter = _load_adapter("cuda", "adapter")

_ROOT = os.path.join(_HERE, "..", "..")
_STAGING_SCHEMA_STAGE = "post-extract"
_OUT_DIR = OUT_DIR
_ENTRIES_OUT = os.path.join(_OUT_DIR, "0_syntactic-api.json")
_REPORT_OUT = os.path.join(_OUT_DIR, "extract-report.json")


def _jsonable(value):
    if isinstance(value, Confident):
        return {"__confident__": True, "value": value.value, "confidence": value.confidence, "note": value.note}
    return value


def run():
    staging_schema = staging_schema_for(_STAGING_SCHEMA_STAGE)

    report = Report()
    entries = {}

    adapters = [
        ("mpi", lambda: mpi_adapter.extract_mpi(prose_index=mpi_prose.build_prose_index())),
        ("shmem", shmem_adapter.extract_shmem),
        ("nccl", nccl_adapter.extract_nccl),
        ("nvshmem", nvshmem_adapter.extract_nvshmem),
        ("openmp", openmp_adapter.extract_openmp),
        ("cuda", cuda_adapter.extract_cuda),
    ]

    # Extract is the only stage that reads the model selection: it is the only
    # one that goes to external-inputs/ per model. Every later stage takes
    # whatever families are in the checkpoint it is handed, so a --ppm build
    # needs no change downstream. A deselected model is absent from ppm_counts
    # rather than present as 0, so a report never claims an adapter ran and
    # found nothing.
    adapters = [(model, fn) for model, fn in adapters if model in set(MODELS)]

    for model, run_adapter in adapters:
        results = run_adapter()
        report.ppm_counts[model] = len(results)

        for ir, _adapter_flags in results:
            # assemble_entry's own returned flags already fold in
            # ir["flags"] (see emit.py: `flags.extend(ir.get("flags")
            # or [])`), which is the same list object as _adapter_flags
            # here -- report only assemble_entry's return, not both, or
            # every adapter-level flag gets double-counted.
            entry_key = f"{ir['model']}:{ir['function_key']}"
            try:
                entry, flags = assemble_entry(ir)
            except ValueError as e:
                report.add(Flag(entry_key=entry_key, field=None, severity="skipped", reason=f"assemble_entry failed: {e}"))
                continue

            try:
                validate_entry(entry, staging_schema)
            except ValidationError as e:
                report.add(Flag(entry_key=entry_key, field=None, severity="skipped",
                                 reason=f"assembled entry fails staging-schema validation: {e}"))
                continue

            entries[entry_key] = entry
            report.extend(flags)

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
