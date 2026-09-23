"""
OpenMP's Heuristic Classification module. The corpus is the `omp_*` runtime
library routines the OpenMP ARB declares in its own omp.h
(workflow/extract/openmp/adapter.py): no collectives, no point-to-point or
one-sided data movement, no atomics, no MPI-4-style procedure taxonomy. What
there is to classify:

  identity.api_group -- the specification's own naming convention.
      omp_get_*, omp_in_*, omp_is_*, omp_target_is_* and the
      omp_display_*/omp_capture_* reporting routines inquire and change nothing
      (query); omp_set_*, the lock/allocator/device-memory lifecycle and
      omp_pause_resource* manage runtime state (management); lock
      set/unset/test and omp_fulfill_event order threads or tasks against each
      other (synchronization). The device-memory copy/fill routines --
      omp_target_memcpy*, omp_target_memset* -- are a local copy, which fits
      none of the seven groups: left null and logged as a gap
      (docs/cross-ppm-analysis/known-gaps-and-open-questions.md) rather than
      forced into one.
  execution.launch/gpu_scope -- left null. omp.h is the same header for host
      and offload-device compilation, and whether a routine may be called
      inside a target region is a per-routine restriction in the
      specification, visible in no declaration.
  relationships.variants -- the `_async` suffix pairs a device-memory routine
      with its asynchronous (task-based) counterpart: omp_target_memcpy /
      omp_target_memcpy_async, and the _rect and memset pairs.
  parameters[].kind/.constraints.not_null -- the shared rules in heuristics.py.
      The ARB header names every parameter, so the name rules apply here where
      libomp's unnamed declarations used to leave them nothing to read; a kind
      still stays null where the name settles nothing and the C type is as
      overloaded as `size_t` (a length and two offsets in omp_target_memcpy).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from common.ir import Confident  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from heuristics import kind_from_c_type, parameter_kind, return_value_kind, is_pointer_param  # noqa: E402

# Checked first: omp_set_lock would otherwise match the omp_set_ management prefix.
_SYNCHRONIZATION_NAMES = frozenset({
    "omp_set_lock", "omp_unset_lock", "omp_test_lock",
    "omp_set_nest_lock", "omp_unset_nest_lock", "omp_test_nest_lock",
    "omp_fulfill_event",
})
_LOCAL_COPY_PREFIXES = ("omp_target_memcpy", "omp_target_memset")
# omp_ancestor_is_ is the one inquiry prefix that is not omp_<verb>_: OpenMP 6.0
# section 21.12, "returns true if the ancestor thread of the encountering thread
# is a free-agent thread ...; otherwise, it returns false".
_QUERY_PREFIXES = ("omp_get_", "omp_in_", "omp_is_", "omp_ancestor_is_", "omp_target_is_",
                   "omp_display_", "omp_capture_")
_QUERY_NAMES = frozenset({
    # 6.0 section 27.8: returns the user data that the partitioner associated
    # with the partition -- an inquiry, despite the mempartition_ prefix.
    "omp_mempartition_get_user_data",
})
_MANAGEMENT_PREFIXES = (
    "omp_set_", "omp_init_", "omp_destroy_", "omp_pause_resource",
    "omp_target_alloc", "omp_target_free", "omp_target_associate_ptr", "omp_target_disassociate_ptr",
)
_MANAGEMENT_NAMES = frozenset({
    "omp_alloc", "omp_aligned_alloc", "omp_calloc", "omp_aligned_calloc", "omp_realloc", "omp_free",
    # 6.0 section 27.6: "defines the size and resource of a given part of a
    # memory partition" -- configuration of an allocator object, as omp_set_* is
    # configuration of an ICV.
    "omp_mempartition_set_part",
})


def _api_group(function_key):
    if function_key in _SYNCHRONIZATION_NAMES:
        return Confident("synchronization", "pattern",
                         "OpenMP lock acquire/release/test or task-event fulfilment -- orders threads/tasks, "
                         "moves no data")
    if function_key.startswith(_LOCAL_COPY_PREFIXES):
        return None  # a local copy/fill fits no api_group -- the logged gap, see the module docstring
    if function_key.startswith(_QUERY_PREFIXES) or function_key in _QUERY_NAMES:
        return Confident("query", "pattern", "OpenMP inquiry-routine naming convention (get/in/is/display)")
    if function_key.startswith(_MANAGEMENT_PREFIXES) or function_key in _MANAGEMENT_NAMES:
        return Confident("management", "pattern",
                         "OpenMP runtime-state or lock/allocator/device-memory lifecycle routine")
    return None


def _blocking(function_key):
    """execution.blocking from OpenMP's `_async` suffix.

    The OpenMP runtime API has exactly one asynchronous family, and the ARB
    names it in the symbol: omp_target_memcpy_async,
    omp_target_memcpy_rect_async and omp_target_memset_async take a depobj
    list and return once the operation is *enqueued*. Every other omp_*
    routine -- the runtime-state setters and inquiries, the lock routines
    (omp_set_lock blocks until it holds the lock; that is blocking, not
    asynchronous), the allocators and the synchronous device-memory
    routines -- returns once its own effect is done.

    Note this contradicts a convention some consumers carry: a query like
    omp_get_thread_num is *blocking* here, in the same sense MPI_Comm_rank
    is (it returns its answer before it returns), not "nonblocking" because
    it is cheap. curated/supplement/supplement-openmp.json already said
    `true` for the three thread-number queries by hand; this reproduces
    that.
    """
    if function_key.endswith("_async"):
        return Confident(False, "pattern",
                         "OpenMP _async suffix: returns once the operation is enqueued, "
                         "completion tracked through its depobj list")
    return Confident(True, "pattern",
                     "OpenMP: no _async suffix -- the routine returns once its own effect is "
                     "complete (the ARB marks its only asynchronous family in the symbol)")


def _collective(function_key):
    """execution.collective -- always false for OpenMP.

    OpenMP does have a team -- the thread team -- and constructs every member
    must reach, but they are *directives* (`#pragma omp barrier`), not routines,
    and directives are out of this corpus's scope. What the runtime library
    exposes is per-thread: inquiries (omp_get_thread_num), runtime-state
    setters, locks, allocators and the device-memory routines, any of which one
    thread may call alone. Stated rather than defaulted, for the same reason as
    CUDA's.
    """
    return Confident(False, "pattern",
                     "OpenMP: the runtime library is per-thread -- its team-wide constructs are "
                     "directives, not routines, and are out of this corpus's scope")


def _execute_once(function_key):
    """execution.execute_once -- always false for OpenMP.

    The OpenMP runtime library has no initialization or finalization routine
    at all: the runtime starts implicitly and the `omp_init_*` names are
    lock, allocator and mempartitioner constructors, each called as many
    times as the program has objects. Nothing here is a process-lifetime
    singleton.
    """
    return Confident(False, "pattern",
                     "OpenMP: the runtime has no init/finalize entry point -- omp_init_* are lock "
                     "and allocator constructors, callable once per object, not once per process")


def _variants(function_key, all_function_keys):
    if function_key.endswith("_async"):
        base = function_key[: -len("_async")]
        if base in all_function_keys:
            return {"blocking": Confident(base, "pattern", "OpenMP _async-suffix naming convention")}
    elif function_key + "_async" in all_function_keys:
        return {"nonblocking": Confident(function_key + "_async", "pattern", "OpenMP _async-suffix naming convention")}
    return None


def _parameters(function_key, entry):
    out = []
    for p in entry["parameters"]:
        is_ptr = is_pointer_param(p)
        kind = parameter_kind(p.get("name"), is_ptr, function_key)
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


def classify_openmp(entries):
    """entries: {function_key: full syntactic entry} for model=="openmp".
    Returns list[(ir_dict, flags_list)], mirroring Extract adapters' shape.
    """
    all_keys = set(entries)
    results = []
    for function_key, entry in entries.items():
        # Rank and team-size queries, per function -- see heuristics._RETURN_VALUE_KINDS.
        value_kind = return_value_kind(function_key, entry["return"]["kind"])
        value_kind = Confident(value_kind, "pattern", "rank/team-size query, listed per function") if value_kind else None
        ir = {
            "model": "openmp",
            "function_key": function_key,
            "identity.api_group": _api_group(function_key),
            "execution.blocking": _blocking(function_key),
            "execution.execute_once": _execute_once(function_key),
            "execution.collective": _collective(function_key),
            "execution.launch": None,          # host/device callability is not in the declaration -- see docstring
            "execution.gpu_scope": None,
            "execution.stages": None,          # no MPI-4-style init/start/complete/free taxonomy
            "execution.procedure_class": None,
            "semantics.atomic": None,          # no atomic routines; atomics are directives in OpenMP
            "relationships.variants": _variants(function_key, all_keys),
            "return.value_kind": value_kind,
            "parameters": _parameters(function_key, entry),
            "flags": [],
        }
        results.append((ir, ir["flags"]))
    return results
