"""
OpenSHMEM's Heuristic Classification module. SHMEM's naming conventions differ
from MPI's in ways that change which heuristics apply at all: SHMEM has no
two-sided messaging (no point_to_point api_group at all -- OpenSHMEM is
one-sided-only), no I-prefix/`_init` nonblocking/persistent taxonomy, but
does have its own real nonblocking-variant naming convention (a `_nbi`
suffix on the atomics family), and a rich, mechanically-recognizable typed-
atomics suffix convention (shmem_ctx_int32_atomic_compare_swap, etc.) that
MPI doesn't have at all.

Grounded in the real corpus (instances/0_syntactic-api.json's 1608 SHMEM
entries, inspected while writing this -- 458 atomic-named functions cover
the full SHMEM_ATOMIC_SUFFIX_MAP operation set) -- see docs/workflow/
workflow/README.md.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from common.ir import Confident  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from heuristics import (
    kind_from_c_type,  # noqa: E402
    shmem_atomic_op_from_name, parameter_kind, return_value_kind, is_pointer_param,
    shmem_nonblocking_immediate, shmem_synchronization_name,
)

# execution.launch is a scope constant here, not a per-function naming guess
# -- see classify_mpi._LAUNCH_CPU's own comment for the full reasoning, which
# applies unchanged. OpenSHMEM is a host-side API; the device-callable
# PGAS surface belongs to NVSHMEM, which is a separate model in this corpus
# with its own real per-function qualifier signal to read. 1541 of 1608
# SHMEM entries were null on the rejected "no qualifier in the source"
# rationale (audited 2026-07-21).
_LAUNCH_CPU = Confident(
    "cpu", "static",
    "OpenSHMEM is a host-side API -- the standard defines no device-callable routine, "
    "independent of any qualifier being present in the source to read it off",
)

_ONE_SIDED_SUBSTRINGS = ("put", "get", "atomic")
_COLLECTIVE_SUBSTRINGS = ("broadcast", "collect", "alltoall", "reduce", "barrier", "sync")
_QUERY_NAMES = frozenset({"shmem_my_pe", "shmem_n_pes", "shmem_pe_accessible", "shmem_ptr", "shmem_addr_accessible",
                          # 2026-07-21 full-corpus audit: these are inquiries whose names happen to
                          # contain a data-movement substring, so without an explicit entry here the
                          # coarse _ONE_SIDED_SUBSTRINGS rule below claims them. shmem_ctx_get_team
                          # returns the team a context belongs to -- it moves no data and touches no
                          # remote PE; the "get" in its name is ordinary English, not an RMA get.
                          "shmem_ctx_get_team", "shmem_team_get_config", "shmem_team_my_pe",
                          "shmem_team_n_pes", "shmem_team_translate_pe"})
# "malloc"/"free"/"calloc"/"align" added 2026-07-17 after reviewing the pilot
# corpus --
# symmetric-heap lifecycle calls (shmem_malloc, shmem_free, shmem_calloc,
# shmem_align, shmem_malloc_with_hints) matched none of the original
# substrings and were silently null. Confirmed against the real corpus that
# each of these four substrings matches only the intended heap-management
# functions (no other SHMEM name contains them).
_MANAGEMENT_SUBSTRINGS = ("init", "finalize", "_create", "_destroy", "global_exit", "malloc", "free", "calloc", "align")

# 2026-07-21, second full-corpus audit. 30 SHMEM function families were still
# null, and every one of them is a real data-movement, synchronization or
# lifecycle call that the substring rules above simply cannot see:
#
#   - The single-element RMA pair. shmem_{T}_p / shmem_{T}_g (and their ctx_
#     forms) write and read exactly one element, so their names contain
#     neither "put" nor "get" -- a one-letter verb defeats a substring rule.
#   - The pre-1.4 atomics. shmem_{T}_add/inc/set/swap/cswap/fadd/finc/fetch
#     are the original spellings of what 1.4 renamed shmem_{T}_atomic_*, so
#     they lack the "atomic" substring that classifies their modern synonyms.
#     They are the same operations on the same memory.
#   - The signal family. shmem_signal_add/set/fetch and the ctx_ forms write
#     a remote signal word -- one-sided by the same reasoning as a put.
#
# Anchored as exact names or full-suffix matches rather than substrings,
# because these verbs are short enough to appear inside unrelated names.
_ONE_SIDED_SUFFIXES = ("_p", "_g", "_add", "_inc", "_set", "_swap", "_cswap",
                       "_fadd", "_finc", "_fetch")
_ONE_SIDED_NAME_PARTS = ("signal_add", "signal_set", "signal_fetch")

# Distributed lock operations -- shmem_set_lock blocks until the lock is
# acquired, shmem_clear_lock releases it, shmem_test_lock attempts it without
# blocking. All three are synchronization, and shmem_test_lock in particular
# is already called out in shmem_synchronization_name's own comment as
# deliberately excluded from the completion-poll family -- excluded from
# *that* family, but it still belongs to this group.
_LOCK_NAMES = frozenset({"shmem_set_lock", "shmem_clear_lock", "shmem_test_lock"})

# shmem_wait is the deprecated, always-blocking predecessor of
# shmem_wait_until (no cmp operator; waits for the value to change).
_EXTRA_SYNCHRONIZATION_NAMES = frozenset({"shmem_wait"})

_EXTRA_MANAGEMENT_NAMES = frozenset({
    "shmem_realloc", "shmem_team_split_2d", "shmem_team_split_strided",
    "shmem_team_ptr", "shmem_ctx_session_start", "shmem_ctx_session_stop",
    "shmem_pcontrol",
    # The SHMEM 1.0 initialization call, superseded by shmem_init.
    "start_pes",
})
_EXTRA_QUERY_NAMES = frozenset({"shmem_query_thread"})


def _api_group(function_key):
    if function_key in _QUERY_NAMES or function_key in _EXTRA_QUERY_NAMES or function_key.endswith("_query"):
        return Confident("query", "pattern", "SHMEM query-function name convention")
    if function_key in _LOCK_NAMES or function_key in _EXTRA_SYNCHRONIZATION_NAMES:
        return Confident("synchronization", "pattern", "SHMEM distributed-lock / deprecated-wait name")
    if function_key in _EXTRA_MANAGEMENT_NAMES:
        return Confident("management", "pattern", "SHMEM context/team/heap lifecycle name")
    # "synchronization" (fence/quiet/wait_until/_test point-poll family;
    # shmem_test_lock is excluded by the anchored regex -- it's a lock
    # acquisition attempt, not a completion poll). Checked before
    # management/collective/one_sided so shmem_signal_wait_until never falls
    # through to a data-moving group. (shmem_quiet/shmem_{T}_wait_until were
    # 2 of the 5 functions that grounded the new enum value -- see
    # known-gaps-and-open-questions.md's resolved row.)
    if shmem_synchronization_name(function_key):
        return Confident("synchronization", "pattern", "SHMEM local-synchronization name convention (fence/quiet/wait_until/_test)")
    if any(s in function_key for s in _MANAGEMENT_SUBSTRINGS):
        return Confident("management", "pattern", "SHMEM lifecycle/management name substring")
    if any(s in function_key for s in _COLLECTIVE_SUBSTRINGS):
        return Confident("collective", "pattern", "SHMEM collective-operation name substring")
    if any(s in function_key for s in _ONE_SIDED_SUBSTRINGS):
        return Confident("one_sided", "pattern", "SHMEM one-sided/atomic name substring (put/get/atomic)")
    if function_key.endswith(_ONE_SIDED_SUFFIXES) or any(s in function_key for s in _ONE_SIDED_NAME_PARTS):
        return Confident("one_sided", "pattern",
                         "SHMEM single-element RMA (_p/_g), pre-1.4 atomic spelling, or remote signal write")
    return None


def _blocking(function_key):
    """execution.blocking from OpenSHMEM's `_nbi` convention.

    OpenSHMEM splits the axis exactly one way and names it in the symbol:
    an `_nbi` ("nonblocking implicit") routine initiates the transfer and
    returns immediately, its completion observable only through
    shmem_quiet/shmem_fence, while every other routine in the standard --
    RMA, atomics, collectives, locks, the wait_until/test polls, heap and
    team management -- returns only once its own local effect is done.
    There is no third case and no unmarked nonblocking routine, which is
    what makes the complement arm a reading of the standard rather than a
    default.

    The two borderline-looking families are both genuinely blocking on this
    definition and are worth naming because a reader may expect otherwise:
    `shmem_fence` returns once the ordering point is established (it does
    not wait for delivery, but establishing it *is* its local effect --
    curated/supplement/supplement-nvshmem.json said `true` for
    nvshmem_fence by hand, for the same reason), and `shmem_test`/
    `shmem_test_lock` return once they have produced their answer.
    """
    if shmem_nonblocking_immediate(function_key):
        return Confident(False, "pattern",
                         "OpenSHMEM _nbi suffix: initiates the transfer and returns, "
                         "completion observable only via shmem_quiet/shmem_fence")
    return Confident(True, "pattern",
                     "OpenSHMEM: no _nbi suffix -- the routine returns once its own local "
                     "effect is complete (the standard marks every nonblocking routine)")


def _atomic(function_key):
    hit = shmem_atomic_op_from_name(function_key)
    if hit is None:
        return None
    op, fetch, compare = hit
    reason = f"SHMEM typed-atomics suffix convention ({function_key})"
    return {
        "operation": Confident(op, "pattern", reason),
        "fetch": Confident(fetch, "pattern", reason),
        "compare": Confident(compare, "pattern", reason),
    }


# OpenSHMEM's collective set, read off the standard's own per-routine content
# files: external-inputs/shmem/tex/shmem-standard/content/ has one .tex per
# routine, and 20 of the 101 carry an explicit collective statement ("The
# shmem_malloc routine is a collective operation on the world team", "team-based
# broadcast routines are collective routines over a valid team", ...). Derived
# by scanning those files and mapping each back through the Extract adapter to
# the entries it defines, then audited by hand (2026-09-13). Three adjustments
# the raw scan gets wrong, each checked against the text:
#
#   * shmem_ctx_session_start and shmem_global_exit are excluded -- both say
#     "is a NON-collective routine", which a keyword scan reads as a hit.
#   * shmem_barrier_all, shmem_sync_all and shmem_init_thread are added -- all
#     three are collective ("blocks the PE until all other PEs arrive"; the
#     initialization pair is described together in shmem_init.tex) but their
#     files never use the word.
#   * shmem_team_create_ctx stays out on the standard's own statement that
#     "the context creation operation is not collective".
_COLLECTIVE_NAMES = frozenset({
    "shmem_align", "shmem_alltoall32", "shmem_alltoall64", "shmem_alltoallmem",
    "shmem_alltoalls32", "shmem_alltoalls64", "shmem_alltoallsmem",
    "shmem_barrier", "shmem_barrier_all", "shmem_broadcast32",
    "shmem_broadcast64", "shmem_broadcastmem", "shmem_calloc",
    "shmem_collect32", "shmem_collect64", "shmem_collectmem",
    "shmem_fcollect32", "shmem_fcollect64", "shmem_fcollectmem",
    "shmem_finalize", "shmem_free", "shmem_init", "shmem_init_thread",
    "shmem_malloc", "shmem_malloc_with_hints", "shmem_realloc", "shmem_sync",
    "shmem_sync_all", "shmem_team_destroy", "shmem_team_split_2d",
    "shmem_team_split_strided", "shmem_team_sync", "shmem_{T}_alltoall",
    "shmem_{T}_alltoalls", "shmem_{T}_and_reduce", "shmem_{T}_and_to_all",
    "shmem_{T}_broadcast", "shmem_{T}_collect", "shmem_{T}_fcollect",
    "shmem_{T}_max_reduce", "shmem_{T}_max_to_all", "shmem_{T}_min_reduce",
    "shmem_{T}_min_to_all", "shmem_{T}_or_reduce", "shmem_{T}_or_to_all",
    "shmem_{T}_prod_reduce", "shmem_{T}_prod_to_all", "shmem_{T}_sum_exscan",
    "shmem_{T}_sum_inscan", "shmem_{T}_sum_reduce", "shmem_{T}_sum_to_all",
    "shmem_{T}_xor_reduce", "shmem_{T}_xor_to_all", "start_pes",
})


def _collective(function_key):
    """execution.collective -- "every PE in the team must call this".

    Note what this is *not*: it is not "is a collective communication
    routine". The symmetric heap is the clearest case -- shmem_malloc,
    shmem_free, shmem_calloc, shmem_align and shmem_realloc are allocation
    calls with identity.api_group == "management", and every one of them is
    "a collective operation on the world team" in the standard's own words,
    because the heap is symmetric and every PE has to agree on its layout.
    Any rule that promoted api_group == "collective" and stopped there would
    get all five wrong; see _COLLECTIVE_NAMES for how the set was derived.
    """
    if function_key in _COLLECTIVE_NAMES:
        return Confident(True, "pattern",
                         "OpenSHMEM 1.5: the routine's own content file states it is collective "
                         "(over a team, an active set, or the world team)")
    return Confident(False, "pattern",
                     "OpenSHMEM 1.5: no collective statement in the routine's own content file -- "
                     "a PE may call this without any other PE doing so")


def _execute_once(function_key):
    """execution.execute_once -- always false for OpenSHMEM.

    The criterion is "may be called at most once per process"
    (docs/schema/field-semantics.md), not "is the library's init/finalize
    bracket", and OpenSHMEM explicitly permits the repeat:

      "The shmem_init and shmem_init_thread initialization routines may be
       called multiple times within an OpenSHMEM program. A corresponding
       call to shmem_finalize must be made for each call to an OpenSHMEM
       initialization routine. The OpenSHMEM library must not be finalized
       until after the last call to shmem_finalize and may be re-initialized
       with a subsequent call to an initialization routine."
       -- OpenSHMEM 1.5, content/shmem_init.tex

    So shmem_init/shmem_init_thread/shmem_finalize are false here, and
    OpenSHMEM has no once-per-process routine at all. This **deviates from
    the two hand-written supplement values** (shmem_init and shmem_finalize
    were `true`, method=general_knowledge, with the note "same reasoning as
    mpi_init") -- that was an analogy to MPI rather than a reading of this
    standard, and the standard says the opposite in as many words. MPI is
    the only one of the six whose text forbids the second call; see
    classify_mpi._execute_once.

    shmem_global_exit is not a candidate either: the standard calls it "a
    non-collective routine that allows any one PE to force termination"
    (content/shmem_global_exit.tex) -- one PE, any number of times.
    """
    return Confident(False, "pattern",
                     "OpenSHMEM 1.5 (shmem_init.tex): the initialization routines may be called "
                     "multiple times and the library re-initialized, so no OpenSHMEM routine is "
                     "restricted to one call per process")


def _variants(function_key, all_function_keys):
    """SHMEM's real nonblocking-variant naming convention: a trailing
    `_nbi` on the atomics family (e.g. ..._atomic_fetch_add_nbi vs.
    ..._atomic_fetch_add) -- only ever points at a name actually present.
    """
    variants = {}
    if function_key.endswith("_nbi"):
        base = function_key[: -len("_nbi")]
        if base in all_function_keys:
            variants["blocking"] = Confident(base, "pattern", "SHMEM _nbi-suffix naming convention")
    else:
        nb = function_key + "_nbi"
        if nb in all_function_keys:
            variants["nonblocking"] = Confident(nb, "pattern", "SHMEM _nbi-suffix naming convention")
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


def classify_shmem(entries):
    """entries: {function_key: full syntactic entry} for model=="shmem".
    Returns list[(ir_dict, flags_list)], mirroring Extract adapters' shape.
    """
    all_keys = set(entries)
    results = []
    for function_key, entry in entries.items():
        # Rank and team-size queries, per function -- see heuristics._RETURN_VALUE_KINDS.
        value_kind = return_value_kind(function_key, entry["return"]["kind"])
        value_kind = Confident(value_kind, "pattern", "rank/team-size query, listed per function") if value_kind else None
        ir = {
            "model": "shmem",
            "function_key": function_key,
            "identity.api_group": _api_group(function_key),
            "execution.blocking": _blocking(function_key),
            "execution.execute_once": _execute_once(function_key),
            "execution.collective": _collective(function_key),
            "execution.launch": _LAUNCH_CPU,
            "execution.gpu_scope": None,  # not applicable outside NVSHMEM's device-scope naming convention
            "execution.stages": None,     # SHMEM has no MPI-4-style init/start/complete/free taxonomy
            "execution.procedure_class": None,
            "semantics.atomic": _atomic(function_key),
            "relationships.variants": _variants(function_key, all_keys),
            "return.value_kind": value_kind,
            "parameters": _parameters(function_key, entry),
            "flags": [],
        }
        results.append((ir, ir["flags"]))
    return results
