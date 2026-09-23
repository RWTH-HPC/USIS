"""
NVSHMEM's Heuristic Classification module. `nvshmemx_*` device-side extension
headers are out of Extract's v1 scope, but the
v1-scope headers it DOES read (`nvshmem_api.h`/`nvshmem_coll_api.h`) are not
host-only despite living under a `host/` directory -- many declarations there
are `__host__ __device__` (dual-callable) or bare `__device__` (device-only),
confirmed 2026-07-17 auditing the pilot corpus. execution.launch is therefore
derived per-function from the qualifier `workflow/extract/nvshmem/adapter.py`
now preserves on `bindings.c.signature` (see `_launch_for` below), not a
blanket constant the way classify_nccl.py's genuinely-correct `_LAUNCH_CPU`
is (NCCL's device header is excluded from Extract's scope at the file level,
a real, structural difference from NVSHMEM's mixed-in declarations).
execution.gpu_scope's device-scope naming convention (see
heuristics.nvshmem_gpu_scope_from_name) is included for completeness but
fires zero times against the *current* corpus. No atomic-operation family is
present in this corpus either (NVSHMEM's typed atomics live in the
device-side headers Extract doesn't ingest yet). What NVSHMEM does share with
SHMEM: the same `_nbi` nonblocking-suffix convention (78 real matches in the
corpus) and the same one-sided/collective naming split.

Grounded in the real corpus (instances/0_syntactic-api.json's NVSHMEM entries,
inspected while writing this).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from common.ir import Confident  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from heuristics import (
    kind_from_c_type,  # noqa: E402
    nvshmem_gpu_scope_from_name, parameter_kind, return_value_kind, is_pointer_param,
    shmem_nonblocking_immediate, shmem_synchronization_name,
)

_QUERY_SUBSTRINGS = ("my_pe", "n_pes", "get_config", "translate_pe")
# "free" added 2026-07-17 after reviewing the pilot corpus -- nvshmem_free (symmetric-heap
# deallocation) matched none of the four original substrings and was
# silently null. Confirmed against the real corpus that "free" matches only
# this one function (no other NVSHMEM host-API name contains it).
_MANAGEMENT_SUBSTRINGS = ("team_destroy", "team_split", "init", "finalize", "free")
_COLLECTIVE_SUBSTRINGS = ("broadcast", "collect", "alltoall", "reduce", "barrier", "sync")
_ONE_SIDED_SUBSTRINGS = ("put", "get", "signal")

# Replaced 2026-07-17: the blanket "always cpu" claim this constant used to
# encode (matching classify_nccl.py's genuinely-correct _LAUNCH_CPU) turned
# out to be wrong for NVSHMEM specifically, found auditing the pilot corpus
# against the real headers directly (execution.launch was wrong for 9 of 10
# NVSHMEM pilot functions). Unlike
# NCCL (which excludes its device-side header, nccl_device.h, from Extract's
# v1 scope entirely), NVSHMEM's "host/" header directory name is misleading
# -- it also declares __host__ __device__ (dual-callable) and bare __device__
# (device-only) functions, which workflow/extract/nvshmem/adapter.py now
# preserves as a literal qualifier prefix on bindings.c.signature (see that
# adapter's own comment). This derives execution.launch from that real
# per-function signal instead of a wrong constant -- matching what
# curated/field-provenance.json's own execution.launch rationale already said
# should happen ("syntactic when the source has __host__/__device__
# qualifiers... NVSHMEM headers").
def _launch_for(entry):
    sig = ((entry.get("bindings") or {}).get("c") or {}).get("signature") or ""
    has_host = "__host__" in sig
    has_device = "__device__" in sig
    if has_host and has_device:
        return Confident("cpu+gpu", "pattern", "signature carries both __host__ and __device__ qualifiers")
    if has_device:
        return Confident("gpu", "pattern", "signature carries a __device__ qualifier with no __host__ counterpart")
    return Confident("cpu", "pattern", "no __host__/__device__ qualifier in the signature -- genuinely host-only")


def _api_group(function_key):
    if any(s in function_key for s in _QUERY_SUBSTRINGS):
        return Confident("query", "pattern", "NVSHMEM query-function name substring")
    if any(s in function_key for s in _MANAGEMENT_SUBSTRINGS):
        return Confident("management", "pattern", "NVSHMEM lifecycle/team-management name substring")
    # "synchronization" (fence/quiet/wait_until/_test point-poll family)
    # -- checked BEFORE one_sided deliberately: nvshmem_signal_wait_until
    # contains the "signal" substring and would otherwise misclassify as
    # one_sided, but it locally waits on a signal variable, it doesn't move
    # data. (nvshmem_fence/quiet were 2 of the 5 functions that grounded the
    # new enum value -- see known-gaps-and-open-questions.md's resolved row.)
    if shmem_synchronization_name(function_key):
        return Confident("synchronization", "pattern", "NVSHMEM local-synchronization name convention (fence/quiet/wait_until/_test)")
    if any(s in function_key for s in _COLLECTIVE_SUBSTRINGS):
        return Confident("collective", "pattern", "NVSHMEM collective-operation name substring")
    if any(s in function_key for s in _ONE_SIDED_SUBSTRINGS):
        return Confident("one_sided", "pattern", "NVSHMEM one-sided/signal name substring (put/get/signal)")
    # 2026-07-21, second full-corpus audit -- the same three misses OpenSHMEM
    # had (see classify_shmem's own note). nvshmem_{T}_p is the single-element
    # put, whose one-letter verb no "put" substring can match;
    # nvshmem_query_thread is an inquiry the _QUERY_SUBSTRINGS list doesn't
    # cover; nvshmem_global_exit terminates the program, i.e. lifecycle.
    if function_key.endswith("_p"):
        return Confident("one_sided", "pattern", "NVSHMEM single-element RMA put (_p)")
    if function_key == "nvshmem_query_thread":
        return Confident("query", "pattern", "NVSHMEM thread-level inquiry")
    if function_key == "nvshmem_global_exit":
        return Confident("management", "pattern", "NVSHMEM program-termination call")
    return None


def _blocking(function_key):
    """Same `_nbi` convention, same reasoning as classify_shmem._blocking --
    NVSHMEM inherits OpenSHMEM's naming and its completion model, and marks
    every nonblocking routine in the symbol. Kept as its own function rather
    than imported from the SHMEM module so each PPM's note cites its own
    standard, matching how _variants is already duplicated across the two.
    """
    if shmem_nonblocking_immediate(function_key):
        return Confident(False, "pattern",
                         "NVSHMEM _nbi suffix: initiates the transfer and returns, "
                         "completion observable only via nvshmem_quiet/nvshmem_fence")
    return Confident(True, "pattern",
                     "NVSHMEM: no _nbi suffix -- the routine returns once its own local "
                     "effect is complete")


# NVSHMEM's collective set. NVSHMEM implements the OpenSHMEM API, and its
# documentation states collectivity the same way, per API area rather than per
# routine (external-inputs/nvshmem/docs/3.7.0/gen/api/): "nvshmem_barrier is a
# collective synchronization routine over a team", "nvshmem_alltoall routines
# are collective routines", "nvshmem_team_split_strided routine is a collective
# routine", and memory.md's "collective allocation of Symmetric Data Objects".
# Enumerated rather than pattern-matched so it cannot drift into the atomics and
# RMA families that share the nvshmem_{T}_ prefix (audited 2026-09-13).
#
# The explicit negatives the documentation gives are honoured: "nvshmem_quiet is
# a local, non-collective operation", and nvshmem_global_exit is OpenSHMEM's
# non-collective "any one PE forces termination" routine.
_COLLECTIVE_NAMES = frozenset({
    # Symmetric-heap allocation -- collective for the same reason OpenSHMEM's is
    "nvshmem_align", "nvshmem_calloc", "nvshmem_free", "nvshmem_malloc",
    # Initialization and finalization
    "nvshmem_init", "nvshmem_init_thread", "nvshmem_finalize",
    # Collective communication
    "nvshmem_alltoallmem", "nvshmem_broadcastmem", "nvshmem_fcollectmem",
    "nvshmem_{T}_alltoall", "nvshmem_{T}_broadcast", "nvshmem_{T}_fcollect",
    # Reductions and reduce-scatters
    "nvshmem_{T}_and_reduce", "nvshmem_{T}_max_reduce", "nvshmem_{T}_min_reduce",
    "nvshmem_{T}_or_reduce", "nvshmem_{T}_prod_reduce", "nvshmem_{T}_sum_reduce",
    "nvshmem_{T}_xor_reduce",
    "nvshmem_{T}_and_reducescatter", "nvshmem_{T}_max_reducescatter",
    "nvshmem_{T}_min_reducescatter", "nvshmem_{T}_or_reducescatter",
    "nvshmem_{T}_prod_reducescatter", "nvshmem_{T}_sum_reducescatter",
    "nvshmem_{T}_xor_reducescatter",
    # Synchronization over a team
    "nvshmem_barrier", "nvshmem_barrier_all", "nvshmem_sync_all", "nvshmem_team_sync",
    # Team construction and destruction
    "nvshmem_team_destroy", "nvshmem_team_split_2d", "nvshmem_team_split_strided",
})


def _collective(function_key):
    """execution.collective -- "every PE in the team must call this".

    Same shape as classify_shmem._collective, including the part a rule built
    on identity.api_group alone would miss: nvshmem_malloc and nvshmem_free are
    `management` by group and collective by the documentation, because the
    symmetric heap requires every PE to agree on its layout.
    """
    if function_key in _COLLECTIVE_NAMES:
        return Confident(True, "pattern",
                         "NVSHMEM 3.7.0: documented as a collective routine over a team, the world "
                         "team, or the symmetric heap")
    return Confident(False, "pattern",
                     "NVSHMEM 3.7.0: not documented as collective -- a PE may call this without any "
                     "other PE doing so")


def _execute_once(function_key):
    """execution.execute_once -- always false for NVSHMEM, same as OpenSHMEM.

    NVSHMEM inherits OpenSHMEM's initialization model and says so directly:

      "Multiple calls to nvshmem_init are allowed, and must be called by the
       same set of processes as the initial call to nvshmem_init. At the end
       of the NVSHMEM program which it initialized, each call to
       nvshmem_init must be matched with a call to nvshmem_finalize."
       -- NVSHMEM 3.7.0, docs/gen/api/setup.md

    Worth stating plainly because api-schema.json's own description of this
    field named `nvshmem_init` as its example of a true value. The example
    was wrong against NVSHMEM's documentation; the field's stated criterion
    ("may be called at most once per process") is what is implemented, and
    the description has been corrected in place. See
    classify_mpi._execute_once for the one standard that does forbid it.
    """
    return Confident(False, "pattern",
                     "NVSHMEM 3.7.0 (setup.md): multiple calls to nvshmem_init are allowed, each "
                     "matched by an nvshmem_finalize, so no NVSHMEM routine is restricted to one "
                     "call per process")


def _variants(function_key, all_function_keys):
    """Same `_nbi` nonblocking-suffix convention as SHMEM (see
    classify_shmem.py) -- 78 real matches in the current corpus.
    """
    variants = {}
    if function_key.endswith("_nbi"):
        base = function_key[: -len("_nbi")]
        if base in all_function_keys:
            variants["blocking"] = Confident(base, "pattern", "NVSHMEM _nbi-suffix naming convention")
    else:
        nb = function_key + "_nbi"
        if nb in all_function_keys:
            variants["nonblocking"] = Confident(nb, "pattern", "NVSHMEM _nbi-suffix naming convention")
    return variants or None


def _parameters(function_key, entry):
    out = []
    for p in entry["parameters"]:
        is_ptr = is_pointer_param(p)
        kind = parameter_kind(p.get("name"), is_ptr, function_key)
        # Deterministic C-type fallback -- only ever fills a null the
        # name rules left behind; see heuristics.kind_from_c_type.
        kind_reason = f"parameter name/type heuristic ({p.get('name')!r})"
        if kind is None:
            kind = kind_from_c_type(p)
            if kind is not None:
                kind_reason = ("declared C handle type "
                               f"({(p.get('binding_type') or {}).get('c')!r}) -- unambiguous, not a name guess")
        kind_c = Confident(kind, "pattern", kind_reason) if kind else None
        not_null_c = None
        if is_ptr is True and p.get("direction") in ("in", "inout"):
            not_null_c = Confident(True, "pattern", "required (non-optional) pointer parameter convention")
        out.append({"kind": kind_c, "not_null": not_null_c})
    return out


def classify_nvshmem(entries):
    """entries: {function_key: full syntactic entry} for model=="nvshmem".
    Returns list[(ir_dict, flags_list)], mirroring Extract adapters' shape.
    """
    all_keys = set(entries)
    results = []
    for function_key, entry in entries.items():
        # Rank and team-size queries, per function -- see heuristics._RETURN_VALUE_KINDS.
        value_kind = return_value_kind(function_key, entry["return"]["kind"])
        value_kind = Confident(value_kind, "pattern", "rank/team-size query, listed per function") if value_kind else None
        launch = _launch_for(entry)
        launch_is_gpu = launch is not None and "gpu" in (launch.value or "")
        # The _warp/_block/_thread suffix heuristic is only meaningful for a
        # routine that is actually device-callable. Unguarded it also matched
        # nvshmem_query_thread -- a HOST query about the initialized thread
        # level, whose trailing "_thread" is the noun it queries, not a CUDA
        # execution scope. That produced the one live gpu_scope/launch
        # contradiction in the corpus (gpu_scope='thread', launch='cpu').
        gpu_scope = nvshmem_gpu_scope_from_name(function_key) if launch_is_gpu else None
        gpu_scope_reason = "NVSHMEM device-scope suffix naming convention"
        if gpu_scope is None and launch_is_gpu:
            # A device-callable routine with gpu_scope null contradicts the
            # field's own definition ("null if not GPU-callable") -- and 49 of
            # this corpus's 67 entries were in exactly that state before the
            # 2026-07-21 full-corpus audit, because the suffix heuristic only
            # ever fires on the _warp/_block/_thread names and NONE of those
            # are in Extract's v1 scope (they live in nvshmemx_*, excluded).
            #
            # The unsuffixed device API is per-thread by construction: each
            # calling thread issues the operation independently, and the
            # cooperative-group forms are separate symbols that spell their
            # scope in the name. So "no suffix" is not missing information
            # here -- it IS the thread-scope signal, and reading it that way
            # is what the suffix convention means, not an extra assumption.
            gpu_scope = "thread"
            gpu_scope_reason = ("unsuffixed NVSHMEM device API is per-thread by construction -- the "
                                "_warp/_block cooperative-group forms are separate nvshmemx_* symbols "
                                "that name their scope explicitly")
        ir = {
            "model": "nvshmem",
            "function_key": function_key,
            "identity.api_group": _api_group(function_key),
            "execution.blocking": _blocking(function_key),
            "execution.execute_once": _execute_once(function_key),
            "execution.collective": _collective(function_key),
            "execution.launch": launch,
            "execution.gpu_scope": Confident(gpu_scope, "pattern", gpu_scope_reason) if gpu_scope else None,
            "execution.stages": None,
            "execution.procedure_class": None,
            "semantics.atomic": None,          # NVSHMEM's typed atomics are device-side, out of v1 Extract scope
            "relationships.variants": _variants(function_key, all_keys),
            "return.value_kind": value_kind,
            "parameters": _parameters(function_key, entry),
            "flags": [],
        }
        results.append((ir, ir["flags"]))
    return results
