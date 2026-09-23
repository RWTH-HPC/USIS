"""
Completes parameters[].length and parameters[].array_type on the merged corpus,
so that both follow one convention in every entry:

    length          meaning
    --------------  ------------------------------------------------------------
    integer         the array has that many elements
    parameter name  the array has as many elements as that parameter's value, in
                    units of the buffer's datatype where it has one
    PPM constant    the array has as many elements as that named constant
                    (MPI_MAX_OBJECT_NAME)
    "*"             an array whose length is not recorded as a number,
                    parameter or constant: it depends on an object passed in
                    (a communicator's group size, a topology's degree), on
                    several parameters, on a terminator, or the source does
                    not say; desc says more where the source does
    null            not an array: a scalar, a handle, or a pointer to one value

    array_type is null exactly when length is, and otherwise "fixed" (a number
    or constant), "2d" (a declared T x[][n]; length holds the outer dimension)
    or "variable" (everything else).

Extract sets both where the source states them (MPI's apis.json). Everything
else is decided here, after the merge, because the decision needs
parameters[].kind (Classify) and, for a buffer's element count, the extent of
the buffer's own semantics.formal data_flow access (assigned shapes). Nothing
already set is overwritten.

Is a parameter an array? In order, the first rule that fires decides:

  declared   length already set, or the C declarator has [] (T x[], T *x[])
  kind       parameters[].kind is BUFFER or INDEX_ARRAY
  string     a single-level char pointer (char *, const char *) -- a string is
             an array of char; char ** is a pointer to one and is not
  desc       the parameter's own description opens with "array/list/set ..."
             ("Array of nodes", "Optional array of edge data", "List of
             devices") or names an "array of length ..." -- but only on a
             single-level pointer, or on T ** when the description says the
             array holds pointers ("Array of pointers to kernel parameters")
  listed     _LISTED_ARRAYS below: arrays the rules cannot see, mostly
             because the source gives no description to read (NCCL, NVSHMEM
             and OpenMP carry none), each listed with its reason
  otherwise  not an array

The length of an array found here is, in order: the parameter _LISTED_ARRAYS
names; the parameter its description names ("array of length nelems", "Array
of size numOps") when that is a parameter of the same call; for a buffer, the
count_ref of its formal extent, when every data_flow access to it agrees on
one count_ref naming a scalar parameter and none places data at an offset (a
gathered write, a per-recipient block -- there the extent is one block, not
the buffer); otherwise "*".

Each value set here goes into promotion_log, so the provenance report
attributes it: a length read from a shape's extent to the assignment it came
from (stage "assign", model-assisted, needs approval), everything else to this
step (stage "assemble", mechanical, pattern) with the rule that fired.
"""

import re

