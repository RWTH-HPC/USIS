"""
Self-contained golden-example test harness for Heuristic Classification,
mirroring workflow/extract/test_emit.py's pattern (no pytest, no jsonschema
package -- see workflow/formal/validate.py's docstring for why): re-run all
4 classifiers, pick out 12 real functions (3 per PPM) chosen to exercise
each of the 13 Heuristic-Classification-owned fields at least once -- not just the easy path --
and check:

  1. the assembled entry validates against
     instances/api-schema.staging.post-heuristic-classification.json (built
     2026-07-20 alongside the omission-based staging fix -- see
     docs/overview/glossary.md (Staging schema) -- so this
     stage now has its own precise staging schema instead of reusing
     Extract's looser one);
  2. every field outside the 13 Heuristic-Classification-owned leaves is byte-identical to the
     source syntactic-api.json entry (enforces the passthrough half of the
     interface contract,
     for every case at once);
  3. the 13 owned leaves match a checked-in golden value byte-for-byte
     (workflow/classify/golden_entries.json) -- catches a future heuristic
     change silently altering real output.

Golden values were captured from these classifiers' own real output against
Extract's real output over the real external-inputs/ sources -- grounded, not
synthetic -- and spot-checked by hand before being committed. The input is
produced fresh on every run by running Extract into a temporary directory,
never read from instances/, so the test needs no prior build and cannot pass
against a stale checkpoint.

Run directly: python3 workflow/classify/test_emit.py
"""

import copy
import importlib.util
import json
import os
import subprocess
import sys
import tempfile

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
from common.ir import Confident, unwrap  # noqa: E402

from classify_mpi import classify_mpi  # noqa: E402
from classify_shmem import classify_shmem  # noqa: E402
from classify_nccl import classify_nccl  # noqa: E402
from classify_nvshmem import classify_nvshmem  # noqa: E402
from classify_openmp import classify_openmp  # noqa: E402
from classify_cuda import classify_cuda  # noqa: E402

_LAYOUT_COMMON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common")
sys.path.insert(0, _LAYOUT_COMMON)
sys.path.insert(0, os.path.join(_LAYOUT_COMMON, "..", "staging"))
from derive_schema import staging_schema_for  # noqa: E402
from layout import ALL_MODELS, MODELS, external_input  # noqa: E402

# validate_entry.py is bare-named and lives in workflow/extract/ -- loaded
# by explicit file path to avoid colliding with this package's own
# emit.py/heuristics.py (see cli.py's docstring for the identical
# workaround, and workflow/extract/cli.py's own "adapter" collision note).
_spec = importlib.util.spec_from_file_location("_classify_test_validate_entry", os.path.join(_HERE, "..", "extract", "validate_entry.py"))
_validate_entry_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_validate_entry_mod)
validate_entry = _validate_entry_mod.validate_entry
ValidationError = _validate_entry_mod.ValidationError

_ROOT = os.path.join(_HERE, "..", "..")
_STAGING_SCHEMA_STAGE = "post-heuristic-classification"
_GOLDEN_PATH = os.path.join(_HERE, "golden_entries.json")

CLASSIFIERS = {"mpi": classify_mpi, "shmem": classify_shmem, "nccl": classify_nccl, "nvshmem": classify_nvshmem,
               "openmp": classify_openmp, "cuda": classify_cuda}

