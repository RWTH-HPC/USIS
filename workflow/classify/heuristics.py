"""
Shared, PPM-agnostic naming/co-located-flag primitives for Heuristic
Classification, Classify Semantics' mechanical component (docs/workflow/
workflow/README.md).

Each function here is a pure string/dict -> guess-or-None transform, with no
PPM branching of its own -- the per-PPM classify_<ppm>.py modules decide
*when* to call these (MPI's I-prefix means something structurally different
from NVSHMEM's device-scope suffix, so which signal applies to which
function is a per-PPM judgment, kept in the per-PPM module, not here).

Every function returns either a plain guessed value (the caller wraps it in
workflow.common.ir.Confident with a reason) or None ("this signal doesn't
apply / had nothing to go on" -- the caller decides whether that's worth a
`note` flag). None of these ever raises a Flag directly -- flag-raising
stays in the per-PPM modules and emit.py, next to the code that knows *why*,
matching Extract's own established convention.
"""

import re

# curated/schemas/api-schema.json $defs/semantics_atomic -- the 14 allowed operation
# values, and (fetch, compare) for each. Keys here are the SHMEM/NVSHMEM
# `..._atomic_<key>` name-suffix convention (after stripping a trailing
# "_nbi", which only marks the nonblocking-immediate variant and carries no
# operation information of its own).
SHMEM_ATOMIC_SUFFIX_MAP = {
    "add": ("add", False, False),
    "fetch_add": ("fetch_add", True, False),
    "and": ("and", False, False),
    "fetch_and": ("fetch_and", True, False),
    "or": ("or", False, False),
    "fetch_or": ("fetch_or", True, False),
    "xor": ("xor", False, False),
    "fetch_xor": ("fetch_xor", True, False),
    "inc": ("inc", False, False),
    "fetch_inc": ("fetch_inc", True, False),
    "set": ("set", False, False),
    # Plain "swap"/"compare_swap" have no separate "fetch_swap"/"fetch_cswap"
    # spelling in SHMEM's naming convention or in the schema's own operation
    # enum -- both inherently return the previous value, so fetch=True is a
    # naming-convention inference (flagged low_confidence by the caller),
    # not a literal read.
    "swap": ("swap", True, False),
    "compare_swap": ("cswap", True, True),
    # Bare "atomic_fetch" (no operation suffix at all) is itself the "fetch"
    # operation -- a pure atomic read, matching the schema's own "fetch"
    # enum value.
    "fetch": ("fetch", True, False),
}

_ATOMIC_SUFFIX_RE = re.compile(r"atomic_([a-z_]+?)(?:_nbi)?$")


def shmem_atomic_op_from_name(function_key):
    """"shmem_ctx_int32_atomic_compare_swap" -> ("cswap", True, True), or
    None if the name has no atomic_<suffix> tail this map recognizes."""
    m = _ATOMIC_SUFFIX_RE.search(function_key)
    if not m:
        return None
    return SHMEM_ATOMIC_SUFFIX_MAP.get(m.group(1))


# MPI's atomic-operation family isn't suffix-based like SHMEM/NVSHMEM's typed
# atomics -- it's two specifically-named functions. Grounded directly in the
# real corpus (curated/schemas/../instances/0_syntactic-api.json): mpi_accumulate and
# its r*/get_* siblings are semantics.one_sided (operation="accumulate"), a
# different sub-object entirely -- not semantics.atomic. Only these two are.
MPI_ATOMIC_NAME_MAP = {
    "mpi_compare_and_swap": ("cswap", True, True),
    # MPI_Fetch_and_op's actual reduction operator is a *runtime* MPI_Op
    # argument, not encoded in the function name -- operation cannot be
    # determined statically here (an honest gap, not a guess), but "it
    # fetches, and it isn't a compare" both follow directly from the name.
    "mpi_fetch_and_op": (None, True, False),
}


# MPI-4 procedure taxonomy (execution.stages / execution.procedure_class):
# I-prefix -> nonblocking, "_init" suffix -> persistent. Partitioned
# persistent ops (MPI_Psend_init/MPI_Precv_init) are a distinct enum value
# ("pp-op") from plain persistent ops ("p-op") and would be silently
# misclassified by the generic "_init" suffix rule, so they're checked
# first as an explicit literal exception -- grounded in the real corpus
# (mpi_psend_init/mpi_precv_init are the only two functions matching this).
MPI_PARTITIONED_INIT_NAMES = frozenset({"mpi_psend_init", "mpi_precv_init"})


