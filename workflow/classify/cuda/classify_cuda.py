"""
CUDA's Heuristic Classification module. The corpus is the CUDA Runtime API
declared in cuda_runtime_api.h (workflow/extract/cuda/adapter.py): no
collectives, point-to-point or one-sided communication, and no atomics.

  execution.launch -- which routines device code may call, read from the
      vendored cuda_device_runtime_api.h: the device runtime's own header, and
      therefore the list of what it actually declares. NOT from the
      `__cudart_builtin__` qualifier, which says the runtime may supply a
      builtin implementation and is a different claim: 22 of the 52 routines
      carrying it -- cudaMallocManaged, cudaGetDeviceProperties,
      cudaStreamCreateWithPriority, the occupancy helpers and 17 more -- are
      not in that header at all, while cudaGraphLaunch is in it without
      carrying the qualifier. The qualifier is still reported in the note when
      it corroborates. Routines the device header marks __CDPRT_DEPRECATED
      (cudaDeviceSynchronize, which it comments "is removed on sm_90+") say so
      in the note rather than silently claiming an unqualified "cpu+gpu".
  execution.gpu_scope -- "thread" for a device-callable routine: each calling
      thread issues a device-runtime call on its own, the same reading as the
      unsuffixed NVSHMEM device API.
  identity.api_group -- CUDA's verb-in-the-name convention: Get/Is/Can
      inquiries (query); Malloc/Free/Create/Destroy/Set/Register... lifecycle
      and configuration (management); *Synchronize, stream/event waits, event
      records, completion polls, external-semaphore signal/wait and the
      GPUDirect RDMA write flush (synchronization). cudaMemcpy*, cudaMemset*
      and cudaMemPrefetch* are a local copy, fill or migration, and
      cudaLaunch*/cudaGraphLaunch a kernel launch; neither fits any of the
      seven groups -- left null and logged
      (docs/cross-ppm-analysis/known-gaps-and-open-questions.md).
  relationships.variants -- the `Async` suffix pairs a routine with its
      stream-ordered counterpart: cudaMemcpy/cudaMemcpyAsync,
      cudaMalloc/cudaMallocAsync, ...
  parameters[].kind -- CUDA-local rules keyed on the declared C type first,
      which in this API settles what the names do not (_cuda_kind); the
      shared name rules in heuristics.py only for plain C types.
"""

import functools
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from common.ir import Confident  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from heuristics import kind_from_c_type, parameter_kind, return_value_kind, is_pointer_param  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "common"))
from layout import EXTERNAL_INPUTS_DIR  # noqa: E402

_DEVICE_HEADER_NAME = "cuda_device_runtime_api.h"
_DEVICE_HEADER_PATH = os.path.join(EXTERNAL_INPUTS_DIR, "cuda", "implementation", "cuda-13.1.0",
                                   "include", _DEVICE_HEADER_NAME)
# "extern __device__ __cudart_builtin__ __CDPRT_DEPRECATED(cudaDeviceSynchronize)
#  cudaError_t CUDARTAPI cudaDeviceSynchronize(void);" and the inline/template
# forms further down the same header.
_DEVICE_DECL_RE = re.compile(r"\b(cuda[A-Za-z0-9_]+)\s*\(")
_CDPRT_DEPRECATED_RE = re.compile(r"__CDPRT_DEPRECATED\s*\(\s*(cuda[A-Za-z0-9_]+)\s*\)")