# 35 cases, chosen to hit each of the 13 owned fields at least
# once: mpi_ibcast/mpi_bcast_init exercise procedure_class/stages/variants;
# mpi_compare_and_swap/mpi_fetch_and_op exercise semantics.atomic (including
# the "withheld, not partially populated" case); mpi_psend_init exercises
# the pp-op partitioned-naming exception; the shmem/nvshmem _nbi cases
# exercise their own variants convention; ncclBroadcast/nvshmem_broadcastmem
# exercise execution.launch's scope-constant "static" confidence (no flag).
GOLDEN_CASES = [
    ("mpi", "mpi_bcast"), ("mpi", "mpi_ibcast"), ("mpi", "mpi_bcast_init"),
    ("mpi", "mpi_compare_and_swap"), ("mpi", "mpi_fetch_and_op"), ("mpi", "mpi_psend_init"),
    # mpi_init is the only execute_once=true arm in the whole corpus, and
    # shmem_init is the deviation from the hand-written supplement that
    # OpenSHMEM's own "may be called multiple times" clause forces -- both
    # pinned here so a future edit to either rule shows up as a golden diff.
    ("mpi", "mpi_init"), ("shmem", "shmem_init"),
    # execution.collective's two rules that a promotion of identity.api_group
    # would get wrong in opposite directions: mpi_reduce_local is api_group
    # "collective" and is not, shmem_malloc is "management" and is.
    ("mpi", "mpi_reduce_local"), ("shmem", "shmem_malloc"),
    # shmem_ctx_int32_atomic_compare_swap / shmem_int32_atomic_fetch_add_nbi no
    # longer exist as separate concrete entries -- collapsed into
    # shmem_ctx_{T}_atomic_compare_swap / shmem_{T}_atomic_fetch_add_nbi on
    # 2026-07-16 (identity.type_family now populated); the atomic-suffix
    # heuristic (heuristics.py's _ATOMIC_SUFFIX_RE) matches the suffix after
    # "atomic_", not the type prefix, so it fires identically on the
    # collapsed name.
    ("shmem", "shmem_ctx_{T}_atomic_compare_swap"), ("shmem", "shmem_{T}_atomic_fetch_add_nbi"),
    ("nccl", "ncclBroadcast"), ("nccl", "ncclSend"),
    ("nvshmem", "nvshmem_broadcastmem"), ("nvshmem", "nvshmem_{T}_put_nbi"),
    # omp_get_thread_num: query, launch deliberately null. omp_target_memcpy_async:
    # the null api_group of a local copy, and the _async variants convention.
    # omp_mempartition_set_part: a 6.0 routine whose group comes from its own
    # documented effect rather than a name prefix.
    ("openmp", "omp_get_thread_num"), ("openmp", "omp_target_memcpy_async"),
    ("openmp", "omp_mempartition_set_part"),
    # cudaMalloc: launch and gpu_scope for a routine the device runtime really
    # does declare, the void ** SCALAR rule and the Async variants convention.
    # cudaMemcpy: null api_group, and the C-type rules winning over the shared
    # dst/src name rules. cudaStreamCreateWithPriority and cudaGraphLaunch are
    # the two directions the device-runtime header corrects: __cudart_builtin__
    # without a device declaration -> cpu, and a device declaration without the
    # qualifier -> cpu+gpu.
    ("cuda", "cudaMalloc"), ("cuda", "cudaMemcpy"),
    ("cuda", "cudaStreamCreateWithPriority"), ("cuda", "cudaGraphLaunch"),
    # The rank/team-size vocabulary. mpi_comm_size and ncclCommCount are
    # TEAM_SIZE out-parameters;
    # mpi_type_size is the pointer "size" that must STAY SCALAR, which is why
    # TEAM_SIZE is per-function. shmem_my_pe and nvshmem_team_n_pes carry
    # return.value_kind; omp_get_max_threads is the value return left null on
    # purpose. (omp_get_thread_num above covers value_kind RANK for OpenMP.)
    ("mpi", "mpi_comm_size"), ("mpi", "mpi_type_size"), ("nccl", "ncclCommCount"),
    ("shmem", "shmem_my_pe"), ("nvshmem", "nvshmem_team_n_pes"), ("openmp", "omp_get_max_threads"),
    # THREAD_LEVEL (mpi_init_thread's required/provided), the *_team
    # out-parameter TEAM fix (shmem_team_split_strided's new_team), DEVICE by
    # value and through a pointer (cudaSetDevice, ncclCommCuDevice) and as
    # return.value_kind (omp_get_device_num), and SIG_OP.
    ("mpi", "mpi_init_thread"), ("shmem", "shmem_team_split_strided"), ("cuda", "cudaSetDevice"),
    ("nccl", "ncclCommCuDevice"), ("openmp", "omp_get_device_num"), ("shmem", "shmem_{T}_put_signal"),
]


def _load_syntactic(models=ALL_MODELS):
    # Only the models asked for (PPM_MODELS, which build.py --ppm sets): a
    # model left out may be one whose fetched inputs are not on disk.
    #
    # Runs Extract itself, into a throwaway directory, rather than reading
    # instances/0_syntactic-api.json: the test then needs no prior build and
    # cannot pass against a stale checkpoint. A subprocess, not an import,
    # because extract/ and classify/ both have modules named emit, cli, ...
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, PPM_OUT_DIR=tmp, PPM_MODELS=",".join(models))
        subprocess.run([sys.executable, os.path.join(_HERE, "..", "extract", "cli.py")],
                       env=env, check=True, stdout=subprocess.DEVNULL)
        with open(os.path.join(tmp, "0_syntactic-api.json")) as f:
            return json.load(f)