def mpi_procedure_class_and_stages(function_key, all_function_keys=None):
    """function_key -> (procedure_class, stages) or (None, None).

    Conservative by design: only fires on evidence that is actually in the
    corpus. It does NOT default everything else to "b-op" -- most MPI
    functions (mpi_comm_rank, mpi_init, mpi_type_commit, ...) aren't
    operations with a blocking/nonblocking/persistent axis at all, and
    guessing "b-op" for them would be exactly the kind of forced fit this
    project's philosophy rejects.

    `all_function_keys` (the corpus's own key set) is what keeps the two
    naming signals honest, and passing it is strongly preferred -- see the
    counterpart-existence rule below. It is optional only so the shared
    primitive stays callable in isolation; omitting it restores the older,
    name-only behaviour and its false positives.

    **The counterpart-existence rule (fixed 2026-07-21).** Both signals are
    *relative* naming conventions, not absolute ones: MPI's I-prefix means
    "the nonblocking form of MPI_<verb>", and the `_init` suffix means "the
    persistent form of MPI_<verb>". Neither says anything at all unless that
    `<verb>` is a real function. Matching on the affix alone misread 21 of
    the corpus's 571 MPI functions (audited 2026-07-21):

      - 19 false `nb-op`s, because "starts with mpi_i" caught every name
        whose *own* first letter is i rather than a nonblocking marker --
        the entire `mpi_info_*` family (15), `mpi_intercomm_*` (3), and
        `mpi_is_thread_main`.
      - 2 false `p-op`s, because "ends with _init" caught the two functions
        that *are* an initialization rather than the persistent form of
        something -- `mpi_init` itself and `mpi_session_init`. `mpi_init`
        additionally got `stages: ["i"]` out of this, next to an
        `execution.completion` of "c" that contradicted it.

    Requiring the counterpart to actually exist in the corpus removes all 21
    without suppressing a single true positive (every real I-prefix/`_init`
    function in the corpus has its base form present). This is the same
    discipline `classify_mpi._variants` already applies -- only ever name a
    function that is actually there, never one the convention implies should
    be.

    **The blocking base form (added 2026-07-21).** The counterpart-existence
    rule runs in both directions, and only one of them was being used. If
    `mpi_ibcast` is in the corpus, that is exactly as much evidence that
    `mpi_bcast` is the *blocking* form as it is that `mpi_ibcast` is the
    nonblocking one -- the convention is a statement about the pair. Reading
    it in one direction only left 27 blocking base forms at `null` next to
    their own nonblocking and persistent variants (`mpi_allgather` null,
    `mpi_iallgather` nb-op, `mpi_allgather_init` p-op), and disagreed with
    the five b-op values `curated/supplement/supplement-mpi.json` already carried by
    hand. This still fires on corpus evidence only, never on a bare name:
    a function with no I-prefixed and no `_init` counterpart present stays
    `null`, which is what keeps `mpi_comm_rank` and friends out.

    **stages.** Derived from procedure_class, per MPI-4's own taxonomy and
    docs/schema/field-semantics.md: a blocking call does all four stages in
    the one call, a nonblocking call initializes and starts (its matching
    MPI_Wait does the completing and freeing), and a persistent call's
    `_init` form only initializes. `nb-op` previously returned `None` here,
    contradicting the `["i", "s"]` the supplement carried for `mpi_isend`.
    """
    if function_key in MPI_PARTITIONED_INIT_NAMES:
        return "pp-op", ["i"]

    def _present(base):
        # No corpus to check against -> fall back to the affix alone.
        return all_function_keys is None or base in all_function_keys

    if function_key.endswith("_init") and function_key.startswith("mpi_"):
        if _present(function_key[: -len("_init")]):
            return "p-op", ["i"]
        return None, None
    if function_key.startswith("mpi_i") and not function_key.startswith("mpi_init"):
        if _present("mpi_" + function_key[len("mpi_i"):]):
            return "nb-op", ["i", "s"]
        return None, None
    # No affix of its own -> it may still be the base form some *other*
    # function's affix refers to. Only checkable against a real corpus.
    if function_key.startswith("mpi_") and all_function_keys is not None:
        nonblocking = "mpi_i" + function_key[len("mpi_"):]
        persistent = function_key + "_init"
        if nonblocking in all_function_keys or persistent in all_function_keys:
            return "b-op", ["i", "s", "c", "f"]
    return None, None


_GPU_SCOPE_SUFFIXES = (("_block", "block"), ("_warp", "warp"), ("_thread", "thread"))


def nvshmem_gpu_scope_from_name(function_key):
    """NVSHMEM's device-scope naming convention (e.g. a "_block" suffix on
    a cooperative-group collective). Included for completeness/future-
    proofing even though it fires zero times against the *current* corpus:
    Extract's scope excludes NVSHMEM's device-side extension headers entirely, so no
    function in instances/0_syntactic-api.json actually carries this suffix
    yet. If device-side functions are ever added to Extract's scope, this
    heuristic starts firing without any change needed here.
    """
    for suffix, scope in _GPU_SCOPE_SUFFIXES:
        if function_key.endswith(suffix):
            return scope
    return None


# execution.blocking ---------------------------------------------------------
#
# The three shared primitives below answer one question -- "does this call
# leave an operation running after it returns?" -- for the naming conventions
# more than one PPM uses. The per-PPM decision itself (including each PPM's
# default arm) lives in that PPM's own classify_<ppm>.py, because the default
# is a statement about that standard, not a shared convention.
#
# Why a *default* arm is legitimate here, when this file's other heuristics
# deliberately refuse to guess (mpi_procedure_class_and_stages' docstring
# argues at length against defaulting everything to "b-op"): `blocking` is a
# required, NON-nullable boolean in api-schema.json, and each of the four
# standards defines the axis exhaustively rather than leaving it open. MPI
# 4.1 §2.4 is explicit -- "An MPI procedure is *nonblocking* if it is
# incomplete and local" and "*blocking* if it is not nonblocking" -- so
# "blocking" is the closed complement of a recognizable set, not a guess
# about the remainder. procedure_class has no such complement rule (a
# function with no blocking/nonblocking/persistent axis at all is genuinely
# null, not "b-op"), which is why that one still refuses and this one does
# not.


