"""
Self-contained golden-example test harness for Extract, mirroring
workflow/formal/test_shapes.py's pattern (no pytest, no jsonschema package
-- see workflow/formal/validate.py's docstring for why neither is
available in this environment): re-run every adapter, pick out 3 real
functions per PPM chosen to exercise real structural variety
rather than only the easy path, and check:

  1. the assembled entry validates against instances/api-schema.staging.post-extract.json
     (the actual proof the interface contract in docs/workflow/
     workflow/README.md is met, not just internal
     self-consistency);
  2. every field outside what Extract owns (curated/field-provenance.json's
     "syntactic"/"derived" tiers) is ABSENT, not null (enforces requirement
     #2 of that contract for every case at once -- see
     docs/overview/glossary.md (Staging schema) for why
     omission, not null-padding, is the contract now);
  3. semantics.formal is entirely absent unconditionally (requirement #3);
  4. the entry (which, by (2), already only contains what Extract owns)
     matches a checked-in golden value byte-for-byte
     (workflow/extract/golden_entries.json) -- this is what catches a
     future adapter change silently altering real output, the same
     "golden-diff" role workflow/formal/testdata/expansions.json plays for Generate Formal.

Golden values were captured from this adapter code's own real output
against the real external-inputs/ sources (grounded, not synthetic -- the
same choice as Generate Formal's pinned expansions) and spot-checked by hand before being committed -- see this
session's approved plan for the per-function sanity checks performed.

Run directly: python3 workflow/extract/test_emit.py
"""

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

from emit import assemble_entry  # noqa: E402
from validate_entry import validate_entry, ValidationError  # noqa: E402
from ir import Confident  # noqa: E402

_LAYOUT_COMMON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common")
sys.path.insert(0, _LAYOUT_COMMON)
sys.path.insert(0, os.path.join(_LAYOUT_COMMON, "..", "staging"))
from derive_schema import staging_schema_for  # noqa: E402
from layout import ALL_MODELS, MODELS  # noqa: E402


_ROOT = os.path.join(_HERE, "..", "..")
_STAGING_SCHEMA_STAGE = "post-extract"
_GOLDEN_PATH = os.path.join(_HERE, "golden_entries.json")

# 3 cases per PPM, chosen to exercise real structural variety -- see the
# approved plan's rationale table for why each was picked, not just the
# easiest-to-extract function.
GOLDEN_CASES = [
    ("mpi", "mpi_send"), ("mpi", "mpi_bcast"), ("mpi", "mpi_isend"),
    # shmem_int_broadcast/shmem_int_put no longer exist as separate concrete
    # entries -- collapsed into shmem_{T}_broadcast/shmem_{T}_put on
    # 2026-07-16 (identity.type_family now populated); see
    # docs/schema/schema-overview.md's Type-genericity note.
    ("shmem", "shmem_{T}_broadcast"), ("shmem", "shmem_{T}_put"), ("shmem", "shmem_barrier_all"),
    # shmem_{T}_and_reduce pins the operation-filtered type expansion: its table
    # (teamreducetypes) lists 26 types, but only the 14 whose bitwise column is
    # non-empty support AND, so type_family must have 14 members and must not
    # contain "char". Reading the table as a plain type list -- which is what
    # happened until 2026-09-12, when the table was not read at all -- would
    # mint shmem_char_and_reduce.
    ("shmem", "shmem_{T}_and_reduce"),
    ("nccl", "ncclBroadcast"), ("nccl", "ncclAllReduce"), ("nccl", "ncclSend"),
    ("nvshmem", "nvshmem_{T}_broadcast"), ("nvshmem", "nvshmem_broadcastmem"), ("nvshmem", "nvshmem_barrier"),
    # omp_get_thread_num: no parameters, a value return, desc from the 5.2
    # Summary. omp_target_memcpy: seven parameters and the ERROR_CODE carve-out,
    # with `dst` staying "out" where Fortran states no INTENT. omp_set_lock: the
    # ARB Fortran interface's INTENT(INOUT), the only source of an "inout" in the
    # corpus. omp_get_submemspace: a routine only 6.0 defines -- parameter names
    # from the specification prototype, bindings.fortran08 populated, desc null.
    # omp_set_affinity_format keeps its place for `char const *`, the
    # const-after-type spelling; the ARB header carries none of libomp's ompc_
    # link-name #defines, so that note is gone from it.
    ("openmp", "omp_get_thread_num"), ("openmp", "omp_target_memcpy"),
    ("openmp", "omp_set_lock"), ("openmp", "omp_get_submemspace"),
    ("openmp", "omp_set_affinity_format"),
    # cudaMemcpy: doxygen \brief/\param text and the per-thread-default-stream
    # note. cudaMalloc: `void **` and the __cudart_builtin__ qualifier.
    # cudaGetDriverEntryPoint: the one literal "deprecated as of CUDA X.Y".
    # cudaFree: the released-parameter correction, "in" where const/pointer-ness
    # alone reads "out".
    ("cuda", "cudaMemcpy"), ("cuda", "cudaMalloc"), ("cuda", "cudaGetDriverEntryPoint"),
    ("cuda", "cudaFree"),
    # Three cases added 2026-09-12, one per mechanism the macro expander gained
    # when the atomics, _g and sum/prod reductions turned out to be missing:
    #   nvshmem_{T}_atomic_fetch_add -- the OPGROUP macro form (the declaration
    #     template is named by token-pasting an abbreviation onto a prefix), the
    #     merge of one family's type axis across the separate BITWISE and
    #     STANDARD AMO invocations (7 + 5, so type_family must have 12 members),
    #     a return type that is itself the generic type, and dest's `inout`.
    #   nvshmem_{T}_sum_reduce -- a REPT macro whose body is nothing but a
    #     nested REPT call, so type_family must have all 24 arithmetic reduce
    #     types, not the 10 the enclosing table lists directly.
    #   nvshmem_{T}_g -- the same generic return type on the plain RMA path,
    #     the case that made the gap look like a macro problem rather than the
    #     declaration-regex problem it also was.
    ("nvshmem", "nvshmem_{T}_atomic_fetch_add"),
    ("nvshmem", "nvshmem_{T}_sum_reduce"),
    ("nvshmem", "nvshmem_{T}_g"),
]