def _group_by_model(syntactic, models=ALL_MODELS):
    by_model = {model: {} for model in models}
    for entry_key, entry in syntactic.items():
        model, function_key = entry_key.split(":", 1)
        by_model[model][function_key] = entry
    return by_model


def _run_all_classifiers(by_model):
    return {model: {ir["function_key"]: (ir, flags) for ir, flags in CLASSIFIERS[model](by_model[model])}
            for model in by_model}


def _confident_to_jsonable(value):
    if isinstance(value, Confident):
        return {"__confident__": True, "value": value.value, "confidence": value.confidence, "note": value.note}
    return value


def _entry_owned_subset(entry):
    """Just the 13 Heuristic-Classification-owned leaves, for golden-diffing -- avoids
    re-asserting the full passthrough entry in the golden file (that
    invariant is checked separately and uniformly by _check_passthrough,
    not duplicated per golden case)."""
    return {
        "identity.api_group": entry["identity"]["api_group"],
        # .get(): execution.blocking and execution.execute_once are the owned
        # fields emit.py writes conditionally -- both are required,
        # NON-nullable booleans, so "no answer" is expressed by leaving the
        # key absent rather than by null (see emit.py's comment). Every
        # classifier answers for every entry today, so in practice these are
        # always present.
        "execution.blocking": entry["execution"].get("blocking"),
        "execution.execute_once": entry["execution"].get("execute_once"),
        "execution.collective": entry["execution"].get("collective"),
        "execution.launch": entry["execution"]["launch"],
        "execution.gpu_scope": entry["execution"]["gpu_scope"],
        "execution.stages": entry["execution"]["stages"],
        "execution.procedure_class": entry["execution"]["procedure_class"],
        # atomic/variants are OMITTED (not present) when nothing matched --
        # see docs/overview/glossary.md (Staging schema) --
        # .get() rather than a direct subscript, since either side may
        # legitimately lack the key entirely.
        "semantics.atomic": entry["semantics"].get("atomic"),
        "relationships.variants": entry["relationships"].get("variants"),
        "return.value_kind": entry["return"]["value_kind"],
        "parameters": [{"kind": p["kind"], "not_null": p["constraints"]["not_null"]} for p in entry["parameters"]],
    }


_VARIANT_KEYS = ("nonblocking", "blocking", "persistent", "neighborhood", "host", "gpu")


def _check_passthrough(source_entry, entry):
    """Every field outside the 13 owned leaves must be byte-identical to the
    source entry -- null both sides' owned leaves out and compare the rest,
    rather than re-listing every passthrough path by hand. Assignment (not
    a read-then-check) throughout, since atomic/variants may legitimately
    be absent on either side -- normalizing via assignment adds the key
    with the same neutral value on both sides regardless of whether it was
    there to begin with, so the comparison stays valid either way."""
    a, b = copy.deepcopy(source_entry), copy.deepcopy(entry)
    for e in (a, b):
        e["identity"]["api_group"] = None
        # Assignment, like every other owned leaf here, and for the extra
        # reason that these two are absent on the source side by
        # construction: execution.blocking, execution.execute_once and
        # execution.collective are
        # Classify-owned now, so Extract never writes them. Assigning None on
        # both sides is what keeps that legitimate absence from reading as a
        # passthrough violation.
        e["execution"]["blocking"] = None
        e["execution"]["execute_once"] = None
        e["execution"]["collective"] = None
        e["execution"]["launch"] = None
        e["execution"]["gpu_scope"] = None
        e["execution"]["stages"] = None
        e["execution"]["procedure_class"] = None
        e["semantics"]["atomic"] = None
        e["relationships"]["variants"] = {k: None for k in _VARIANT_KEYS}
        # Absent on the source side by construction, like the execution
        # booleans: Extract omits a field it does not own.
        e["return"]["value_kind"] = None
        for p in e["parameters"]:
            p["kind"] = None
            p["constraints"]["not_null"] = None
    return a == b