def mpi_nonblocking_by_name(function_key, all_function_keys):
    """The counterpart of an MPI nonblocking procedure, or None.

    MPI's `I` marker ("incomplete"/"immediate", MPI 4.1 §2.4) is a *segment*
    prefix, not a name prefix: it attaches to the verb, wherever the verb
    sits in the name. `MPI_Isend` carries it in the first segment,
    `MPI_Comm_idup`, `MPI_File_iread_at_all` and `MPI_Session_iflush_buffer`
    in a later one. mpi_procedure_class_and_stages only reads the first
    segment (`mpi_i...`), which is correct for the MPI-4 procedure_class
    taxonomy it implements -- the Forum's own apis.json assigns `nb-op` to
    exactly those -- but it means 15 genuinely nonblocking procedures carry
    no signal there at all.

    Same counterpart-existence discipline as everything else here: the
    convention is a statement about a *pair*, so `mpi_comm_idup` is evidence
    of nothing unless `mpi_comm_dup` is really in the corpus. Returns the
    counterpart's key (truthy) so a caller can cite it.

    Validated against the whole MPI corpus (2026-09-13): 47 matches, no
    false positives, and the 32 entries the MPI Forum's own apis.json marks
    `nb-op` are all 32 among them -- so this agrees with the Forum
    everywhere the Forum has an opinion, and extends it to the 15 (the
    `MPI_Comm_idup*`, `MPI_File_i{read,write}*` and `MPI_*_iflush*`
    families) where it has none.
    """
    parts = function_key.split("_")
    for i in range(1, len(parts)):
        if len(parts[i]) > 1 and parts[i][0] == "i":
            counterpart = "_".join(parts[:i] + [parts[i][1:]] + parts[i + 1:])
            if counterpart in all_function_keys:
                return counterpart
    return None


def shmem_nonblocking_immediate(function_key):
    """OpenSHMEM/NVSHMEM's `_nbi` ("nonblocking implicit") suffix.

    The one naming convention both PGAS models share for this axis, and the
    only one either standard defines: an `_nbi` routine initiates the
    transfer and returns, its completion observable only through
    shmem_quiet/shmem_fence; every other RMA routine in both standards
    returns with the local buffer reusable. Suffix-anchored deliberately --
    across both corpora no name carries `_nbi` anywhere but the tail
    (checked 2026-09-13), and the same anchoring is already what
    classify_shmem._variants and classify_nvshmem._variants use to pair a
    routine with its blocking form.
    """
    return function_key.endswith("_nbi")


def takes_cuda_stream(entry):
    """True iff the declaration takes a `cudaStream_t` argument.

    For NCCL this is the syntactic marker of stream-ordered semantics, and
    so of a call that returns before the work it enqueued has run: every
    collective and ncclSend/ncclRecv takes a stream, while ncclCommInitRank,
    ncclGroupStart/End, the allocators and the queries do not.

    **Not a valid blocking signal for CUDA itself** (found 2026-09-13, after
    trying it): CUDA owns the stream type, so ~20 of its routines take a
    `cudaStream_t` to *operate on that stream* rather than to enqueue onto
    it -- cudaStreamCreateWithPriority takes an out-pointer to one, and
    cudaStreamSynchronize takes one by value. NCCL has no stream-management
    surface at all, which is exactly why the same signature check is sound
    there and not here. classify_cuda._blocking enumerates CUDA's
    asynchronous families from api-sync-behavior.md instead.

    Reads two places because the two Extract adapters populate different
    ones: the CUDA adapter parses declarations into parameters[].binding_type.c,
    while the NCCL adapter leaves per-parameter types null and keeps the
    declaration verbatim in bindings.c.signature. Both are checked so the
    primitive stays usable from either adapter's output.
    """
    for param in entry.get("parameters") or []:
        if "cudaStream_t" in ((param.get("binding_type") or {}).get("c") or ""):
            return True
    return "cudaStream_t" in (((entry.get("bindings") or {}).get("c") or {}).get("signature") or "")


def is_pointer_param(param):
    """True/False/None -- whether a parameter is a pointer type.

    Two signals, checked in the order each PPM's Extract adapter actually
    populates them (confirmed against the real corpus): SHMEM/NCCL/NVSHMEM
    populate parameters[].pointer directly and completely (100% non-null in
    the current corpus); MPI leaves it null almost always (54+16 populated
    out of 2781) but populates binding_type.c as a literal C fragment 100%
    of the time, so a "*" substring check is the fallback there. Returns
    None only when neither signal is available at all.
    """
    if param.get("pointer") is not None:
        return param["pointer"]
    c = (param.get("binding_type") or {}).get("c")
    if c:
        return "*" in c
    return None


