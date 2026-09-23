"""
NCCL's Heuristic Classification module. NCCL has no atomic-operation family, no
I-prefix/`_init` procedure taxonomy, and no `_block`/`_warp` device-scope
naming (this v1-scope corpus is entirely NCCL's host API -- nccl_device.h
is out of scope) -- so this module only ever
touches api_group, execution.launch (a scope constant, not a per-function
guess), and parameters[].kind/.constraints.not_null.

Function names are camelCase (ncclAllReduce, ncclSend, ...), unlike MPI/
SHMEM/NVSHMEM's lowercase_underscore convention -- every substring check
here lower()s first.

Grounded in the real corpus (instances/0_syntactic-api.json's 63 NCCL
entries -- small enough to have read every name while writing this).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from common.ir import Confident  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from heuristics import kind_from_c_type, parameter_kind, return_value_kind, is_pointer_param, takes_cuda_stream  # noqa: E402

_COLLECTIVE_SUBSTRINGS = ("allgather", "allreduce", "alltoall", "bcast", "broadcast", "gather", "reduce", "scatter")
_P2P_SUBSTRINGS = ("send", "recv")
_ONE_SIDED_SUBSTRINGS = ("put", "win", "signal")
_MANAGEMENT_SUBSTRINGS = ("comm", "group", "memalloc", "memfree", "redopcreate", "redopdestroy", "param")
_QUERY_SUBSTRINGS = ("geterrorstring", "getlasterror", "getuniqueid", "getversion")

# --- 2026-07-21 full-corpus audit: the substring families above are far too
# coarse on their own, and their ORDER made it worse. "comm" and "param" swept
# every ncclComm*/ncclParam* name into management regardless of what the call
# does, and "win"/"signal" swept window registration and signal waiting into
# one_sided. 20 of NCCL's 63 entries were misfiled -- management became a
# dumping ground and one_sided collected calls that move no data at all.
#
# Rather than widen the substring lists (which would just move the collisions
# around), the specific families below are matched FIRST, as literal names or
# tightly-anchored patterns, and only what falls through reaches the coarse
# rules. Every name here was checked against the vendored header signature in
# external-inputs/nccl/.../include/nccl.h.

# Inquiries: an input handle plus a single out-pointer the call fills in.
# ncclComm* inquiries (Count/UserRank/CuDevice/GetAsyncError/MemStats) are
# NOT lifecycle management, and the whole ncclParamGet*/ncclParamDumpAll
# family reads configuration rather than changing it.
_QUERY_NAMES = frozenset({
    "nccluserrank", "ncclcommcount", "ncclcommuserrank", "ncclcommcudevice",
    "ncclcommgetasyncerror", "ncclcommmemstats", "ncclwingetuserptr",
})
_QUERY_PREFIXES = ("ncclparamget", "ncclparamdump")

# Registering/deregistering a window is handle lifecycle, not a data-moving
# one-sided operation -- the "win" substring alone cannot tell the two apart.
_MANAGEMENT_NAMES = frozenset({
    "ncclcommwindowregister", "ncclcommwindowderegister",
    "ncclcommregister", "ncclcommderegister",
})

# Signalling and waiting on a signal are synchronization primitives; only
# ncclPutSignal actually carries a payload, and it stays one_sided.
_SYNCHRONIZATION_NAMES = frozenset({"ncclsignal", "ncclwaitsignal"})

# execution.launch is a scope constant here, not a per-function naming
# guess: Extract's v1 scope for NCCL is nccl.h (the host API) only, never
# nccl_device.h -- every function currently in the corpus is structurally
# host-callable, confirmed by direct inspection. "static" confidence -- like Extract's own docs-matched
# desc fields -- because this isn't a guess about one function, it's a
# guaranteed fact about what Extract's scope could possibly have ingested.
_LAUNCH_CPU = Confident("cpu", "static", "NCCL v1 Extract scope is host-API headers only (nccl.h); no device-side function could be present")


def _api_group(function_key):
    lkey = function_key.lower()

    # Specific families first -- see the comment block above for why order
    # matters here and what each of these rescues from a coarse rule below.
    if lkey in _QUERY_NAMES or lkey.startswith(_QUERY_PREFIXES):
        return Confident("query", "pattern",
                         "NCCL inquiry: takes an input handle and fills a single out-pointer, rather "
                         "than creating/destroying anything (checked against the header signature)")
    if lkey in _MANAGEMENT_NAMES:
        return Confident("management", "pattern",
                         "NCCL buffer/window registration -- handle lifecycle, not a data-moving "
                         "one-sided operation")
    if lkey in _SYNCHRONIZATION_NAMES:
        return Confident("synchronization", "pattern",
                         "NCCL signal/wait primitive -- carries no payload, so synchronization rather "
                         "than one_sided")

    if any(s in lkey for s in _QUERY_SUBSTRINGS):
        return Confident("query", "pattern", "NCCL query-function name substring")
    if any(s in lkey for s in _COLLECTIVE_SUBSTRINGS):
        return Confident("collective", "pattern", "NCCL collective-operation name substring")
    if any(s in lkey for s in _P2P_SUBSTRINGS):
        return Confident("point_to_point", "pattern", "NCCL point-to-point name substring (send/recv)")
    if any(s in lkey for s in _ONE_SIDED_SUBSTRINGS):
        return Confident("one_sided", "pattern", "NCCL one-sided/window name substring (put/win/signal)")
    if any(s in lkey for s in _MANAGEMENT_SUBSTRINGS):
        return Confident("management", "pattern", "NCCL comm/group-lifecycle name substring")
    return None


def _blocking(entry):
    """execution.blocking from NCCL's stream argument.

    NCCL's completion model is CUDA's, and the signal is in the signature:
    a call that takes a `cudaStream_t` enqueues its work on that stream and
    returns, so it is complete only when the caller synchronizes the stream
    -- exactly what `completion: "stream_ordered"` is
    for. A call without one (ncclCommInitRank, ncclCommDestroy,
    ncclGroupStart/End, ncclMemAlloc/MemFree, the error-string and version
    queries) does its work before it returns.

    This splits the corpus 14/49 and reproduces all 7 `blocking: false`
    values curated/supplement/supplement-nccl.json had set by hand, plus the
    4 `true` ones, without exception.

    Worth flagging for consumers: it makes every NCCL collective and
    ncclSend/ncclRecv NONBLOCKING. Tools that treat a collective's
    blocking-ness as part of its matching identity will see NCCL
    collectives change side. That is the stream-ordered semantics NCCL
    actually has, not a reclassification of convenience.
    """
    if takes_cuda_stream(entry):
        return Confident(False, "pattern",
                         "NCCL: takes a cudaStream_t -- stream-ordered, complete only when the "
                         "caller synchronizes that stream")
    return Confident(True, "pattern",
                     "NCCL: no stream argument -- the call does its work before it returns")


# NCCL's collective set, from the statements its own API documentation makes
# (external-inputs/nccl/docs/2.30/api/): "It is a collective function that must
# be called by all participating ranks in the newly created communicator"
# (ncclCommInitRankConfig, ncclCommInitRankScalable, ncclCommShrink),
# "ncclCommSplit is a collective function", ncclCommGrow "must be called by both
# existing ranks ... and new ranks", ncclCommDestroy "is an intra-node collective
# call, which all ranks on the same node should call to avoid a hang", and
# ncclCommWindowRegister's "Since this is a collective call, every rank in the
# communicator needs ...". The collective communication operations themselves
# are collective by construction -- the user guide's "to be called for each rank
# (hence CUDA device), using the same count and the same datatype, to form a
# complete collective operation".
#
# Three documented negatives kept out on purpose (audited 2026-09-13):
# ncclCommInitAll is the "single process version ... convenience function" one
# thread calls for every device; ncclCommWindowDeregister's "Deregistration is
# local to the rank"; and ncclGroupStart/ncclGroupEnd are thread-local brackets
# rather than participation in anything. ncclCommFinalize is the one name taken
# from an adjacent statement rather than its own: ncclCommDestroy is documented
# collective and "will call ncclCommFinalize internally", so a program calling
# it explicitly does on every rank what Destroy would have.
_COLLECTIVE_NAMES = frozenset({
    "ncclAllGather", "ncclAllReduce", "ncclAlltoAll", "ncclBcast",
    "ncclBroadcast", "ncclGather", "ncclReduce", "ncclReduceScatter",
    "ncclScatter",
    "ncclCommInitRank", "ncclCommInitRankConfig", "ncclCommInitRankScalable",
    "ncclCommSplit", "ncclCommShrink", "ncclCommGrow",
    "ncclCommDestroy", "ncclCommFinalize", "ncclCommWindowRegister",
})


def _collective(function_key):
    """execution.collective -- "every rank in the communicator must call this".

    Wider than the collective *operations*: NCCL's communicator lifecycle is
    collective too, which is why ncclCommSplit and ncclCommDestroy sit here next
    to ncclAllReduce. ncclSend/ncclRecv are point-to-point and stay out.
    """
    if function_key in _COLLECTIVE_NAMES:
        return Confident(True, "pattern",
                         "NCCL 2.30: documented as a collective call that every rank in the "
                         "communicator must make")
    return Confident(False, "pattern",
                     "NCCL 2.30: not documented as collective -- point-to-point, thread-local, or "
                     "a per-rank query")


def _execute_once(function_key):
    """execution.execute_once -- always false for NCCL.

    NCCL has no process-lifetime singleton to mark. Its initialization is
    per-*communicator*, not per-process: ncclCommInitRank/InitAll/
    InitRankConfig build a communicator object, an application may hold
    several at once, and ncclCommDestroy/ncclCommFinalize tear down one of
    them. Calling ncclCommInitRank a second time is ordinary use of the API,
    not an error.
    """
    return Confident(False, "pattern",
                     "NCCL: initialization is per-communicator, not per-process -- an application "
                     "may create and destroy several communicators, so nothing here is restricted "
                     "to one call per process")


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


def classify_nccl(entries):
    """entries: {function_key: full syntactic entry} for model=="nccl".
    Returns list[(ir_dict, flags_list)], mirroring Extract adapters' shape.
    """
    results = []
    for function_key, entry in entries.items():
        # Rank and team-size queries, per function -- see heuristics._RETURN_VALUE_KINDS.
        value_kind = return_value_kind(function_key, entry["return"]["kind"])
        value_kind = Confident(value_kind, "pattern", "rank/team-size query, listed per function") if value_kind else None
        ir = {
            "model": "nccl",
            "function_key": function_key,
            "identity.api_group": _api_group(function_key),
            "execution.blocking": _blocking(entry),
            "execution.execute_once": _execute_once(function_key),
            "execution.collective": _collective(function_key),
            "execution.launch": _LAUNCH_CPU,
            "execution.gpu_scope": None,       # no device-scope naming convention in the host-API-only corpus
            "execution.stages": None,          # no MPI-4-style init/start/complete/free taxonomy in NCCL
            "execution.procedure_class": None,
            "semantics.atomic": None,          # NCCL has no atomic-operation family
            "relationships.variants": None,    # no recognized variant-naming convention in NCCL
            "return.value_kind": value_kind,
            "parameters": _parameters(function_key, entry),
            "flags": [],
        }
        results.append((ir, ir["flags"]))
    return results