def generate_golden():
    """Regenerate golden_entries.json from the classifiers' current real
    output. Not run automatically by run() -- a deliberate action, the same
    way updating workflow/extract/golden_entries.json is."""
    by_model = _group_by_model(_load_syntactic())
    all_results = _run_all_classifiers(by_model)
    golden = {}
    for ppm, function_key in GOLDEN_CASES:
        ir, _flags = all_results[ppm][function_key]
        entry, _more_flags = assemble_classified_entry(by_model[ppm][function_key], ir)
        golden[f"{ppm}:{function_key}"] = json.loads(json.dumps(_entry_owned_subset(entry), default=_confident_to_jsonable))
    with open(_GOLDEN_PATH, "w") as f:
        json.dump(golden, f, indent=2, sort_keys=True)
        f.write("\n")
    return golden


def _check_forum_execute_once_not_inherited(all_results):
    """The MPI Forum's apis.json carries an `attributes.execute_once` of its
    own, and it is a FALSE FRIEND: `false` on all 571 entries, MPI_Init
    included. It is a document-rendering flag, unrelated to this schema's
    "may be called at most once per process".

    Wiring it up would produce an all-false MPI column that looks
    authoritative and is wrong on exactly the three entries that matter, so
    this asserts the disagreement stays visible: the Forum says false for
    mpi_init, and classify_mpi says true.

    Returns a list of failure strings (empty when correct)."""
    apis_path = external_input("mpi", "tex", "mpi-standard", "apis.json")
    if not os.path.exists(apis_path):
        return [f"{apis_path} missing -- cannot check the Forum execute_once false friend"]
    with open(apis_path) as f:
        forum = json.load(f)

    failures = []
    forum_value = forum.get("mpi_init", {}).get("attributes", {}).get("execute_once")
    if forum_value is not False:
        failures.append(
            "external-inputs' apis.json no longer reports attributes.execute_once=false for "
            f"mpi_init (got {forum_value!r}) -- re-read classify_mpi._execute_once before trusting it")

    ours, _flags = all_results["mpi"]["mpi_init"]
    if unwrap(ours["execution.execute_once"])[0] is not True:
        failures.append(
            "classify_mpi no longer reports execute_once=true for mpi_init -- the MPI world model "
            "cannot be initialized more than once (chap-dynamic/dynamic-2.tex)")
    return failures


def run():
    staging_schema = staging_schema_for(_STAGING_SCHEMA_STAGE)

    if not os.path.exists(_GOLDEN_PATH):
        print(f"no golden file at {_GOLDEN_PATH} -- run generate_golden() first")
        return 1
    with open(_GOLDEN_PATH) as f:
        golden = json.load(f)

    by_model = _group_by_model(_load_syntactic(MODELS), MODELS)
    all_results = _run_all_classifiers(by_model)
    failures = []
    checked = 0
    skipped = 0

    for ppm, function_key in GOLDEN_CASES:
        if ppm not in all_results:
            skipped += 1
            continue
        checked += 1
        key = f"{ppm}:{function_key}"

        if function_key not in all_results[ppm]:
            failures.append(f"{key}: classifier no longer produces this function at all")
            continue

        ir, _flags = all_results[ppm][function_key]
        source_entry = by_model[ppm][function_key]
        entry, _more_flags = assemble_classified_entry(source_entry, ir)

        try:
            validate_entry(entry, staging_schema)
        except ValidationError as e:
            failures.append(f"{key}: fails validate_entry against staging schema: {e}")

        if not _check_passthrough(source_entry, entry):
            failures.append(f"{key}: a field outside the 13 Heuristic-Classification-owned leaves was modified")

        actual = json.loads(json.dumps(_entry_owned_subset(entry), default=_confident_to_jsonable))
        expected = golden.get(key)
        if expected is None:
            failures.append(f"{key}: no golden entry recorded (run generate_golden())")
        elif actual != expected:
            failures.append(f"{key}: classifier output drifted from golden_entries.json -- re-run generate_golden() and review the diff if this is an intentional change")

    if "mpi" in all_results:
        failures.extend(_check_forum_execute_once_not_inherited(all_results))

    print(f"{checked} golden case(s) checked"
          + (f", {skipped} skipped for models outside PPM_MODELS ({', '.join(MODELS)})." if skipped else "."))
    if failures:
        print(f"\n{len(failures)} FAILURE(S):")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("All golden cases validate against the staging schema, leave every field outside the 13 "
          "Heuristic-Classification-owned leaves untouched, and match golden_entries.json byte-for-byte.")
    return 0


if __name__ == "__main__":
    if "--generate" in sys.argv:
        generate_golden()
        print(f"wrote {_GOLDEN_PATH}")
        sys.exit(0)
    sys.exit(run())