# Name -> parameters[].kind, for the cases where the name alone (regardless
# of pointer-ness) is unambiguous across all 4 PPMs' real corpora.
_KIND_NAME_MAP = {
    "comm": "COMMUNICATOR", "newcomm": "COMMUNICATOR", "ctx": "COMMUNICATOR",
    "datatype": "DATATYPE", "sendtype": "DATATYPE", "recvtype": "DATATYPE",
    "request": "REQUEST", "req": "REQUEST",
    "status": "STATUS",
    "win": "WINDOW", "window": "WINDOW",
    "team": "TEAM", "parent_team": "TEAM",
    # 2026-09-14: the remaining team handles, all OpenSHMEM/NVSHMEM with no C
    # binding type for kind_from_c_type to read -- shmem_team_split_strided's
    # new_team ("An OpenSHMEM team handle"), shmem_team_split_2d's
    # xaxis_team/yaxis_team ("A new PE team handle"), and
    # shmem_team_translate_pe's src_team/dest_team, plus the NVSHMEM
    # counterparts of all three. 10 parameters, every "*_team" name that was
    # still null.
    "new_team": "TEAM", "xaxis_team": "TEAM", "yaxis_team": "TEAM",
    "src_team": "TEAM", "dest_team": "TEAM",
    "tag": "TAG",
    "key": "KEY",
    "ierror": "ERROR_CODE",
    "op": "OPERATION",
    # SIG_OP: the OpenSHMEM/NVSHMEM *_put_signal
    # family's signal operator, "Signal operator that represents the type of
    # update to be performed" on the signal. Its values are the signal-update
    # constants, a domain disjoint from OPERATION's MPI_Op / ncclRedOp_t /
    # reduction constants, and a consumer dispatching on OPERATION would take
    # it for one of those. 172 parameters.
    "sig_op": "SIG_OP",
    # THREAD_LEVEL: a thread-support level (MPI_THREAD_SINGLE ..
    # MPI_THREAD_MULTIPLE; OpenSHMEM's and NVSHMEM's SHMEM_THREAD_* levels).
    # Every corpus instance of these three names is one: "desired level of
    # thread support" / "provided level of thread support" (mpi_init_thread,
    # mpi_query_thread, mpi_t_init_thread), "The thread level support
    # requested by the user" / "... provided by the OpenSHMEM implementation"
    # (shmem/nvshmem _init_thread and _query_thread). 11 parameters. The
    # other level-valued parameters (verbosity, cb_safety) are not thread
    # levels and stay null.
    "required": "THREAD_LEVEL", "requested": "THREAD_LEVEL", "provided": "THREAD_LEVEL",
    # DEVICE: a device number (ordinal), by value or written through an
    # int* -- CUDA's "Device number to query", "Returned device ordinal",
    # "Source device"/"Destination device", "Peer device to enable direct
    # access to"; OpenMP's device_num/dev and the src_/dst_device_num of the
    # omp_target_memcpy family; ncclCommCuDevice's device. 69 parameters.
    # Deliberately NOT the arrays of devices (OpenMP's devs, NCCL's devlist,
    # CUDA's device_arr) -- DEVICE is scalar, the same exclusion that keeps
    # "periods" out of BOOL -- nor ndevs (a count), deviceFlags (flags), or
    # device_ptr/devPtr (memory).
    "device": "DEVICE", "peerdevice": "DEVICE", "srcdevice": "DEVICE", "dstdevice": "DEVICE",
    "dev": "DEVICE", "device_num": "DEVICE", "src_device_num": "DEVICE", "dst_device_num": "DEVICE",
    # "stream" is unambiguous across the corpus
    # (every instance is a cudaStream_t -- NCCL's collectives/p2p, NVSHMEM's
    # *_on_stream variants); "commid" is ncclCommInitRank's ncclUniqueId, the
    # function that grounded the ID kind. "argv" is MPI_Init's char*** --
    # an array-of-strings the implementation may read and prune, i.e. a
    # BUFFER (its sibling argc is a pointer-to-scalar, handled below).
    "stream": "STREAM",
    "commid": "ID",
    "argv": "BUFFER",
    # 2026-07-21, second full-corpus audit. Each of these already had a
    # fitting value in the enum and was reaching null only because the map
    # listed one spelling of a name the corpus uses several of -- not because
    # the schema lacked a category. Every one is grounded in the parameter's
    # own desc text in the standard, quoted below; none needed new vocabulary.
    #
    # MPI's four attribute-key parameters. "key" was already KEY; the corpus
    # actually spells it keyval, per-handle-type ("The key value of the
    # deleted attribute"). 40 parameters.
    "keyval": "KEY", "comm_keyval": "KEY", "type_keyval": "KEY", "win_keyval": "KEY",
    # INDEX_ARRAY -- an array of positions into another parameter. Each
    # is confirmed against its own desc: displs/sdispls/rdispls/
    # array_of_displacements "Entry i specifies the displacement (relative to
    # recvbuf)", indices "an integer array of size len, indicating category
    # indices" (and the wait_until_some family's output positions), index
    # "array of integers describing node degrees" (MPI_Graph_create's
    # cumulative index into edges), coords "coordinates of the MPI process
    # ... in Cartesian structure". 150 parameters.
    #
    # Two near-misses deliberately excluded, both by reading their descs:
    # "dims" is "integer array ... specifying the NUMBER OF PROCESSES in each
    # dimension" -- an array of counts, not of positions -- and "periods" is
    # a "logical array ... whether the grid is periodic", an array of
    # booleans. Neither indexes anything.
    "displs": "INDEX_ARRAY", "sdispls": "INDEX_ARRAY", "rdispls": "INDEX_ARRAY",
    "array_of_displacements": "INDEX_ARRAY", "indices": "INDEX_ARRAY",
    "index": "INDEX_ARRAY", "coords": "INDEX_ARRAY",
    # OPAQUE_STATE -- a void* the PPM stores and hands back without ever
    # dereferencing it ("extra state for callback function", "attribute
    # value"). 72 parameters.
    "extra_state": "OPAQUE_STATE", "extra_state2": "OPAQUE_STATE",
    "attribute_val": "OPAQUE_STATE", "attribute_val_in": "OPAQUE_STATE",
    "attribute_val_out": "OPAQUE_STATE",
    # Error-code spellings other than Fortran's "ierror" -- MPI_Abort's
    # "error code to return to invoking environment", the errhandler
    # callbacks' int *error_code, and the "ierr" short form. 19 parameters.
    "errorcode": "ERROR_CODE", "error_code": "ERROR_CODE", "ierr": "ERROR_CODE",
    # MPI_Sendrecv's two tags ("send message tag" / "receive tag or
    # MPI_ANY_TAG") -- TAG, exactly as the plain "tag" above. 8 parameters.
    "sendtag": "TAG", "recvtag": "TAG",
    # MPI RMA's "rank of target", by value in all 10 corpus instances --
    # RANK, the same as a by-value "rank". 10 parameters.
    "target_rank": "RANK",
    # ------------------------------------------------------------------
    # Same method as the block above: every name below was read against its own desc
    # in the standard before being mapped, and the near-misses are recorded
    # as exclusions rather than silently swept in.
    #
    # BOOL -- a true/false predicate answer. "flag" is MPI's universal
    # predicate out-parameter ("Flag is true if MPI_INIT or MPI_INIT_THREAD
    # has been called and false otherwise"; "boolean flag, same as from
    # MPI_TEST"); "reorder" is by-value ("ranks may be reordered (true) or
    # not (false)"). 42 parameters.
    #
    # Four deliberate exclusions, each by reading the desc:
    #   "provided" -- "provided level of thread support". A LEVEL
    #       (MPI_THREAD_SINGLE..MULTIPLE), not a boolean; it is
    #       THREAD_LEVEL, above.
    #   "result"   -- MPI_Comm_compare's MPI_IDENT/CONGRUENT/SIMILAR/UNEQUAL.
    #       A four-way comparison, not a predicate.
    #   "periods"  -- "logical array of size ndims specifying whether the
    #       grid is periodic (true) or not". An ARRAY of booleans; BOOL is
    #       scalar. Already excluded from INDEX_ARRAY on the same grounds.
    #   "bind"     -- "type of MPI object to which this variable must be
    #       bound". An object-type enum.
    "flag": "BOOL", "reorder": "BOOL",
    # STRING -- a text buffer. All char*/char[] in every instance, and
    # every desc names text: "a port name", "a service name", "data
    # representation identifier", "name of file to open", "the character
    # string that is remembered as the name", "buffer to return the string
    # containing a description of the control variable", "Text that
    # corresponds to the errorcode", "unique identifier for this operation"
    # (MPI_Comm_create_from_group's user-supplied matching tag -- a string,
    # not the opaque out-of-band blob ID is defined for). 49 parameters.
    #
    # Excluded: "value" and "version", both of which the corpus spells with
    # BOTH char* and int* types across different functions (an info value vs.
    # an MPI_T variable value; a version string vs. a version number), so
    # neither can be settled by name alone -- exactly the "dest"/"source"
    # pointer-ness problem one row up, but with no equally clean
    # disambiguator, so they stay null.
    "name": "STRING", "port_name": "STRING", "service_name": "STRING",
    "datarep": "STRING", "filename": "STRING", "comm_name": "STRING",
    "type_name": "STRING", "win_name": "STRING", "desc": "STRING",
    "string": "STRING", "stringtag": "STRING",
    # OPAQUE_STATE -- "pointer to a
    # user-controlled buffer" handed to an MPI_T event callback and returned
    # verbatim, which is this kind's exact definition. 5 parameters.
    #
    # Its sibling "obj_handle" is NOT mapped: "reference to a handle of the
    # MPI object to which this variable is supposed to be bound" is
    # dereferenced by the implementation, so it is neither opaque state nor
    # an MPI_T handle of its own. Logged, not forced.
    "user_data": "OPAQUE_STATE",
}