@functools.lru_cache(maxsize=None)
def _device_runtime_surface(path=None):
    """-> ({routine}, {routine: deprecated}) from the fetched device-runtime
    header. A name is device-callable when that header declares it; the second
    set is the subset the header itself marks as deprecated for device use.
    Read on first use, not at import: the header is fetched, not vendored
    (workflow/fetch/manifest.json), and a build that leaves CUDA out with
    --ppm still imports this module through classify/cli.py."""
    with open(path or _DEVICE_HEADER_PATH, encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    text = re.sub(r"//[^\n]*", " ", text)
    declared = set()
    for statement in re.finditer(r"[^;{}]*[;{]", text):
        body = statement.group(0)
        if "__device__" not in body:
            continue
        for name in _DEVICE_DECL_RE.findall(body):
            declared.add(name)
    deprecated = set(_CDPRT_DEPRECATED_RE.findall(text))
    return declared, deprecated

_SYNCHRONIZATION_NAMES = frozenset({
    "cudaStreamWaitEvent", "cudaStreamQuery", "cudaEventQuery",
    "cudaEventRecord", "cudaEventRecordWithFlags",
    "cudaExecutionCtxRecordEvent", "cudaExecutionCtxWaitEvent",
    "cudaSignalExternalSemaphoresAsync", "cudaWaitExternalSemaphoresAsync",
    # Orders outstanding GPUDirect RDMA writes before later accesses -- the
    # same role as OpenSHMEM's fence/quiet, which are synchronization too.
    "cudaDeviceFlushGPUDirectRDMAWrites",
})
_NO_GROUP_PREFIXES = (
    # a local copy, fill or migration -- the logged gap
    "cudaMemcpy", "cudaMemset", "cudaMemPrefetch", "cudaMemDiscardAndPrefetch",
    # a kernel/graph launch -- likewise no group
    "cudaLaunch", "cudaGraphLaunch",
)
_QUERY_PREFIXES = ("cudaOccupancy", "cudaPeekAt", "cudaChoose")
_QUERY_TOKENS = ("Get", "Dump")
_QUERY_NAMES = frozenset({
    "cudaEventElapsedTime", "cudaStreamIsCapturing", "cudaDeviceCanAccessPeer",
    "cudaGraphNodeFindInClone", "cudaGraphDebugDotPrint", "cudaLibraryEnumerateKernels", "cudaLogsCurrent",
})
# Case-sensitive CamelCase tokens: "Register" does not match "Unregister",
# so the un- forms are listed in their own right.
_MANAGEMENT_TOKENS = (
    "Malloc", "Free", "Alloc", "Register", "Unregister", "Create", "Destroy", "Set", "Reset", "Init",
    "Import", "Export", "Map", "Unmap", "Retain", "Release", "Enable", "Disable", "Add", "Remove",
    "Instantiate", "Upload", "Attach", "Capture", "Update", "Open", "Close", "Clone", "Trim",
    "Advise", "Copy", "Load", "Unload", "Split", "Generate", "Discard",
)


def _launch_for(entry, function_key):
    sig = ((entry.get("bindings") or {}).get("c") or {}).get("signature") or ""
    device_callable, device_deprecated = _device_runtime_surface()
    if function_key in device_callable:
        note = f"declared __device__ in {_DEVICE_HEADER_NAME}, so device code may call it"
        if "__cudart_builtin__" in sig:
            note += "; cuda_runtime_api.h's __cudart_builtin__ agrees"
        if function_key in device_deprecated:
            note += (f"; {_DEVICE_HEADER_NAME} marks it __CDPRT_DEPRECATED, and for cudaDeviceSynchronize "
                     f"comments that it is removed on sm_90+")
        if "__host__" not in sig:
            return Confident("gpu", "pattern", note + " -- and cuda_runtime_api.h gives it no __host__ form")
        return Confident("cpu+gpu", "pattern", note)
    note = f"{_DEVICE_HEADER_NAME} does not declare it, so only host code may call it"
    if "__cudart_builtin__" in sig:
        note += ("; the __cudart_builtin__ qualifier on its cuda_runtime_api.h declaration says the runtime "
                 "may supply a builtin implementation, which is not a claim about device-callability")
    return Confident("cpu", "pattern", note)


def _api_group(function_key):
    if function_key.endswith("Synchronize") or function_key in _SYNCHRONIZATION_NAMES:
        return Confident("synchronization", "pattern",
                         "CUDA synchronize/wait/record/poll routine -- orders host, streams and events, moves no data")
    if function_key.startswith(_NO_GROUP_PREFIXES):
        return None
    if (any(tok in function_key for tok in _QUERY_TOKENS) or function_key.startswith(_QUERY_PREFIXES)
            or function_key in _QUERY_NAMES):
        return Confident("query", "pattern", "CUDA inquiry naming convention (Get/Query/Is)")
    if any(tok in function_key for tok in _MANAGEMENT_TOKENS):
        return Confident("management", "pattern",
                         "CUDA lifecycle/configuration verb in the name (Malloc/Free/Create/Destroy/Set/...)")
    return None


# The kernel-launch family -- api-sync-behavior.md's third asynchronous
# family ("Kernel launches are asynchronous with respect to the host").
# Prefix-matched because every member spells it the same way, plus the two
# graph entry points that submit rather than build (cudaGraphLaunch enqueues
# an instantiated graph; cudaGraphUpload uploads one ahead of launching it).
# The ~90 other cudaGraph* routines construct or query a graph on the host
# and are ordinary synchronous calls.
_LAUNCH_PREFIXES = ("cudaLaunch",)
_LAUNCH_NAMES = frozenset({"cudaGraphLaunch", "cudaGraphUpload"})


def _blocking(function_key, entry):
    """execution.blocking, read off CUDA's own API-synchronization page.

    external-inputs/cuda/docs/13.1/md/api-sync-behavior.md is the vendored
    statement of which runtime calls are asynchronous with respect to the
    host, and it names exactly three families: the memcpy/memset forms with
    an "Async" suffix, the memsets, and kernel launches. Everything else in
    the runtime API returns once its work is done. The three rules below are
    that page, enumerated:

      - an `Async` suffix -> asynchronous. The page's own marker for the
        stream-taking forms, and it also picks up the stream-ordered
        allocators (cudaMallocAsync/cudaFreeAsync) and prefetches.
      - `cudaMemset*` -> asynchronous, quoting the page directly: "The
        cudaMemset functions are asynchronous with respect to the host
        except when the target memory is pinned host memory." The pinned-
        host exception is a property of the argument, not of the symbol --
        this field records the default case and
        tool_integration.context_dependencies is where such an exception
        belongs. The graph node builders (cudaGraphAddMemsetNode, ...)
        deliberately do not match: they record a memset into a graph, they
        do not perform one.
      - the launch family (_LAUNCH_PREFIXES/_LAUNCH_NAMES).

    **Why not "takes a cudaStream_t", the way classify_nccl._blocking does**
    (tried first, 2026-09-13, and wrong): unlike NCCL, whose API has no
    stream-management surface at all, CUDA owns the stream type, so ~20 of
    its routines take a `cudaStream_t` in order to *operate on that stream*
    rather than to enqueue work onto it -- cudaStreamCreateWithPriority
    takes an out-pointer to one, and cudaStreamSynchronize, the single most
    blocking call in the API, takes one by value. The signature says which
    handle a routine touches, not when the routine returns.

    That page's own caveat is worth repeating rather than encoding: "Any
    CUDA API call may block or synchronize for various reasons such as
    contention for or unavailability of internal resources." This field
    records the call's documented behaviour, not a guarantee about any
    particular execution.
    """
    if function_key.endswith("Async"):
        return Confident(False, "pattern",
                         "CUDA Async-suffix family: asynchronous with respect to the host "
                         "(api-sync-behavior.md)")
    if function_key.startswith("cudaMemset"):
        return Confident(False, "pattern",
                         "CUDA api-sync-behavior.md: \"The cudaMemset functions are asynchronous "
                         "with respect to the host except when the target memory is pinned host "
                         "memory\"")
    if function_key.startswith(_LAUNCH_PREFIXES) or function_key in _LAUNCH_NAMES:
        return Confident(False, "pattern",
                         "CUDA api-sync-behavior.md: \"Kernel launches are asynchronous with "
                         "respect to the host\"")
    return Confident(True, "pattern",
                     "CUDA runtime default: synchronous with respect to the host -- "
                     "api-sync-behavior.md lists the asynchronous families exhaustively")


def _collective(function_key):
    """execution.collective -- always false for CUDA.

    The CUDA Runtime API has no team to be collective over. Every entry point is
    issued by one host thread against one device, stream or context; the
    multi-process, multi-device coordination this field describes is what NCCL
    and NVSHMEM are layered on top of CUDA to provide. Stated here rather than
    left to fall out of a default, so the value is a reading of the API's scope
    and not an absence of evidence.
    """
    return Confident(False, "pattern",
                     "CUDA: the Runtime API has no process or device team -- every call is issued "
                     "by one host thread against one device, stream or context")


def _execute_once(function_key):
    """execution.execute_once -- always false for CUDA.

    The CUDA runtime has no explicit initialization call to mark: context
    creation is implicit on first use, cudaInitDevice and cudaSetDevice are
    per-device and freely repeatable, and cudaDeviceReset destroys the
    calling thread's current device context but leaves the process able to
    build another. No runtime entry point is restricted to one call per
    process.
    """
    return Confident(False, "pattern",
                     "CUDA: runtime initialization is implicit and per-device, and no runtime "
                     "entry point is restricted to one call per process")


def _variants(function_key, all_function_keys):
    if function_key.endswith("Async"):
        base = function_key[: -len("Async")]
        if base in all_function_keys:
            return {"blocking": Confident(base, "pattern", "CUDA Async-suffix naming convention")}
    elif function_key + "Async" in all_function_keys:
        return {"nonblocking": Confident(function_key + "Async", "pattern", "CUDA Async-suffix naming convention")}
    return None


# Kinds read off the declared C type, applied BEFORE the shared name rules.
# Those rules encode MPI/OpenSHMEM conventions about plain ints -- a by-value
# "src" is a rank, a by-value "dst" a stride -- and CUDA passes handles by
# value under the same names: cudaStreamCopyAttributes(cudaStream_t dst,
# cudaStream_t src), cudaMemcpyToArray(cudaArray_t dst, ...), and
# cudaArrayGetInfo(struct cudaChannelFormatDesc *desc, ...) would otherwise be
# a STRING. So a parameter of a CUDA handle, enum or struct type -- or a
# pointer to one -- is settled here, and only plain C types reach the shared
# rules.
#
# Untyped pointers are settled by name, from the names the corpus actually
# uses. A `void *` named for memory (dst/src/devPtr/ptr/symbol/...) is an
# address -> BUFFER; the same type named func/entryFuncAddr/symbolPtr is a
# function, and value/shareableHandle a typeless out-location -- neither a
# buffer, so they stay null. A `void **` under an address name is where the
# routine stores an address it produced -- a pointer-to-scalar output, which
# is SCALAR's definition (heuristics._SCALAR_OUT_PTR_NAMES is the same rule for
# rank/size); the other `void **`s (args, the option-value arrays, dptrs)
# are arrays and stay null. userData is the caller's cookie handed back to a
# callback: OPAQUE_STATE, exactly as MPI's extra_state/user_data.
_ARRAY_HANDLE_TYPES = frozenset({"cudaArray_t", "cudaArray_const_t", "cudaMipmappedArray_t", "cudaMipmappedArray_const_t"})
_CUDA_TYPEDEF_RE = re.compile(r"^cuda\w*_t$")
_UNTYPED_POINTERS = frozenset({"void *", "const void *"})
_BUFFER_POINTER_NAMES = frozenset({
    "dst", "src", "devPtr", "ptr", "dptr", "dptr_out", "symbol", "pHost", "data", "code",
})
_ADDRESS_OUT_NAMES = frozenset({"devPtr", "ptr", "dptr", "pHost", "pDevice", "funcPtr", "fptr"})


def _cuda_kind(p):
    """-> (kind, reason) when the declared C type settles the parameter -- kind
    None then means no kind fits and the shared name rules must not guess --
    or None to fall through to them."""
    c = (p.get("binding_type") or {}).get("c") or ""
    name = p.get("name")
    core = re.sub(r"\bconst\b|\*", " ", c).split()  # the type with qualifiers and pointers stripped
    if core == ["cudaStream_t"]:
        return "STREAM", f"declared {c} -- a CUDA stream handle, unambiguous, not a name guess"
    if c in _ARRAY_HANDLE_TYPES:
        return "BUFFER", f"declared {c} -- a CUDA array, the memory a copy reads or writes"
    if (len(core) == 1 and _CUDA_TYPEDEF_RE.match(core[0])) or (len(core) == 2 and core[0] in ("struct", "enum")):
        return None, None
    if c in _UNTYPED_POINTERS and name in _BUFFER_POINTER_NAMES:
        return "BUFFER", f"untyped pointer ({c!r}) named for memory -- an address"
    if c == "void **" and name in _ADDRESS_OUT_NAMES:
        return "SCALAR", "void ** under an address name -- the routine stores an address it produced"
    if name == "userData":
        return "OPAQUE_STATE", "the caller's opaque cookie, handed back to a callback"
    return None


def _parameters(function_key, entry):
    out = []
    for p in entry["parameters"]:
        is_ptr = is_pointer_param(p)
        settled = _cuda_kind(p)
        if settled is not None:
            kind, kind_reason = settled
        else:
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


def classify_cuda(entries):
    """entries: {function_key: full syntactic entry} for model=="cuda".
    Returns list[(ir_dict, flags_list)], mirroring Extract adapters' shape.
    """
    all_keys = set(entries)
    results = []
    for function_key, entry in entries.items():
        # Rank and team-size queries, per function -- see heuristics._RETURN_VALUE_KINDS.
        value_kind = return_value_kind(function_key, entry["return"]["kind"])
        value_kind = Confident(value_kind, "pattern", "rank/team-size query, listed per function") if value_kind else None
        launch = _launch_for(entry, function_key)
        gpu_scope = None
        if "gpu" in launch.value:
            gpu_scope = Confident("thread", "pattern",
                                  "a device-runtime call is issued by each calling thread independently")
        ir = {
            "model": "cuda",
            "function_key": function_key,
            "identity.api_group": _api_group(function_key),
            "execution.blocking": _blocking(function_key, entry),
            "execution.execute_once": _execute_once(function_key),
            "execution.collective": _collective(function_key),
            "execution.launch": launch,
            "execution.gpu_scope": gpu_scope,
            "execution.stages": None,          # no MPI-4-style init/start/complete/free taxonomy
            "execution.procedure_class": None,
            "semantics.atomic": None,          # atomics are device intrinsics, not runtime API routines
            "relationships.variants": _variants(function_key, all_keys),
            "return.value_kind": value_kind,
            "parameters": _parameters(function_key, entry),
            "flags": [],
        }
        results.append((ir, ir["flags"]))
    return results