# The exact key set Extract owns per section, expressed as top-level
# section keys so the "everything else is ABSENT" check (requirement #2)
# can walk section-by-section without hardcoding every dotted leaf path --
# see emit.py's own build_null_entry() for the authoritative skeleton this
# is checked against.
_IN_SCOPE_SECTIONS = {
    "identity": {"model", "name", "since", "deprecated_in", "standard_refs", "desc", "type_family"},
    "bindings": {"c", "fortran90", "fortran08", "lis", "cpp"},
    "return": {"kind", "binding_type"},
    "tool_integration": {"profiling_name"},
}
# relationships is in this set: every key -- variants, superseded_by,
# supersedes -- belongs to a later stage, so Extract emits {} for the whole
# section exactly as it already did for execution and semantics.
_ALWAYS_EMPTY_SECTIONS = {"execution", "semantics", "relationships"}
_IN_SCOPE_PARAMETER_KEYS = {
    "name", "direction", "desc", "binding_type", "asynchronous", "constant",
    "pointer", "array_type", "func_type", "length", "parameter_bindings",
    "root_only", "constraints",
}


def _load_module(unique_name, file_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(unique_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[unique_name] = module
    spec.loader.exec_module(module)
    return module


def _run_all_adapters(models=ALL_MODELS):
    # Only the models asked for: a build restricted with --ppm hands its
    # selection down as PPM_MODELS, and a model left out may be one whose
    # fetched inputs (workflow/fetch/manifest.json) are not on disk.
    #
    # Each PPM subpackage has its own module literally named adapter.py;
    # loaded under distinct sys.modules keys (not all as bare "adapter")
    # so their sibling-module imports (mpi/adapter.py importing "signature"
    # and "prose" from its own directory, already on sys.path from the
    # top of this file) resolve correctly without clobbering each other.
    def mpi():
        mpi_mod = _load_module("_extract_mpi_adapter", os.path.join(_HERE, "mpi", "adapter.py"))
        mpi_prose = _load_module("_extract_mpi_prose", os.path.join(_HERE, "mpi", "prose.py"))
        return mpi_mod.extract_mpi(prose_index=mpi_prose.build_prose_index())

    def adapter(model):
        mod = _load_module(f"_extract_{model}_adapter", os.path.join(_HERE, model, "adapter.py"))
        return getattr(mod, f"extract_{model}")()

    results = {}
    for model in models:
        extracted = mpi() if model == "mpi" else adapter(model)
        results[model] = {ir["function_key"]: (ir, flags) for ir, flags in extracted}
    return results


def _confident_to_jsonable(value):
    if isinstance(value, Confident):
        return {"__confident__": True, "value": value.value, "confidence": value.confidence, "note": value.note}
    return value


def _check_field_ownership(entry):
    """Every section/leaf outside what Extract owns must be ABSENT, not
    null -- walks the full assembled entry generically rather than
    re-listing every out-of-scope dotted path by hand. This is
    requirement #2's omission-based form (docs/overview/glossary.md (Staging schema)): a stray extra key is
    exactly as much a violation as a missing owned key, so both directions
    are checked via a plain key-set equality rather than a one-way scan."""
    problems = []
    for section in _ALWAYS_EMPTY_SECTIONS:
        if entry[section] != {}:
            problems.append(f"{section} should be empty ({{}}) but has keys {sorted(entry[section])!r}")

    for section, expected_keys in _IN_SCOPE_SECTIONS.items():
        actual_keys = set(entry[section].keys())
        if actual_keys != expected_keys:
            problems.append(f"{section} keys {sorted(actual_keys)!r} != expected {sorted(expected_keys)!r}")

    for i, p in enumerate(entry["parameters"]):
        actual_keys = set(p.keys())
        if actual_keys != _IN_SCOPE_PARAMETER_KEYS:
            problems.append(f"parameters[{i}] keys {sorted(actual_keys)!r} != expected {sorted(_IN_SCOPE_PARAMETER_KEYS)!r}")
        elif p["constraints"] != {}:
            problems.append(f"parameters[{i}].constraints should be empty ({{}}) but is {p['constraints']!r}")

    return problems


def generate_golden():
    """Regenerate golden_entries.json from the adapters' current real
    output. Not run automatically by run() -- a deliberate action, the
    same way updating workflow/formal/testdata/expansions.json is a deliberate action, not
    something a test run does on your behalf."""
    all_results = _run_all_adapters(ALL_MODELS)
    golden = {}
    for ppm, function_key in GOLDEN_CASES:
        ir, _flags = all_results[ppm][function_key]
        entry, _more_flags = assemble_entry(ir)
        key = f"{ppm}:{function_key}"
        # entry already contains exactly what Extract owns (checked
        # separately by _check_field_ownership) -- no subsetting needed.
        golden[key] = json.loads(json.dumps(entry, default=_confident_to_jsonable))
    with open(_GOLDEN_PATH, "w") as f:
        json.dump(golden, f, indent=2, sort_keys=True)
        f.write("\n")
    return golden


def run():
    staging_schema = staging_schema_for(_STAGING_SCHEMA_STAGE)

    if not os.path.exists(_GOLDEN_PATH):
        print(f"no golden file at {_GOLDEN_PATH} -- run generate_golden() first")
        return 1
    with open(_GOLDEN_PATH) as f:
        golden = json.load(f)

    all_results = _run_all_adapters(MODELS)
    failures = []
    checked = 0
    skipped = 0

    for ppm, function_key in GOLDEN_CASES:
        if ppm not in all_results:
            skipped += 1
            continue
        checked += 1
        key = f"{ppm}:{function_key}"
        label = key

        if function_key not in all_results[ppm]:
            failures.append(f"{label}: adapter no longer produces this function at all")
            continue

        ir, _flags = all_results[ppm][function_key]
        entry, _more_flags = assemble_entry(ir)

        try:
            validate_entry(entry, staging_schema)
        except ValidationError as e:
            failures.append(f"{label}: fails validate_entry against staging schema: {e}")

        if "formal" in entry["semantics"]:
            failures.append(f"{label}: semantics.formal is present (contract requirement #3 violated -- must be entirely absent coming out of Extract)")

        ownership_problems = _check_field_ownership(entry)
        for p in ownership_problems:
            failures.append(f"{label}: {p}")

        actual = json.loads(json.dumps(entry, default=_confident_to_jsonable))
        expected = golden.get(key)
        if expected is None:
            failures.append(f"{label}: no golden entry recorded (run generate_golden())")
        elif actual != expected:
            failures.append(f"{label}: adapter output drifted from golden_entries.json -- re-run generate_golden() and review the diff if this is an intentional change")

    print(f"{checked} golden case(s) checked"
          + (f", {skipped} skipped for models outside PPM_MODELS ({', '.join(MODELS)})." if skipped else "."))
    if failures:
        print(f"\n{len(failures)} FAILURE(S):")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("All golden cases validate against the staging schema, keep semantics.formal absent, "
          "leave every out-of-scope field absent (not null), and match golden_entries.json byte-for-byte.")
    return 0


if __name__ == "__main__":
    if "--generate" in sys.argv:
        generate_golden()
        print(f"wrote {_GOLDEN_PATH}")
        sys.exit(0)
    sys.exit(run())