# Pointer-to-scalar OUTPUT names -> SCALAR (SCALAR covers these alongside
# by-value operands). Grounded in the audit's own 2026-07-17
# finding: every real corpus instance of a pointer named "size" is an output
# scalar, never a data buffer; "argc" (MPI_Init's int*) is the same shape.
# By-value "size" stays COUNT via the substring rule.
#
# The name settles the shape but not the quantity: a pointer "size" is a byte
# size in mpi_type_size/mpi_pack_size, an offset in mpi_file_get_size, and a
# team size in mpi_comm_size. SCALAR is the honest answer for the name alone;
# the team-size queries are picked out by function in _TEAM_SIZE_OUT_PARAMS.
_SCALAR_OUT_PTR_NAMES = frozenset({"size", "argc"})

# Pointer "rank" OUTPUT -> RANK. Every corpus instance
# (mpi_comm_rank/mpi_group_rank/mpi_cart_rank/ncclCommUserRank) receives a rank
# value, and RANK has always meant a rank value without saying whose -- the
# by-value dest/source/root/pe/target_rank below. Unlike "size", the name is
# not overloaded, so no per-function list is needed. Checked before
# _RANK_OR_BUFFER_NAMES, which would otherwise read a pointer "rank" as BUFFER.
_RANK_OUT_PTR_NAMES = frozenset({"rank"})

# Out-parameters receiving the size of a team, group or communicator ->
# TEAM_SIZE. An explicit (function_key,
# parameter) set, not a name rule, for the reason given at
# _SCALAR_OUT_PTR_NAMES. Each MPI desc names the group: "number of MPI
# processes in the group of comm", "... in the remote group of comm", "... in
# the group". NCCL's comms.md: "Returns in *count* the number of ranks in the
# NCCL communicator *comm*."
_TEAM_SIZE_OUT_PARAMS = frozenset({
    ("mpi_comm_size", "size"), ("mpi_comm_remote_size", "size"), ("mpi_group_size", "size"),
    ("ncclCommCount", "count"),
})