# Arrays the rules above cannot see: most have no description to read. Keyed
# by (entry_key, parameter name); the value is (length, why it is an array),
# length being the sibling parameter that counts it or None where no parameter
# does. Each was checked against the call's C signature, which names the
# counting parameter, and its description where the source has one -- not yet
# against the vendor documentation.
_LISTED_ARRAYS = {
    ("nccl:ncclCommInitAll", "comm"): ("ndev", "one communicator per device in devlist"),
    ("nccl:ncclCommInitAll", "devlist"): ("ndev", "the CUDA devices, ndev of them"),
    ("nccl:ncclCommInitRankScalable", "commIds"): ("nId", "nId unique ids"),
    ("nccl:ncclCommShrink", "excludeRanksList"): ("excludeRanksCount", "excludeRanksCount ranks to exclude"),
    ("nccl:ncclWaitSignal", "signalDescs"): ("nDesc", "nDesc signal descriptors"),
    ("nvshmem:nvshmem_{T}_test_all", "status"): ("nelems", "optional mask of nelems entries, as in OpenSHMEM"),
    ("nvshmem:nvshmem_{T}_test_any", "status"): ("nelems", "optional mask of nelems entries, as in OpenSHMEM"),
    ("nvshmem:nvshmem_{T}_test_some", "status"): ("nelems", "optional mask of nelems entries, as in OpenSHMEM"),
    ("nvshmem:nvshmem_{T}_wait_until_all", "status"): ("nelems", "optional mask of nelems entries, as in OpenSHMEM"),
    ("nvshmem:nvshmem_{T}_wait_until_any", "status"): ("nelems", "optional mask of nelems entries, as in OpenSHMEM"),
    ("nvshmem:nvshmem_{T}_wait_until_some", "status"): ("nelems", "optional mask of nelems entries, as in OpenSHMEM"),
    ("nvshmem:nvshmem_{T}_test_all_vector", "status"): ("nelems", "optional mask of nelems entries, as in OpenSHMEM"),
    ("nvshmem:nvshmem_{T}_test_any_vector", "status"): ("nelems", "optional mask of nelems entries, as in OpenSHMEM"),
    ("nvshmem:nvshmem_{T}_test_some_vector", "status"): ("nelems", "optional mask of nelems entries, as in OpenSHMEM"),
    ("nvshmem:nvshmem_{T}_wait_until_all_vector", "status"): ("nelems", "optional mask of nelems entries, as in OpenSHMEM"),
    ("nvshmem:nvshmem_{T}_wait_until_any_vector", "status"): ("nelems", "optional mask of nelems entries, as in OpenSHMEM"),
    ("nvshmem:nvshmem_{T}_wait_until_some_vector", "status"): ("nelems", "optional mask of nelems entries, as in OpenSHMEM"),
    ("shmem:shmem_{T}_test_all_vector", "status"): ("nelems", "optional mask of nelems entries"),
    ("shmem:shmem_{T}_test_any_vector", "status"): ("nelems", "optional mask of nelems entries"),
    ("shmem:shmem_{T}_test_some_vector", "status"): ("nelems", "optional mask of nelems entries"),
    ("shmem:shmem_{T}_wait_until_all_vector", "status"): ("nelems", "optional mask of nelems entries"),
    ("shmem:shmem_{T}_wait_until_any_vector", "status"): ("nelems", "optional mask of nelems entries"),
    ("shmem:shmem_{T}_wait_until_some_vector", "status"): ("nelems", "optional mask of nelems entries"),
    ("shmem:shmem_ctx_pe_quiet", "target_pes"): ("npes", "npes target PEs"),
    ("shmem:shmem_pe_quiet", "target_pes"): ("npes", "npes target PEs"),
    ("openmp:omp_get_devices_allocator", "devs"): ("ndevs", "ndevs device numbers"),
    ("openmp:omp_get_devices_and_host_allocator", "devs"): ("ndevs", "ndevs device numbers"),
    ("openmp:omp_get_devices_and_host_memspace", "devs"): ("ndevs", "ndevs device numbers"),
    ("openmp:omp_get_devices_memspace", "devs"): ("ndevs", "ndevs device numbers"),
    ("openmp:omp_get_partition_place_nums", "place_nums"): (None, "one place number per place in the partition"),
    ("openmp:omp_get_place_proc_ids", "ids"): (None, "one processor id per processor in the place"),
    ("openmp:omp_get_submemspace", "resources"): ("num_resources", "num_resources resource ids"),
    ("openmp:omp_target_memcpy_async", "depobj_list"): ("depobj_count", "depobj_count dependence objects"),
    ("openmp:omp_target_memcpy_rect_async", "depobj_list"): ("depobj_count", "depobj_count dependence objects"),
    ("openmp:omp_target_memset_async", "depobj_list"): ("depobj_count", "depobj_count dependence objects"),
    ("openmp:omp_target_memcpy_rect", "volume"): ("num_dims", "one extent per dimension, num_dims of them"),
    ("openmp:omp_target_memcpy_rect", "dst_offsets"): ("num_dims", "one offset per dimension, num_dims of them"),
    ("openmp:omp_target_memcpy_rect", "src_offsets"): ("num_dims", "one offset per dimension, num_dims of them"),
    ("openmp:omp_target_memcpy_rect", "dst_dimensions"): ("num_dims", "one extent per dimension, num_dims of them"),
    ("openmp:omp_target_memcpy_rect", "src_dimensions"): ("num_dims", "one extent per dimension, num_dims of them"),
    ("openmp:omp_target_memcpy_rect_async", "volume"): ("num_dims", "one extent per dimension, num_dims of them"),
    ("openmp:omp_target_memcpy_rect_async", "dst_offsets"): ("num_dims", "one offset per dimension, num_dims of them"),
    ("openmp:omp_target_memcpy_rect_async", "src_offsets"): ("num_dims", "one offset per dimension, num_dims of them"),
    ("openmp:omp_target_memcpy_rect_async", "dst_dimensions"): ("num_dims", "one extent per dimension, num_dims of them"),
    ("openmp:omp_target_memcpy_rect_async", "src_dimensions"): ("num_dims", "one extent per dimension, num_dims of them"),
    ("openmp:omp_target_memcpy", "dst"): (None, "the destination buffer, length bytes"),
    ("openmp:omp_target_memcpy_async", "dst"): (None, "the destination buffer, length bytes"),
    ("openmp:omp_target_memcpy_rect", "dst"): (None, "the destination buffer of the rectangular copy"),
    ("openmp:omp_target_memcpy_rect_async", "dst"): (None, "the destination buffer of the rectangular copy"),
    ("openmp:omp_get_affinity_format", "buffer"): ("size", "a string buffer of size characters"),
    ("openmp:omp_capture_affinity", "buffer"): ("size", "a string buffer of size characters"),
    ("mpi:mpi_status_c2f", "f_status"): ("MPI_STATUS_SIZE", "a Fortran status, MPI_STATUS_SIZE integers"),
    ("mpi:mpi_status_f2c", "f_status"): ("MPI_STATUS_SIZE", "a Fortran status, MPI_STATUS_SIZE integers"),
    ("mpi:mpi_status_f082f", "f_status"): ("MPI_STATUS_SIZE", "a Fortran status, MPI_STATUS_SIZE integers"),
    ("mpi:mpi_status_f2f08", "f_status"): ("MPI_STATUS_SIZE", "a Fortran status, MPI_STATUS_SIZE integers"),
}

