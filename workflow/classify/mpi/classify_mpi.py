"""
MPI's Heuristic Classification module: workflow/classify/heuristics.py's shared
primitives plus MPI-specific naming judgment (I-prefix/`_init`-suffix for
procedure_class/stages/relationships.variants, MPI's own two-function atomic
name pair, MPI's collective/one_sided/point_to_point name conventions).

Grounded directly in the real corpus (instances/0_syntactic-api.json's 571 MPI
entries, inspected while writing this) -- see docs/workflow/
workflow/README.md for the per-field heuristic table this
implements. api_group in particular is deliberately conservative: it only
fires on unambiguous name conventions (one-sided's Put/Get/Win_*/Accumulate
family, collective's operation-name substrings, point-to-point's
send/recv/probe substrings) and leaves everything else -- including most of
query and management -- null rather than guess.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from common.ir import Confident, unwrap  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from heuristics import (
    kind_from_c_type,  # noqa: E402
    mpi_procedure_class_and_stages, MPI_ATOMIC_NAME_MAP,
    mpi_nonblocking_by_name,
    parameter_kind, return_value_kind, is_pointer_param,
)

# execution.launch is a scope constant here, not a per-function naming guess
# -- the same reasoning NCCL's own _LAUNCH_CPU already used, applied to the
# PPM it was equally true of. MPI is a host-side API: every routine the
# standard defines is callable only from host code. This was previously left
# null with the rationale "no __host__/__device__ qualifier signal in MPI's
# source", which is precisely the reading docs/schema/field-semantics.md
# rejects -- null must mean genuinely undetermined, not "the source had no
# qualifier to read". 560 of 571 MPI entries were null on that basis
# (audited 2026-07-21); the other 11 already said "cpu" via the supplement,
# so the corpus also disagreed with itself.
_LAUNCH_CPU = Confident(
    "cpu", "static",
    "MPI is a host-side API -- every routine in the standard is host-callable only, "
    "independent of any qualifier being present in the source to read it off",
)

_ONE_SIDED_NAMES = frozenset({
    "mpi_put", "mpi_get", "mpi_rput", "mpi_rget",
    "mpi_accumulate", "mpi_raccumulate",
    "mpi_get_accumulate", "mpi_rget_accumulate",
    "mpi_compare_and_swap", "mpi_fetch_and_op",
})

# RMA epoch and completion calls. These move no data themselves, but they are
# what makes a one-sided epoch well-formed, so they belong to the one-sided
# group with the Put/Get/Accumulate calls they bracket.
#
# This set replaces a blanket `function_key.startswith("mpi_win_")` rule
# (2026-07-21, second full-corpus audit). "mpi_win_" is the handle prefix, not
# an operation marker: of the corpus's 47 mpi_win_* entries only these 15 are
# one-sided in any sense. The other 32 are ordinary handle lifecycle
# (mpi_win_create, mpi_win_free, mpi_win_set_info), inquiry (mpi_win_get_group,
# mpi_win_c2f) or callback typedefs, and calling them one_sided told
# assign.py they might need a shape when in fact no formal layer applies to
# them at all -- the same class of error the api_group nulls were causing.
_WIN_EPOCH_NAMES = frozenset({
    "mpi_win_fence", "mpi_win_lock", "mpi_win_lock_all", "mpi_win_unlock",
    "mpi_win_unlock_all", "mpi_win_post", "mpi_win_start", "mpi_win_complete",
    "mpi_win_wait", "mpi_win_test", "mpi_win_sync", "mpi_win_flush",
    "mpi_win_flush_all", "mpi_win_flush_local", "mpi_win_flush_local_all",
})

_COLLECTIVE_SUBSTRINGS = ("bcast", "reduce", "scatter", "gather", "alltoall", "barrier", "scan")
_P2P_SUBSTRINGS = ("send", "recv", "probe")

# Process-lifetime singletons -- literal, not substring-based, since these are
# the only two functions this applies to and a substring match risks false
# positives elsewhere in a 571-function corpus. Found missing while reviewing
# the pilot corpus:
# neither matches any of the three substring families above, so both were
# silently null with nothing to backstop them.
_MANAGEMENT_NAMES = frozenset({"mpi_init", "mpi_finalize"})

# Pure local inquiries into an already-established communicator -- same
# finding-2 provenance as _MANAGEMENT_NAMES above. Kept literal for the same
# reason: "query" is genuinely ambiguous as a general substring rule (e.g.
# would mpi_type_size, mpi_get_count belong here too? -- not checked, not
# claimed here), so only the two functions finding 2 actually named are
# covered, rather than guessing at siblings.
_QUERY_NAMES = frozenset({"mpi_comm_rank", "mpi_comm_size"})

# Request-completion primitives -> the "synchronization" api_group value
# (mpi_wait was one of the 5 functions that grounded it -- docs/cross-ppm-analysis/known-gaps-and-open-questions.md's
# resolved row). Literal set covering the full wait/test sibling family
# (structurally identical completion calls on one-or-more requests, confirmed
# against the corpus: exactly these 8 exist). mpi_test_cancelled is
# deliberately EXCLUDED -- it inspects a status object without progressing or
# completing anything (closer to query), so classifying it here would be a
# forced fit; left null, same conservatism as _QUERY_NAMES above.
_SYNCHRONIZATION_NAMES = frozenset({
    "mpi_wait", "mpi_waitall", "mpi_waitany", "mpi_waitsome",
    "mpi_test", "mpi_testall", "mpi_testany", "mpi_testsome",
})


# Language-interop handle conversions (MPI_Comm_c2f, MPI_Status_f082c,
# MPI_Type_fromint, ...). Pure local translations of a handle between the C
# and Fortran representations -- they touch no remote state, allocate nothing,
# and complete nothing. 52 entries.
_HANDLE_CONVERSION_SUFFIXES = ("_c2f", "_f2c", "_c2f08", "_f082c", "_f2f08", "_f082f", "_toint", "_fromint")

# Inquiry verbs. "_get_" as an infix rather than a prefix specifically so
# mpi_get / mpi_get_accumulate (RMA) never reach here -- they match the
# one_sided rule at the top of _api_group anyway, but the infix form makes
# that independent of rule order.
_INQUIRY_SUFFIXES = ("_size", "_rank", "_count", "_compare", "_commutative", "_test_inter",
                     "_is_revoked", "_neighbors", "_neighbors_count", "_coords", "_map",
                     "_translate_ranks", "_get_status", "_string", "_class", "_extent",
                     "_get", "_query_thread", "_initialized", "_finalized")
_INQUIRY_LITERALS = frozenset({
    "mpi_get_address", "mpi_get_count", "mpi_get_elements", "mpi_get_elements_x",
    "mpi_get_library_version", "mpi_get_processor_name", "mpi_get_version",
    "mpi_get_hw_resource_info", "mpi_topo_test", "mpi_test_cancelled",
    "mpi_is_thread_main", "mpi_query_thread", "mpi_initialized", "mpi_finalized",
    "mpi_error_class", "mpi_error_string", "mpi_aint_add", "mpi_aint_diff",
    "mpi_sizeof", "mpi_pack_size", "mpi_pack_external_size", "mpi_cartdim_get",
    "mpi_graphdims_get", "mpi_lookup_name",
})

# Lifecycle verbs -- creating, destroying, configuring or registering a handle
# or resource. Matched as a whole trailing word or an infix word, never as a
# bare substring, so "mpi_comm_create_keyval" and "mpi_type_create_darray"
# both match on "create" while a name that merely contains those letters does
# not.
_LIFECYCLE_VERBS = (
    "create", "dup", "delete", "commit", "alloc", "set", "split", "open", "close",
    "attach", "detach", "join", "connect", "accept", "disconnect", "spawn",
    "init", "finalize", "register", "revoke", "abort", "publish_name",
    "unpublish_name", "ack_failed", "merge", "incl", "excl", "union",
    "intersection", "difference", "start", "stop", "reset", "sub", "changed",
)


def _is_handle_conversion(function_key):
    return function_key.endswith(_HANDLE_CONVERSION_SUFFIXES)


# Names that LOOK like inquiries by suffix but are lifecycle calls. Checked
# before _is_inquiry, and found by spot-checking this rule set's own output
# rather than by assuming it was right: mpi_add_error_class and
# mpi_add_error_string end in "_class"/"_string" and were being called query,
# but they mint a new error class/string rather than translate an existing
# one. (mpi_error_class/mpi_error_string, which do translate, stay query --
# the pair is the whole reason a suffix rule alone can't decide this.)
_LIFECYCLE_PREFIXES = ("mpi_add_error_", "mpi_remove_error_")

# Type constructors in their MPI-1 spelling, which carry no "create" the way
# their MPI-2 mpi_type_create_* siblings do, plus a few one-off lifecycle and
# inquiry names with no shared affix to key on.
_LIFECYCLE_LITERALS = frozenset({
    "mpi_type_contiguous", "mpi_type_indexed", "mpi_type_vector",
    "mpi_attr_put", "mpi_startall",
})
_EXTRA_INQUIRY_LITERALS = frozenset({
    "mpi_comm_group", "mpi_comm_remote_group", "mpi_type_size_x",
    "mpi_wtime", "mpi_wtick",
})


def _is_inquiry(function_key):
    if function_key.startswith(_LIFECYCLE_PREFIXES) or function_key in _LIFECYCLE_LITERALS:
        return False
    if function_key in _INQUIRY_LITERALS or function_key in _EXTRA_INQUIRY_LITERALS:
        return True
    if "_get_" in function_key and not function_key.startswith("mpi_get"):
        return True
    return function_key.endswith(_INQUIRY_SUFFIXES)


def _api_group(function_key):
    if function_key in _ONE_SIDED_NAMES or function_key in _WIN_EPOCH_NAMES:
        return Confident("one_sided", "pattern",
                         "MPI one-sided data operation (Put/Get/Accumulate) or RMA epoch/completion call")
    if any(s in function_key for s in _COLLECTIVE_SUBSTRINGS):
        return Confident("collective", "pattern", "MPI collective-operation name substring")
    if any(s in function_key for s in _P2P_SUBSTRINGS):
        return Confident("point_to_point", "pattern", "MPI point-to-point name substring (send/recv/probe)")
    if function_key in _SYNCHRONIZATION_NAMES:
        return Confident("synchronization", "pattern", "MPI request-completion function name (Wait*/Test* family)")
    if function_key in _MANAGEMENT_NAMES:
        return Confident("management", "pattern", "MPI process-lifetime singleton (Init/Finalize)")
    if function_key in _QUERY_NAMES:
        return Confident("query", "pattern", "MPI local-inquiry function name (Comm_rank/Comm_size)")
    # Handle-destructor family (mpi_comm_free, mpi_win_free_keyval, mpi_free_mem,
    # ...) -- checked last, as a fallback, so it never overrides an
    # already-firing rule above (mpi_win_free, e.g., keeps matching the
    # mpi_win_ one_sided prefix rule unchanged). Grounded against the full
    # corpus: every "_free"-containing MPI function name is a handle/memory
    # teardown call, none is a data-moving or query operation (checked via
    # grep against instances/1_syntactic-semantics-api.json while adding this).
    if "free" in function_key:
        return Confident("management", "pattern", "MPI handle/memory-destructor name convention (*_free*)")


    # Handle lifecycle and handle inquiry (2026-07-21, second full-corpus
    # audit). 391 of 571 MPI entries -- 68% -- were reaching null here, which
    # is what made Generate Formal escalate 47 mpi_file_*, 39 mpi_comm_*, 31
    # mpi_type_* and 27 mpi_win_* entries as "needs a new shape" when in fact
    # none of them will ever carry a formal layer: assign.py resolves
    # query/management to no_formal_applicable, and they were only escaping
    # that route because api_group was null. This is the same
    # conservative-literals problem _QUERY_NAMES documents above ("would
    # mpi_type_size, mpi_get_count belong here too? -- not checked"), now
    # checked: they do.
    #
    # Both rules run AFTER every rule above, so nothing already classified
    # changes -- mpi_get/mpi_put keep one_sided, mpi_bcast keeps collective.
    if _is_handle_conversion(function_key) or _is_inquiry(function_key):
        return Confident("query", "pattern",
                         "MPI handle-inquiry/conversion name convention (*_get_*, *_size, *_compare, *_c2f/f2c/toint/fromint)")
    if (function_key.startswith(_LIFECYCLE_PREFIXES) or function_key in _LIFECYCLE_LITERALS
            or any(function_key.endswith(v) or f"_{v}_" in function_key for v in _LIFECYCLE_VERBS)):
        return Confident("management", "pattern",
                         "MPI handle-lifecycle name convention (create/dup/delete/commit/alloc/set/attach/open/...)")

    # "io": the mpi_file_* family. None of the other three PPMs has a
    # file interface, so this stays MPI-local rather than moving into
    # workflow/classify/heuristics.py.
    #
    # Ordered as a FALLBACK, like the *_free* rule above it and the handle
    # rules below, rather than first. Running it first was tried and rejected:
    # it is a blunt prefix, so it also swallowed 16 entries already correctly
    # classified as query (mpi_file_get_amode, the c2f/f2c converters) and 8
    # as management (mpi_file_open/close/delete). Those are genuinely a query
    # and a lifecycle call that happen to act on a file handle -- "operates on
    # a file" is not the same claim as "is an I/O operation", and the more
    # specific answer is the more useful one for a consumer asking what the
    # call DOES. As a fallback it claims exactly the 40 entries nothing else
    # had an answer for.
    if function_key.startswith("mpi_file_"):
        return Confident("io", "pattern", "MPI file-I/O interface (the mpi_file_* family), no more specific rule matched")
    return None


def _procedure_class_and_stages(function_key, all_function_keys):
    proc_class, stages = mpi_procedure_class_and_stages(function_key, all_function_keys)
    if proc_class is None:
        return None, None
    affix = "I-prefix" if proc_class == "nb-op" else "_init suffix"
    reason = (f"MPI-4 procedure-taxonomy naming convention ({affix}), "
              "confirmed against a counterpart function present in the corpus")
    return Confident(proc_class, "pattern", reason), Confident(stages, "pattern", reason)


def _atomic(function_key):
    """Returns a full 3-key dict or None -- never a partially-null one.

    mpi_fetch_and_op's `operation` is a runtime MPI_Op argument, not encoded
    in the function name -- statically undeterminable, while `fetch`/`compare`
    both follow from the name. `semantics.atomic.operation` is nullable for
    exactly this case
    (null = runtime-parameterized via an OPERATION-kind parameter -- see the
    schema's own field description), so the object is now emitted in full
    with operation=null, still never *partially* populated.
    """
    hit = MPI_ATOMIC_NAME_MAP.get(function_key)
    if hit is None:
        return None
    op, fetch, compare = hit
    reason = f"MPI atomic function name ({function_key})"
    if op is None:
        op_reason = (f"{function_key}: reduction operator is a runtime MPI_Op argument -- "
                     "operation=null ('runtime-parameterized'), fetch/compare from the name")
        return {
            "operation": Confident(None, "pattern", op_reason),
            "fetch": Confident(fetch, "pattern", op_reason),
            "compare": Confident(compare, "pattern", op_reason),
        }
    return {
        "operation": Confident(op, "pattern", reason),
        "fetch": Confident(fetch, "pattern", reason),
        "compare": Confident(compare, "pattern", reason),
    }


# The point-to-point half of the persistent families -- see _blocking below
# for why the split matters. Enumerated rather than derived from
# identity.api_group so this rule does not silently inherit that heuristic's
# own failures; checked against the corpus (2026-09-13), these seven are
# exactly the p-op/pp-op entries api_group calls point_to_point.
_PERSISTENT_POINT_TO_POINT = frozenset({
    "mpi_send_init", "mpi_bsend_init", "mpi_rsend_init", "mpi_ssend_init",
    "mpi_recv_init", "mpi_psend_init", "mpi_precv_init",
})


def _blocking(function_key, proc_class, all_function_keys):
    """execution.blocking, read off MPI 4.1 §2.4's own definition.

    The standard defines the axis exhaustively and by complement: "An MPI
    procedure is *nonblocking* if it is incomplete and local"; "An MPI
    procedure is *blocking* if it is not nonblocking". So the work here is
    recognizing the nonblocking set; everything else is blocking by that
    definition, not by assumption.

    The standard's own worked list (chap-terms/terms-2.tex, the
    "categorization examples" advice block) is what settles the two cases a
    naive reading gets wrong, and both are worth stating because both
    contradict what a downstream consumer might expect:

      - **MPI_SEND_INIT and MPI_RECV_INIT are listed as nonblocking**
        ("incomplete and local"), alongside MPI_ISEND and MPI_IRECV. A
        persistent init call returns long before anything is transferred.
      - **MPI_BCAST_INIT is listed as blocking** ("incomplete and nonlocal")
        -- the initialization procedure of a *collective* persistent
        operation is nonlocal, so it fails the "and local" half even though
        it is equally incomplete.

    That is the whole reason this cannot be a one-line promotion of
    procedure_class: `p-op` covers both, and they fall on opposite sides.
    MPI_PSEND_INIT/MPI_PRECV_INIT (`pp-op`) are partitioned point-to-point
    and follow the point-to-point half.

    The remaining arms:
      - `nb-op` -> nonblocking, the Forum's own classification.
      - the one-sided data-movement family (_ONE_SIDED_NAMES, reused from
        _api_group) -> nonblocking. Every one of them is incomplete and
        local in exactly §2.4's sense: the transfer completes at the
        enclosing window's next synchronization (MPI_Win_fence/_unlock/
        _wait, or the MPI_Wait on the request the MPI_R* forms hand back),
        never at return. They carry no procedure_class -- the Forum's
        taxonomy covers point-to-point and collective operations -- and no
        I-marker, so nothing else here would reach them.
      - the segment-`I` families the procedure_class taxonomy does not reach
        (MPI_Comm_idup, MPI_File_iread*, MPI_*_iflush*) -> nonblocking, via
        heuristics.mpi_nonblocking_by_name's counterpart-existence test.
      - everything else -> blocking. This includes both the completing
        procedures (MPI_Send, MPI_Bcast, MPI_Wait) and the procedures the
        standard calls "not MPI operation-related" at all (MPI_Comm_rank,
        MPI_Wtime, MPI_Test, MPI_Start): they leave no operation of their
        own running, so "not nonblocking" is the right reading of each.
    """
    if proc_class == "nb-op":
        return Confident(False, "pattern",
                         "MPI 4.1 §2.4: nonblocking procedure (procedure_class nb-op)")
    if proc_class in ("p-op", "pp-op"):
        if function_key in _PERSISTENT_POINT_TO_POINT:
            return Confident(False, "pattern",
                             "MPI 4.1 §2.4 lists MPI_SEND_INIT/MPI_RECV_INIT as nonblocking "
                             "(incomplete and local) -- a persistent point-to-point init returns "
                             "before the operation is started")
        return Confident(True, "pattern",
                         "MPI 4.1 §2.4 lists MPI_BCAST_INIT as blocking (incomplete and *nonlocal*) "
                         "-- the init procedure of a collective persistent operation is nonlocal")
    if function_key in _ONE_SIDED_NAMES:
        return Confident(False, "pattern",
                         "MPI one-sided data movement: completes at the window's next "
                         "synchronization, not at return")
    counterpart = mpi_nonblocking_by_name(function_key, all_function_keys)
    if counterpart is not None:
        return Confident(False, "pattern",
                         f"MPI I-marker naming convention (the nonblocking form of {counterpart})")
    return Confident(True, "pattern",
                     "MPI 4.1 §2.4: blocking is the complement -- no nonblocking marker, no "
                     "outstanding operation left at return")


# MPI's world model is the one place across the six standards where the
# standard *forbids* a second call -- see _execute_once for why that matters
# and why no other PPM has a member here.
_EXECUTE_ONCE_NAMES = frozenset({"mpi_init", "mpi_init_thread", "mpi_finalize"})


# MPI procedures that are collective but are NOT in the collective-communication
# chapter, so identity.api_group never sees them. Every member is grounded in a
# statement the standard makes about it, and the four blanket statements below
# are what make the list defensible rather than a guess (audited 2026-09-13):
#
#   * chap-context, "Communicator Constructors": "The following are collective
#     functions that are invoked by all MPI processes in the group or groups
#     associated with comm, with the exception of MPI_COMM_CREATE_GROUP,
#     MPI_COMM_CREATE_FROM_GROUP, and MPI_INTERCOMM_CREATE_FROM_GROUPS" -- and
#     those three are collective too, over the *new* communicator's group, which
#     is still "all of a team" and so still true here.
#   * chap-one-side, "Initialization": "MPI provides the following window
#     initialization functions: MPI_WIN_CREATE, MPI_WIN_ALLOCATE,
#     MPI_WIN_ALLOCATE_SHARED, and MPI_WIN_CREATE_DYNAMIC, which are collective
#     over the group of an intra-communicator".
#   * chap-topol: "These topology creation functions are collective" (Cart_create,
#     Graph_create, Dist_graph_create_adjacent, Dist_graph_create); MPI_CART_SUB
#     "is collective over the input communicator's group".
#   * chap-io, table:io:dataaccess: the data-access table has an explicit
#     "collective" column, and these 22 names are exactly its contents.
#
# Explicit negatives the standard states, kept out on purpose: "MPI_WIN_LOCK_ALL
# and MPI_WIN_UNLOCK_ALL are not collective calls" (chap-one-side), and the
# sessions model is deliberately local -- its own rationale contrasts
# MPI_SESSION_FINALIZE with MPI_FINALIZE precisely on this axis.
_COLLECTIVE_NAMES = frozenset({
    # Communicator constructors, destructor, info, inter-communicator operations
    "mpi_comm_dup", "mpi_comm_dup_with_info", "mpi_comm_idup",
    "mpi_comm_idup_with_info", "mpi_comm_create", "mpi_comm_create_group",
    "mpi_comm_split", "mpi_comm_split_type", "mpi_comm_create_from_group",
    "mpi_comm_free", "mpi_comm_set_info",
    "mpi_intercomm_create", "mpi_intercomm_create_from_groups", "mpi_intercomm_merge",
    # Window creation, destruction, info, fence
    "mpi_win_create", "mpi_win_allocate", "mpi_win_allocate_shared",
    "mpi_win_create_dynamic", "mpi_win_free", "mpi_win_set_info", "mpi_win_fence",
    # Topology creation
    "mpi_cart_create", "mpi_graph_create", "mpi_dist_graph_create",
    "mpi_dist_graph_create_adjacent", "mpi_cart_sub",
    # Dynamic process management
    "mpi_comm_spawn", "mpi_comm_spawn_multiple", "mpi_comm_accept",
    "mpi_comm_connect", "mpi_comm_disconnect",
    # World-model initialization and finalization
    "mpi_init", "mpi_init_thread", "mpi_finalize",
    # File management
    "mpi_file_open", "mpi_file_close", "mpi_file_set_size",
    "mpi_file_preallocate", "mpi_file_set_info", "mpi_file_set_view",
    "mpi_file_set_atomicity", "mpi_file_sync", "mpi_file_seek_shared",
    # Collective data access -- table:io:dataaccess's own "collective" column
    "mpi_file_read_at_all", "mpi_file_write_at_all",
    "mpi_file_iread_at_all", "mpi_file_iwrite_at_all",
    "mpi_file_read_at_all_begin", "mpi_file_read_at_all_end",
    "mpi_file_write_at_all_begin", "mpi_file_write_at_all_end",
    "mpi_file_read_all", "mpi_file_write_all",
    "mpi_file_iread_all", "mpi_file_iwrite_all",
    "mpi_file_read_all_begin", "mpi_file_read_all_end",
    "mpi_file_write_all_begin", "mpi_file_write_all_end",
    "mpi_file_read_ordered", "mpi_file_write_ordered",
    "mpi_file_read_ordered_begin", "mpi_file_read_ordered_end",
    "mpi_file_write_ordered_begin", "mpi_file_write_ordered_end",
})

# The one api_group == "collective" entry that is not a collective procedure.
# MPI_REDUCE_LOCAL is defined in chap-coll's "MPI Process-Local Reduction"
# subsection -- "The following function applies a reduction operator to local
# arguments" -- and communicates with nobody; identity.api_group's name-substring
# heuristic catches it on "reduce". Caught by auditing that heuristic's output
# against the chapter rather than promoting it wholesale.
_NOT_COLLECTIVE_NAMES = frozenset({"mpi_reduce_local"})


def _collective(function_key, api_group):
    """execution.collective -- "every process in the team must call this".

    MPI states the definition outright (4.1 §2.4): "An MPI procedure is
    collective if all processes in a group or groups of MPI processes need to
    invoke the procedure." Unlike `blocking`, the standard marks nothing in
    the symbol, so this is the collective-communication chapter (which
    identity.api_group already recognizes) plus an enumerated set drawn from
    the standard's own per-section statements -- see _COLLECTIVE_NAMES.
    """
    if function_key in _NOT_COLLECTIVE_NAMES:
        return Confident(False, "pattern",
                         "MPI 5.1 chap-coll, 'MPI Process-Local Reduction': applies a reduction "
                         "operator to local arguments and communicates with no other process")
    if function_key in _COLLECTIVE_NAMES:
        return Confident(True, "pattern",
                         "MPI 5.1 states this procedure is collective (communicator/window/topology "
                         "construction, file management, or the data-access table's collective column)")
    if api_group == "collective":
        return Confident(True, "pattern",
                         "MPI 5.1 Collective Communication: invoked by all processes of the group "
                         "associated with the communicator")
    return Confident(False, "pattern",
                     "MPI 5.1 §2.4: collective is the complement -- no statement in the standard "
                     "requires all processes of a group to invoke this procedure")


def _execute_once(function_key):
    """execution.execute_once -- "may be called at most once per process".

    That is the criterion docs/schema/field-semantics.md states, and it is
    narrower than "is the library's init/finalize bracket". MPI is the only
    one of the six standards whose text actually forbids the second call:

      "MPI cannot be initialized more than once; and MPI cannot be
       reinitialized after MPI_FINALIZE has been called."
       -- MPI 5.1, chap-dynamic/dynamic-2.tex:873 (The Sessions Model,
          listing the world model's limitations)

    and MPI_FINALIZE is itself once-only by the same chapter's

      "Once MPI_FINALIZE returns, no MPI procedure may be called in the
       world model (not even MPI_INIT, ...)"     -- dynamic-2.tex:588

    MPI_INIT_THREAD is the world model's other initialization procedure and
    is covered by the same sentence, which says "MPI", not "MPI_INIT".

    **The sessions model is deliberately not here.** The same section adds:
    "In the Sessions model, MPI resources can be allocated and freed multiple
    times in an MPI process." So this has to be a literal set, never an
    `_init`-suffix rule -- and the `_init` suffix in MPI overwhelmingly means
    persistent-operation initialization (mpi_bcast_init, mpi_send_init, ...),
    which is neither.

    Queries about the state (mpi_initialized, mpi_finalized) are ordinary
    procedures and may be called freely; they are false here.

    **Do not wire up the Forum's own attribute of this name.** The vendored
    apis.json carries `attributes.execute_once`, and it is `false` for all
    571 entries -- MPI_Init included. It is a document-rendering flag with
    nothing to do with this axis; inheriting it would produce an all-false
    column that looks authoritative. test_emit.py asserts against that.
    """
    if function_key in _EXECUTE_ONCE_NAMES:
        return Confident(True, "pattern",
                         "MPI 5.1, Process Initialization, Creation, and Management: the world "
                         "model cannot be initialized more than once, and no MPI procedure may "
                         "be called once MPI_FINALIZE has returned")
    return Confident(False, "pattern",
                     "MPI: not a world-model initialization or finalization procedure -- no "
                     "once-per-process restriction in the standard")


def _variants(function_key, all_function_keys):
    """I-prefix/_init-suffix naming, but finding a *related* function's
    name in the same corpus rather than classifying the current function --
    only ever points at a name that's actually present, never fabricated.
    """
    variants = {}
    if function_key.startswith("mpi_i") and not function_key.startswith("mpi_init"):
        base = "mpi_" + function_key[len("mpi_i"):]
        if base in all_function_keys:
            variants["blocking"] = Confident(base, "pattern", "MPI I-prefix naming convention")
    elif function_key.endswith("_init"):
        base = function_key[: -len("_init")]
        if base in all_function_keys:
            variants["blocking"] = Confident(base, "pattern", "MPI _init-suffix naming convention")
    else:
        nb = "mpi_i" + function_key[len("mpi_"):]
        if nb in all_function_keys:
            variants["nonblocking"] = Confident(nb, "pattern", "MPI I-prefix naming convention")
        persistent = function_key + "_init"
        if persistent in all_function_keys:
            variants["persistent"] = Confident(persistent, "pattern", "MPI _init-suffix naming convention")
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


def classify_mpi(entries):
    """entries: {function_key: full syntactic entry} for model=="mpi".
    Returns list[(ir_dict, flags_list)], mirroring Extract adapters' shape.
    """
    all_keys = set(entries)
    results = []
    for function_key, entry in entries.items():
        # Rank and team-size queries, per function -- see heuristics._RETURN_VALUE_KINDS.
        value_kind = return_value_kind(function_key, entry["return"]["kind"])
        value_kind = Confident(value_kind, "pattern", "rank/team-size query, listed per function") if value_kind else None
        flags = []
        proc_class, stages = _procedure_class_and_stages(function_key, all_keys)
        api_group = _api_group(function_key)
        ir = {
            "model": "mpi",
            "function_key": function_key,
            "identity.api_group": api_group,
            "execution.blocking": _blocking(function_key, unwrap(proc_class)[0], all_keys),
            "execution.execute_once": _execute_once(function_key),
            "execution.collective": _collective(function_key, unwrap(api_group)[0]),
            "execution.launch": _LAUNCH_CPU,
            "execution.gpu_scope": None,  # not applicable outside NVSHMEM's device-scope naming convention
            "execution.stages": stages,
            "execution.procedure_class": proc_class,
            "semantics.atomic": _atomic(function_key),
            "relationships.variants": _variants(function_key, all_keys),
            "return.value_kind": value_kind,
            "parameters": _parameters(function_key, entry),
            "flags": flags,
        }
        results.append((ir, ir["flags"]))
    return results