# return.value_kind: what a `return.kind == "value"` datum is, in
# parameters[].kind's vocabulary. Only the rank and team-size queries have one;
# every other returned value (a fetched atomic, a time, a handle conversion) has
# no fitting kind and stays null. Listed by function rather than by name
# pattern, each read against its own standard's wording:
#   RANK      -- shmem/nvshmem _my_pe and _team_my_pe (the calling PE's number),
#                _team_translate_pe (a PE number in another team),
#                omp_get_thread_num ("the thread number, within the current
#                team, of the calling thread") and omp_get_ancestor_thread_num
#                (the same, for an ancestor's nesting level).
#   TEAM_SIZE -- shmem/nvshmem _n_pes and _team_n_pes, omp_get_num_threads ("the
#                number of threads in the current team") and omp_get_team_size
#                (the same, for a given nesting level).
#   DEVICE    -- omp_get_device_num ("the device number of the device on
#                which the calling thread is executing"), omp_get_default_device
#                ("the default target device"), omp_get_initial_device ("a
#                device number that represents the host device") and
#                omp_get_device_from_uid (a device number, or
#                omp_invalid_device). omp_get_num_devices is a count, not a
#                device, and stays null.
# Deliberately null, by the same reading:
#   omp_get_max_threads -- "an upper bound on the number of threads that could
#       be used to form a new team": a bound, not the size of any team.
#   omp_get_team_num / omp_get_num_teams -- a position in, and the count of, the
#       teams of a teams region. Those are teams, not members of one, so
#       RANK/TEAM_SIZE would be a near-miss.
_RETURN_VALUE_KINDS = {
    "shmem_my_pe": "RANK", "shmem_team_my_pe": "RANK", "shmem_team_translate_pe": "RANK",
    "shmem_n_pes": "TEAM_SIZE", "shmem_team_n_pes": "TEAM_SIZE",
    "nvshmem_my_pe": "RANK", "nvshmem_team_my_pe": "RANK", "nvshmem_team_translate_pe": "RANK",
    "nvshmem_n_pes": "TEAM_SIZE", "nvshmem_team_n_pes": "TEAM_SIZE",
    "omp_get_thread_num": "RANK", "omp_get_ancestor_thread_num": "RANK",
    "omp_get_num_threads": "TEAM_SIZE", "omp_get_team_size": "TEAM_SIZE",
    "omp_get_device_num": "DEVICE", "omp_get_default_device": "DEVICE",
    "omp_get_initial_device": "DEVICE", "omp_get_device_from_uid": "DEVICE",
}


def return_value_kind(function_key, return_kind):
    """(function_key, the entry's return.kind) -> "RANK" | "TEAM_SIZE" | "DEVICE" | None.

    Non-null only when return.kind is "value" -- that is the field's
    definition. A listed function whose return is anything else means this
    table has gone stale, so it raises instead of writing a contradiction.
    """
    kind = _RETURN_VALUE_KINDS.get(function_key)
    if kind is not None and return_kind != "value":
        raise ValueError(f"{function_key}: listed as returning {kind}, but return.kind is {return_kind!r}")
    return kind

# Names that mean RANK when the parameter is a plain value (not a pointer)
# and BUFFER when it's a pointer -- "dest"/"source" is the concrete
# disambiguating example this project's "design by concrete example"
# convention asks for: MPI_Send's "dest" (int rank) and shmem_int_put's
# "dest" (void* remote address) are the same parameter *name* meaning two
# different `kind`s, distinguished only by pointer-ness, never by name
# alone.
_RANK_OR_BUFFER_NAMES = frozenset({"dest", "destination", "source", "src", "pe", "root", "rank", "peer", "pe_root",
                                   # "target" added 2026-07-19: SHMEM's classic collectives
                                   # (shmem_broadcast32's target buffer) -- same pointer-vs-value
                                   # disambiguation as dest/source.
                                   "target",
                                   # "pe_start" added 2026-07-19: SHMEM's classic active-set triple's
                                   # starting PE number (by value -> RANK, same as pe_root).
                                   "pe_start"})

_BUFFER_ONLY_NAMES = frozenset({
    "buf", "buffer", "sendbuf", "recvbuf", "sendbuff", "recvbuff", "buff",
    "ptr", "addr", "sig_addr",
    # "ivar" added 2026-07-19: SHMEM/NVSHMEM's wait_until/test families poll a
    # pointer-to-symmetric-variable literally named ivar -- a memory location
    # being read, i.e. a BUFFER (confirmed against both PPMs' real signatures;
    # the pilot's 26 wait_until concrete entries all failed strict validation
    # on exactly this null kind).
    "ivar",
    # "psync"/"pwrk" added 2026-07-19: SHMEM's classic-API symmetric work
    # arrays (shmem_broadcast32's pSync etc.) -- real symmetric-heap buffers
    # by the standard's own definition.
    "psync", "pwrk",
    # 2026-07-21, second full-corpus audit. All eight are buffers by the
    # standards' own wording, and all were null only because this set listed
    # one spelling of the name -- the schema was never missing a category.
    #
    # The vector wait_until/test families' plurals. "ivar" was already here;
    # its array form is spelled ivars ("Symmetric address of an ARRAY of
    # remotely accessible data objects" -- the same sentence as ivar's, with
    # "array of" added), and cmp_values is its companion ("Local address of
    # an array of length nelems containing values to be compared"). Note
    # cmp_valueS is a BUFFER while the singular cmp_value stays SCALAR: the
    # singular is a by-value operand, the plural is a pointer to an array,
    # which is exactly the distinction SCALAR is defined on. 426 parameters.
    "ivars", "cmp_values",
    # SHMEM's nonblocking fetching atomics write the fetched value into a
    # caller-supplied location: "Local address of data object to be
    # updated". A local destination, i.e. a BUFFER. 170 parameters.
    "fetch",
    # MPI buffer parameters whose names the set didn't carry, each taken from
    # its own desc: origin_addr "initial address of origin buffer",
    # result_addr "initial address of result buffer", inbuf "input buffer",
    # outbuf "output buffer start", buffer_addr "initial buffer address",
    # base/baseptr "initial address of window", compare_addr "initial address
    # of compare buffer", inoutbuf "combined input and output buffer". The
    # last four (userbuf/filebuf/localbuff, the datarep-conversion and NCCL
    # window callbacks' buffers) carry no desc of their own and are named by
    # the same -buf/-buff convention every other entry in this set uses.
    # 40 parameters.
    "origin_addr", "result_addr", "compare_addr", "inbuf", "outbuf", "inoutbuf",
    "buffer_addr", "base", "baseptr", "userbuf", "filebuf", "localbuff",
})