# CUDA's runtime API pairs most array parameters with a count parameter of the
# same call. Listed per function as (count parameter, [arrays it counts]);
# None where no parameter counts it (a kernel's args follow its signature).
_CUDA_COUNTED = {
    "cudaDevResourceGenerateDesc": ("nbResources", ["resources"]),
    "cudaDevSmResourceSplit": ("nbGroups", ["result", "groupParams"]),
    "cudaDevSmResourceSplitByCount": ("nbGroups", ["result"]),
    "cudaDeviceGetHostAtomicCapabilities": ("count", ["capabilities", "operations"]),
    "cudaDeviceGetP2PAtomicCapabilities": ("count", ["capabilities", "operations"]),
    "cudaDeviceGetPCIBusId": ("len", ["pciBusId"]),
    "cudaGraphAddChildGraphNode": ("numDependencies", ["pDependencies"]),
    "cudaGraphAddEmptyNode": ("numDependencies", ["pDependencies"]),
    "cudaGraphAddEventRecordNode": ("numDependencies", ["pDependencies"]),
    "cudaGraphAddEventWaitNode": ("numDependencies", ["pDependencies"]),
    "cudaGraphAddExternalSemaphoresSignalNode": ("numDependencies", ["pDependencies"]),
    "cudaGraphAddExternalSemaphoresWaitNode": ("numDependencies", ["pDependencies"]),
    "cudaGraphAddHostNode": ("numDependencies", ["pDependencies"]),
    "cudaGraphAddKernelNode": ("numDependencies", ["pDependencies"]),
    "cudaGraphAddMemAllocNode": ("numDependencies", ["pDependencies"]),
    "cudaGraphAddMemFreeNode": ("numDependencies", ["pDependencies"]),
    "cudaGraphAddMemcpyNode": ("numDependencies", ["pDependencies"]),
    "cudaGraphAddMemcpyNode1D": ("numDependencies", ["pDependencies"]),
    "cudaGraphAddMemcpyNodeFromSymbol": ("numDependencies", ["pDependencies"]),
    "cudaGraphAddMemcpyNodeToSymbol": ("numDependencies", ["pDependencies"]),
    "cudaGraphAddMemsetNode": ("numDependencies", ["pDependencies"]),
    "cudaGraphAddNode": ("numDependencies", ["pDependencies"]),
    "cudaGraphAddDependencies": ("numDependencies", ["from", "to", "edgeData"]),
    "cudaGraphRemoveDependencies": ("numDependencies", ["from", "to", "edgeData"]),
    "cudaGraphGetEdges": ("numEdges", ["from", "to", "edgeData"]),
    "cudaGraphGetNodes": ("numNodes", ["nodes"]),
    "cudaGraphGetRootNodes": ("pNumRootNodes", ["pRootNodes"]),
    "cudaGraphNodeGetDependencies": ("pNumDependencies", ["pDependencies", "edgeData"]),
    "cudaGraphNodeGetDependentNodes": ("pNumDependentNodes", ["pDependentNodes", "edgeData"]),
    "cudaGraphicsMapResources": ("count", ["resources"]),
    "cudaGraphicsUnmapResources": ("count", ["resources"]),
    "cudaLaunchKernel": (None, ["args"]),
    "cudaLaunchCooperativeKernel": (None, ["args"]),
    "cudaLibraryEnumerateKernels": ("numKernels", ["kernels"]),
    "cudaLibraryLoadData": ("numJitOptions", ["jitOptions", "jitOptionsValues"]),
    "cudaLibraryLoadFromFile": ("numJitOptions", ["jitOptions", "jitOptionsValues"]),
    "cudaMemDiscardAndPrefetchBatchAsync": ("count", ["dptrs", "sizes"]),
    "cudaMemDiscardBatchAsync": ("count", ["dptrs", "sizes"]),
    "cudaMemPrefetchBatchAsync": ("count", ["dptrs", "sizes"]),
    "cudaMemPoolSetAccess": ("count", ["descList"]),
    "cudaMemRangeGetAttributes": ("numAttributes", ["data", "dataSizes", "attributes"]),
    "cudaMemcpyBatchAsync": ("count", ["dsts", "srcs", "sizes"]),
    "cudaSetValidDevices": ("len", ["device_arr"]),
    "cudaSignalExternalSemaphoresAsync": ("numExtSems", ["extSemArray", "paramsArray"]),
    "cudaWaitExternalSemaphoresAsync": ("numExtSems", ["extSemArray", "paramsArray"]),
    "cudaStreamBeginCaptureToGraph": ("numDependencies", ["dependencies", "dependencyData"]),
    "cudaStreamUpdateCaptureDependencies": ("numDependencies", ["dependencies", "dependencyData"]),
}
_CUDA_COUNTED_SECOND = {
    "cudaLibraryLoadData": ("numLibraryOptions", ["libraryOptions", "libraryOptionValues"]),
    "cudaLibraryLoadFromFile": ("numLibraryOptions", ["libraryOptions", "libraryOptionValues"]),
    "cudaMemDiscardAndPrefetchBatchAsync": ("numPrefetchLocs", ["prefetchLocs", "prefetchLocIdxs"]),
    "cudaMemPrefetchBatchAsync": ("numPrefetchLocs", ["prefetchLocs", "prefetchLocIdxs"]),
    "cudaMemcpyBatchAsync": ("numAttrs", ["attrs", "attrsIdxs"]),
}
for _table in (_CUDA_COUNTED, _CUDA_COUNTED_SECOND):
    for _function, (_count, _arrays) in _table.items():
        for _array in _arrays:
            _LISTED_ARRAYS[(f"cuda:{_function}", _array)] = (
                _count, f"counted by {_count}" if _count else "one entry per kernel parameter")

_DESC_OPENS_ARRAY = re.compile(
    r"^\W*(?:an?\s+|the\s+)?(?:optional\s+|output\s+)?(?:two-dimensional\s+)?(?:array|list|set)s?\b",
    re.IGNORECASE)
_DESC_ARRAY_OF_LENGTH = re.compile(r"\barray (?:\()?of (?:length|size)\b(?!\s+1\b)", re.IGNORECASE)
_DESC_ARRAY_OF_POINTERS = re.compile(r"\barray (?:of|containing) pointers\b", re.IGNORECASE)
_DESC_NAMES_LENGTH = re.compile(r"\b(?:of|\()\s*(?:length|size)\s+(\w+)", re.IGNORECASE)
_CONSTANT = re.compile(r"^[A-Z][A-Z0-9_]*$")


def _declarator(entry, param):
    """The parameter's C declaration: binding_type.c where Extract recorded it
    (MPI, CUDA, OpenMP), else its slice of bindings.c.signature."""
    declared = (param.get("binding_type") or {}).get("c")
    if declared:
        return declared
    signature = ((entry.get("bindings") or {}).get("c") or {}).get("signature") or ""
    name = re.escape(param.get("name") or "")
    match = re.search(r"[(,]\s*([^,()]*?\b" + name + r"\s*(?:\[[^\]]*\]\s*)*)(?=[,)])", signature)
    return match.group(1) if match else ""


def _pointer_depth(declarator):
    return declarator.count("*") + declarator.count("[")