# By-value operand names -> the SCALAR kind (which exists for exactly these:
# SHMEM/NVSHMEM atomics'/wait_until's operands and put_signal's signal value). Only
# fires when the parameter is confirmed NON-pointer: MPI/NCCL also have
# parameters literally named "value" (mpi_info_set's char*, ncclCommGetAttr's
# out-pointer) that are pointers and must keep falling through -- confirmed
# against the real corpus (every by-value hit is SHMEM/NVSHMEM, every MPI/NCCL
# "value" is a pointer).
# "logpe_stride" (2026-07-19): SHMEM's classic active-set triple's log2-stride
# -- a plain by-value scalar operand (its two siblings resolve as RANK/COUNT).
#
# "dst"/"sst" moved here from _BUFFER_ONLY_NAMES 2026-07-21 (full-corpus
# audit). Despite reading like abbreviations of "destination"/"source"
# buffers, in OpenSHMEM/NVSHMEM they are the strided-RMA family's element
# STRIDES: shmem_iput(dest, source, dst, sst, nelems, pe), where the spec
# defines dst as "the stride between consecutive elements of the dest array
# ... scaled by the element size" (external-inputs/shmem/tex/shmem-standard/content/
# shmem_iput.tex) and sst likewise for source. All 108 corpus instances are
# by-value ptrdiff_t, never pointers -- confirmed directly -- so the
# non-pointer guard below is belt-and-braces rather than the discriminator.
# Classifying them BUFFER also fed the formal binder two phantom buffers,
# which is part of why the strided family got force-fitted onto contiguous
# shapes.
_SCALAR_BY_VALUE_NAMES = frozenset({"value", "cmp", "cmp_value", "cond", "signal", "logpe_stride",
                                    "dst", "sst"})

# "size" added 2026-07-19 (grounded: shmem_malloc/nvshmem_malloc's by-value
# size_t size). Safe against mpi_comm_size's out-pointer "size" parameter --
# the COUNT rule below already excludes confirmed pointers.
_COUNT_NAME_SUBSTRINGS = ("count", "nelem", "nblocks", "nranks", "bsize", "nreduce", "size")

# Out-pointer COUNTs (2026-07-21, second audit; approved as a deliberate
# narrowing of the "COUNT excludes pointers" rule above). The exclusion is
# right in general -- a pointer named "size" is usually a scalar OUTPUT, which
# is why mpi_comm_size's "size" resolves to SCALAR earlier -- but a routine
# that writes the *length of a string it just filled in* is returning a count,
# not an opaque scalar, and the standard's own descs say so ("length of the
# string and/or buffer for name", "length of returned name"). Kept as an
# explicit name set rather than by dropping the pointer guard, so the general
# rule stays conservative and only these confirmed cases change.
_COUNT_OUT_PTR_NAMES = frozenset({
    "name_len", "desc_len", "resultlen", "len",
    "num", "num_cvars", "num_pvars", "num_categories", "num_cat", "num_cvar",
    "num_pvar", "num_events", "num_sources", "num_elements",
})

# SHMEM/NVSHMEM local synchronization/completion primitives -> the
# api_group value "synchronization" (which exists for exactly these -- see docs/cross-ppm-analysis/known-gaps-and-open-questions.md's
# resolved row). Three sub-families, all grounded against the real corpus:
# "wait_until" substring (the typed wait_until family incl. signal_wait_until
# and the _all/_any/_some/_vector variants), a fence/quiet name tail
# (shmem_fence/quiet, ctx_/pe_ variants, nvshmem_fence/quiet), and the typed
# point-poll _test family -- anchored as a suffix regex specifically so
# shmem_test_lock (a lock-acquisition attempt, not a completion poll) does
# NOT match.
_SHMEM_TEST_FAMILY_RE = re.compile(r"_test(_all|_any|_some)?(_vector)?$")


def shmem_synchronization_name(function_key):
    """True if the name matches SHMEM/NVSHMEM's local-synchronization naming
    conventions (wait_until / fence / quiet / the typed _test point-poll
    family). PPM-agnostic string check; the per-PPM modules decide whether
    to consult it at all and in what precedence order (in NVSHMEM it must
    run before the one_sided "signal" substring rule, or
    nvshmem_signal_wait_until would misclassify as one_sided)."""
    return (
        "wait_until" in function_key
        or function_key.endswith(("fence", "quiet"))
        or bool(_SHMEM_TEST_FAMILY_RE.search(function_key))
    )