def _is_array(entry_key, entry, param):
    """(True, rule) or (False, None)."""
    if param.get("length") is not None:
        return True, "declared"
    decl = _declarator(entry, param)
    if "[" in decl:
        return True, "declared"
    depth = _pointer_depth(decl)
    if param.get("kind") in ("BUFFER", "INDEX_ARRAY") and depth:
        return True, "kind"
    if re.search(r"\bchar\b", decl) and depth == 1:
        return True, "string"
    desc = param.get("desc") or ""
    if depth == 1 and (_DESC_OPENS_ARRAY.search(desc) or _DESC_ARRAY_OF_LENGTH.search(desc)):
        return True, "desc"
    if depth == 2 and _DESC_ARRAY_OF_POINTERS.search(desc) and _DESC_OPENS_ARRAY.search(desc):
        return True, "desc"
    if (entry_key, param.get("name")) in _LISTED_ARRAYS:
        return True, "listed"
    return False, None


def _length_from_extent(entry, param, params_by_name):
    """The count_ref parameter name, when the formal layer states this buffer's
    whole element count; None otherwise."""
    formal = (entry.get("semantics") or {}).get("formal") or {}
    ref = f"param:{param.get('name')}"
    counts = set()
    accesses = [df for df in formal.get("data_flow") or [] if df.get("buffer") == ref]
    for df in accesses:
        extent = df.get("extent")
        source = df.get("source") or {}
        if not isinstance(extent, dict) or df.get("offset") is not None or source.get("kind") == "gathered":
            return None
        counts.add(extent.get("count_ref"))
    if len(counts) != 1:
        return None
    count_ref = counts.pop() or ""
    if not count_ref.startswith("param:"):
        return None
    name = count_ref[len("param:"):]
    counter = params_by_name.get(name)
    if counter is None or counter.get("length") is not None or counter.get("pointer"):
        return None
    return name


def _array_type(length, declarator):
    if re.search(r"\[[^\]]*\]\s*\[", declarator):
        return "2d"
    if isinstance(length, int) or (isinstance(length, str) and _CONSTANT.match(length)):
        return "fixed"
    return "variable"


def complete_array_shape(entries, promotion_log):
    """Fill length/array_type in place on generic (pre-Concretize) entries and
    log every value set. Returns {rule: count} for the caller's summary."""
    shape_of = {r["entry_key"]: r["shape_ref"] for r in promotion_log
                if r.get("field") == "semantics.formal" and r.get("status") == "applied"}
    counts = {}
    for entry_key in sorted(entries):
        entry = entries[entry_key]
        params = entry.get("parameters") or []
        params_by_name = {p.get("name"): p for p in params}
        for param in params:
            is_array, rule = _is_array(entry_key, entry, param)
            if not is_array:
                continue
            name = param.get("name")
            decl = _declarator(entry, param)
            if param.get("length") is None:
                listed_length, reason = _LISTED_ARRAYS.get((entry_key, name), (None, None))
                named = _DESC_NAMES_LENGTH.search(param.get("desc") or "")
                named = named.group(1) if named and named.group(1) in params_by_name else None
                counted = _length_from_extent(entry, param, params_by_name)
                if listed_length or named:
                    param["length"] = listed_length or named
                    source = f"listed ({reason})" if listed_length else "its description"
                    promotion_log.append({
                        "entry_key": entry_key, "field": f"parameters[{name}].length",
                        "status": "applied", "derived_by": "assemble",
                        "note": f"array by rule '{rule}'; length named by {source}"})
                    counts[rule] = counts.get(rule, 0) + 1
                elif counted is not None:
                    param["length"] = counted
                    promotion_log.append({
                        "entry_key": entry_key, "field": f"parameters[{name}].length",
                        "status": "applied", "shape_ref": shape_of.get(entry_key),
                        "note": f"element count from the extent of this buffer's semantics.formal "
                                f"data_flow access (count_ref param:{counted})"})
                    counts["extent"] = counts.get("extent", 0) + 1
                else:
                    param["length"] = "*"
                    promotion_log.append({
                        "entry_key": entry_key, "field": f"parameters[{name}].length",
                        "status": "applied", "derived_by": "assemble",
                        "note": f"array by rule '{rule}'" + (f" ({reason})" if reason else "")
                                + "; length not recorded as a number, parameter or constant"})
                    counts[rule] = counts.get(rule, 0) + 1
            if param.get("array_type") is None:
                param["array_type"] = _array_type(param["length"], decl)
                promotion_log.append({
                    "entry_key": entry_key, "field": f"parameters[{name}].array_type",
                    "status": "applied", "derived_by": "assemble",
                    "note": f"array by rule '{rule}', length {param['length']!r}"})
    return counts