# --- C-type -> kind, the deterministic fallback (added 2026-07-21) --------
#
# The name-based rules below are heuristics by necessity: a parameter called
# "dest" is a rank in MPI_Send and a buffer in shmem_put. But MPI's handle
# types are not ambiguous at all -- a parameter declared `MPI_Info info` is an
# info handle, full stop, and no naming convention is involved. The full-corpus
# audit found 1286 parameters with a null kind, and grouping them by C base
# type rather than by name showed the bulk were these unambiguous handles:
# MPI_Info (84), MPI_Datatype (69), MPI_File (60), MPI_Group (39), MPI_Comm
# (26), MPI_Errhandler (18), MPI_Session (17), MPI_Request/MPI_Status (10
# each), MPI_Message (6).
#
# Note what that list reveals: MPI_Datatype/MPI_Comm/MPI_Request/MPI_Status
# already HAD enum values -- those 115 parameters were pure misses, names the
# _KIND_NAME_MAP simply didn't enumerate ("newtype", "oldtype", "sendtype",
# ...). Reading the declared type instead of guessing from the name fixes
# those for free and keeps fixing them as new functions appear, which a name
# list never would.
#
# Only consulted AFTER the name rules, so every existing grounded name
# judgment (including the pointer-vs-value dest/source disambiguation) wins
# unchanged; this strictly fills nulls.
_CTYPE_KIND_MAP = {
    # first-class MPI handle types
    "MPI_Info": "INFO",
    "MPI_File": "FILE",
    "MPI_Group": "GROUP",
    "MPI_Errhandler": "ERRHANDLER",
    "MPI_Session": "SESSION",
    "MPI_Message": "MESSAGE",
    # pre-existing enum values the name map was simply missing
    "MPI_Datatype": "DATATYPE",
    "MPI_Comm": "COMMUNICATOR",
    "MPI_Request": "REQUEST",
    "MPI_Status": "STATUS",
    "MPI_Win": "WINDOW",
    "MPI_Op": "OPERATION",
    # address/size scalars: SCALAR covers both by-value operands and
    # pointer-to-scalar outputs, per its own description
    "MPI_Aint": "SCALAR",
    "MPI_Offset": "SCALAR",
    "MPI_Count": "SCALAR",
    # One generic TOOL_HANDLE for the whole MPI_T family rather than
    # a kind per handle type: the five opaque MPI_T typedefs below are all
    # "an opaque handle into the tool information interface" as far as any
    # consumer of this schema is concerned, and minting five values where one
    # carries the same information is what the consumer-vocabulary budget in
    # CLAUDE.md warns against. A tool that needs to tell a pvar handle from a
    # cvar handle can read binding_type.c, which still says which it is.
    "MPI_T_pvar_handle": "TOOL_HANDLE",
    "MPI_T_cvar_handle": "TOOL_HANDLE",
    "MPI_T_pvar_session": "TOOL_HANDLE",
    "MPI_T_event_registration": "TOOL_HANDLE",
    "MPI_T_event_instance": "TOOL_HANDLE",
    "MPI_T_enum": "TOOL_HANDLE",
}

# **Reversed 2026-07-21 by the project owner.** This block previously read:
# "MPI_T_* tool-interface handles are deliberately absent: the MPI Tool
# information interface is a separate API surface from the communication API
# this schema targets, and inventing kinds for it would grow the consumer
# vocabulary for functions no downstream tool has asked for. They stay null --
# a logged gap, not an oversight." That reasoning is still on the record and
# still coherent; it was overridden in favour of covering the 54 MPI_T entries
# the corpus already carries, at a cost of exactly one new enum value. If the
# tool interface is ever taken back out of corpus scope, this mapping and the
# TOOL_HANDLE enum value should go with it.
#
# MPI_T_cb_safety and MPI_T_source_order are deliberately NOT mapped here:
# despite the MPI_T_ prefix they are enumeration types (a callback-safety
# level, a source-ordering mode), not handles -- a value drawn from a fixed
# set, which is a different thing from a reference to runtime state.
_CTYPE_TOKEN_RE = re.compile(r"\b(MPI_[A-Za-z_]+)\b")


def kind_from_c_type(param):
    """parameters[].binding_type.c -> a kind enum value, or None.

    Deterministic: reads the declared C type, never the parameter name.
    """
    c = (param.get("binding_type") or {}).get("c")
    if not c:
        return None
    m = _CTYPE_TOKEN_RE.search(c)
    if not m:
        return None
    return _CTYPE_KIND_MAP.get(m.group(1))


def parameter_kind(name, is_ptr, function_key=None):
    """(parameter name, is_pointer_or_None, function_key) -> a
    parameters[].kind enum value, or None if nothing here matches.

    Deliberately does not try to cover every parameter in the corpus --
    only the names/type-combinations grounded in real, checked examples
    (see workflow/README.md). Scalar
    operand-by-value parameters (SHMEM/NVSHMEM atomics' "value"/"cmp"/
    "cmp_value") are SCALAR, matched below, as are
    pointer-to-scalar outputs, except the rank and team-size outputs: mpi_comm_rank's "rank" is RANK, and mpi_comm_size's "size"
    is TEAM_SIZE -- the latter only via function_key, since a pointer "size"
    is just as often a byte size (see _TEAM_SIZE_OUT_PARAMS).
    """
    if not name:
        return None
    lname = name.lower()

    if is_ptr is True and (function_key, lname) in _TEAM_SIZE_OUT_PARAMS:
        return "TEAM_SIZE"

    if lname in _KIND_NAME_MAP:
        return _KIND_NAME_MAP[lname]

    # A pointer named "rank"/"size"/"argc" is, in every real corpus instance
    # checked (mpi_comm_rank/mpi_cart_rank/mpi_group_rank/ncclCommUserRank,
    # mpi_comm_size, mpi_init -- confirmed 2026-07-17 auditing the pilot
    # corpus against apis.json directly), a pointer-to-scalar output/inout,
    # not a data buffer. Checked before _RANK_OR_BUFFER_NAMES so a pointer
    # "rank" resolves here (by-value "rank" still resolves to RANK below).
    if lname in _RANK_OUT_PTR_NAMES and is_ptr is True:
        return "RANK"
    if lname in _SCALAR_OUT_PTR_NAMES and is_ptr is True:
        return "SCALAR"

    if lname in _RANK_OR_BUFFER_NAMES:
        if is_ptr is True:
            return "BUFFER"
        if is_ptr is False:
            return "RANK"
        return None  # pointer-ness unknown -- genuinely ambiguous, don't guess

    if lname in _BUFFER_ONLY_NAMES:
        return "BUFFER"

    if lname in _SCALAR_BY_VALUE_NAMES and is_ptr is False:
        return "SCALAR"

    if any(s in lname for s in _COUNT_NAME_SUBSTRINGS) and is_ptr is not True:
        return "COUNT"

    if lname in _COUNT_OUT_PTR_NAMES:
        return "COUNT"

    return None
