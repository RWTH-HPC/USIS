# Field Semantics: What Each Field Actually Means

`curated/schemas/api-schema.json` is authoritative for every field's *type*, enum, and requiredness. `docs/schema/schema-overview.md` explains why each *section* exists. This document covers the layer between them: for a field whose name does not fully determine its meaning, **what question is it answering, and what is it deliberately not answering?**

A field whose meaning is only implied by its name gets guessed at, consistently and silently: `semantics.collective.in_place`, `semantics.collective.topology_aware` and `semantics.memory.fence_semantics` were each once filled corpus-wide under a plausible but wrong reading. The examples below name such wrong readings where they occurred.

**Scope.** Only fields where a reasonable person can read the name two ways. A field like `identity.model` or `parameters[].name` is not listed; nothing here would help.

**Keep this in sync with `docs/viz/spec_explorer.html`**, which carries the same text in its own field descriptions. That page is how most people will actually read this — this file is the citable source.

---

## `semantics.collective`

### `in_place`

**Question:** does the PPM define a *distinguished in-place mode* for this call — a documented way to make the send and receive buffers coincide?

**Not:** "would aliasing the two buffers happen to work in practice."

The distinction matters because the field feeds `tool_integration.buffer_aliasing`, which a race detector uses to decide whether an overlap between two arguments is a bug or the documented calling convention.

| PPM | How an in-place mode is spelled | Example |
|---|---|---|
| MPI | The `MPI_IN_PLACE` sentinel replaces the send-buffer argument | `mpi_allreduce`, `mpi_reduce`, `mpi_gather`, `mpi_scatter` → `true` |
| NCCL | A per-call aliasing condition, documented individually | `ncclAllReduce`/`ncclBroadcast`/`ncclReduce` (`sendbuff == recvbuff`) and `ncclAllGather`/`ncclReduceScatter` (with a rank offset) → `true`. `ncclAlltoAll` documents in-place as *not supported* → `false` |
| OpenSHMEM / NVSHMEM | Reductions require `source` and `dest` to be either the same symmetric address or fully disjoint | `shmem_*_reduce`, `nvshmem_*_reduce` → `true` |

**The single-buffer trap.** `mpi_bcast` takes one `inout buffer` that is the source on the root and the destination elsewhere. That is not an in-place *variant* — it is the only form the call has, and `MPI_IN_PLACE` is not defined for it. `in_place` is **`false`**. Reading the single-buffer signature as "already in place" is how an earlier corpus ended up with `mpi_bcast: true` next to `mpi_allreduce: false`, which is exactly backwards.

### `topology_aware`

**Question:** is this one of **MPI's neighborhood collectives** — the family requiring a topology communicator built by `MPI_Cart_create` or `MPI_Dist_graph_create`, which moves data along that attached graph rather than across the whole group?

**Not:** "does the implementation use a topology-aware ring/tree algorithm."

The second reading carries no information: essentially every production collective in every PPM uses topology-aware algorithms. Under it, an earlier corpus marked every NCCL collective `true` and every MPI collective `false` — precisely inverted, since the neighborhood family is an MPI-only concept and NCCL has no equivalent.

`true` for: `MPI_Neighbor_allgather(v)`, `MPI_Neighbor_alltoall(v/w)`, and their nonblocking (`MPI_Ineighbor_*`) and persistent (`*_init`) variants. `false` for everything else, in every PPM.

In the formal layer this family needs no shape of its own — it reuses the ordinary gather/alltoall shapes with an `is_neighbor()` scope selector. See `docs/schema/reference-grammar.md`'s note on why that built-in earns its place.

### `reduction_op`

**Question:** does this call *consume a reduction-operator parameter*?

**Not:** "does this call perform a reduction."

`nvshmem_{T}_max_reduce` performs a reduction but takes no operator argument — the operator is fixed by the function name, and its `semantics.formal` says so with `operation_ref: "literal:max"` rather than a `param:` reference. So `reduction_op` is **`false`**. `mpi_allreduce` and `ncclAllReduce`, which take a real `op`/`MPI_Op` argument, are `true`.

The rule of thumb: `reduction_op` is `true` exactly when some `parameters[]` entry has `kind: "OPERATION"`.

### `root_involved` / `algorithm_class` / `comm_scope`

`root_involved` — does a distinguished root play an asymmetric role (`true` for broadcast/reduce/gather/scatter, `false` for allreduce/allgather/alltoall/barrier). `algorithm_class` — the data-movement *shape* (`one_to_all`/`all_to_one`/`all_to_all`), independent of `type`. `comm_scope` — which communicator kinds the call is legal on, not which one a given call site uses.

---

## `semantics.memory`

### `fence_semantics`

**Question:** **which side does this call actually complete or guard?** Not which side issues it — every one of these is issued locally.

| Value | Meaning | Example |
|---|---|---|
| `none` | Not an ordering/completion primitive at all | every ordinary data-movement call |
| `local` | Completes only the caller's own side (source buffers become reusable) | — |
| `remote` | Guards delivery/ordering *at the target PEs*, without waiting for local completion | `shmem_fence`, `nvshmem_fence` |
| `both` | Completes both sides | `shmem_quiet`, `nvshmem_quiet`, and any barrier that implies a quiet |

The fence-vs-quiet pair is the case worth internalizing: **fence orders, quiet completes.** A fence guarantees that operations issued before it are delivered before operations issued after it, and guarantees nothing about when any of them finish. A quiet waits for all of them to finish, locally and remotely. Labelling `fence` as `local` and `quiet` as `remote` — an earlier corpus's values — names the wrong side in both cases.

### `remote_completion`

**Question:** when does this operation's effect become visible at the remote target?

`null` means **this operation has no remote side at all** — a purely local call, or a get, whose only effect lands locally. It does *not* mean "unknown".

This matters most for puts. `shmem_{T}_put` returning does not mean the target's memory has been updated; it means the local source buffer is reusable. Remote completion is guaranteed by a subsequent quiet, so the value is **`after_quiet`**. An earlier corpus had `null` here, which tells a verifier that a put never writes anything remotely — inverting the meaning of the operation.

### `local_completion` vs. `buffer_reuse`

They usually agree, and they are not the same question. `local_completion` — when is the caller's side of the *operation* done? `buffer_reuse` — when may the caller overwrite the buffer? They diverge for buffered sends, where the buffer is copied out (reusable) well before the operation completes.

---

## `execution`

### `launch` vs. `runs_on`

`launch` — where in *program text* the call may be issued from. `runs_on` — what hardware actually performs the work. Independently variable, which is why they are two fields: `ncclAllReduce` is `launch: "cpu"` (host-callable only) and `runs_on: "gpu"` (the reduction happens on-device).

`null` should mean *genuinely undetermined*, not "the source had no qualifier to read". MPI and OpenSHMEM are host-side APIs; their entries say `launch: "cpu"` even though neither standard carries a `__host__`/`__device__`-style marker a classifier could read.

### `gpu_scope`

Which CUDA execution scope must call this **together**. `null` = not GPU-callable at all. A device-callable entry with `gpu_scope: null` is self-contradictory.

NVSHMEM's unsuffixed device API is `thread` (each calling thread issues independently); the cooperative-group forms are separate symbols with explicit `_warp`/`_block` suffixes.

### `execute_once`

`true` **only** for process-lifetime singletons. Not for ordinary collectives. "Every process calls it" is `collective`; "it may be called at most once per process" is `execute_once`. This is a common confusion.

**The criterion is the standard's own restriction, not the init/finalize role** (so `shmem_init` is *not* an example: OpenSHMEM permits repeated initialization). Exactly one of the six models imposes it:

| model | `execute_once: true` | why |
|---|---|---|
| MPI | `MPI_Init`, `MPI_Init_thread`, `MPI_Finalize` | "MPI cannot be initialized more than once; and MPI cannot be reinitialized after `MPI_FINALIZE` has been called" — MPI 5.1, *Process Initialization, Creation, and Management*. `MPI_FINALIZE` is once-only by the same section: once it returns "no MPI procedure may be called in the world model (not even `MPI_INIT`)". The **sessions** model is excluded on purpose — the same section says its resources "can be allocated and freed multiple times in an MPI process" |
| OpenSHMEM | *none* | "The `shmem_init` and `shmem_init_thread` initialization routines **may be called multiple times** within an OpenSHMEM program", each matched by a `shmem_finalize`, and the library "may be re-initialized with a subsequent call" |
| NVSHMEM | *none* | "**Multiple calls to `nvshmem_init` are allowed**", each matched by an `nvshmem_finalize` |
| NCCL | *none* | initialization is per-communicator; an application may hold several at once |
| CUDA | *none* | runtime initialization is implicit and per-device |
| OpenMP | *none* | no init/finalize entry point exists; `omp_init_*` are lock and allocator constructors |

So `shmem_init`/`shmem_finalize` are **`false`**, reversing two hand-written supplement values whose own note read "same reasoning as `mpi_init`" — an analogy to MPI rather than a reading of OpenSHMEM. A checker that flagged a second `shmem_init` would be reporting a legal program.

### `stages` and `procedure_class`

MPI-4's operation taxonomy. `stages` — which of initialization / starting / completion / freeing this call performs at least part of. A blocking operation does all four in one call (`["i","s","c","f"]`); `MPI_Isend` does `["i","s"]` and the matching `MPI_Wait` does `["c","f"]`.

`procedure_class` is the *call-shape* axis (`b-op`/`nb-op`/`p-op`/`pp-op`), distinct from `semantics.collective.type` / `semantics.atomic.operation`, which describe the data operation. It is `null` for calls that are not operations with that axis at all — `MPI_Init`, `MPI_Comm_rank`, `MPI_Type_commit`. `null` here is a real answer, not a gap.

> **Naming-convention warning.** MPI's I-prefix and `_init` suffix are *relative* conventions: `MPI_I<verb>` means "the nonblocking form of `MPI_<verb>`", and `<verb>_init` means "the persistent form of `<verb>`". Neither says anything unless that counterpart exists. Matching on the affix alone misclassified 21 functions — the whole `mpi_info_*` family and `mpi_intercomm_*` as `nb-op` (their names merely start with i), and `mpi_init`/`mpi_session_init` as `p-op` (they *are* initializations, not persistent forms of anything). See `workflow/classify/heuristics.py`.

### `completion`

`ic` (incomplete — leaves a request) | `c` (completing) | `f` (freeing) | `stream_ordered`. The last is for NCCL/NVSHMEM host calls whose completion is implied by CUDA-stream order with no request-like handle, observable only via the caller's own stream/event synchronization.

---

## `identity`

### `since` / `deprecated_in`

Version strings, never booleans. `deprecated_in` is the version that deprecated the function, `null` if current.

**Format:** `<PPM>-<version>` — `MPI-2.0`, `OpenSHMEM-1.5`, `NCCL-2.7`, `NVSHMEM-1.0` — enforced by a `pattern` in the schema.

> **Granularity warning.** OpenSHMEM's changelog resolves to a *content file*, and a content file can document routines with different histories. `shmem_broadcast.tex` holds both the team-based `shmem_broadcast` that 1.5 added and the `shmem_broadcast32/64` that the same release deprecated. File-level attribution reported the deprecation release as the introduction release. Where the source cannot distinguish the two, Extract emits `null` + a flag rather than guessing, and `curated/supplement/supplement-shmem.json` fills it per function.

### `desc`

**One sentence.** Not a paragraph, not the standard's full description block. Three of the four PPMs now have `desc` extraction retired entirely (MPI, NVSHMEM, NCCL) because their sources' prose is arbitrary-length by nature and truncating it loses meaning rather than summarizing it; those values come from `curated/supplement/supplement-<ppm>.json`. OpenSHMEM keeps mechanical extraction — its `\apisummary{}` macro is a purpose-built one-sentence summary.

### `bindings.<lang>.name` — one canonical name per binding, and why no alias list

Each binding sub-object holds exactly **one** name, and the two Fortran bindings hold *different* ones. That is not an inconsistency to be reconciled with an alias array — it is the MPI standard's own convention, visible in its two auto-generated binding appendices:

| Appendix | Binding | Spelling |
|---|---|---|
| `appLang-FNames.tex` | `mpif.h` / `USE mpi` → `bindings.fortran90` | `MPI_BSEND(BUF, COUNT, DATATYPE, ...)` |
| `appLang-F2008Names.tex` | `mpi_f08` → `bindings.fortran08` | `MPI_Bsend(buf, count, datatype, ...)` |

The schema encoded this from the start — `binding_fortran90.name`'s example is `'MPI_COMM_RANK'` and `binding_fortran08.name`'s is `'MPI_Comm_rank'`. So `MPI_SEND` and `MPI_Send` are not two spellings of one name needing an alias slot; they are two *different bindings*, each with one name, already stored separately.

**Case variants within a single binding are not distinct symbols.** Fortran is case-insensitive: `MPI_SEND`, `mpi_send` and `MPI_Send` are the same procedure, and a code generator may emit any casing. There is nothing to alias, which is why one `name` field per binding is complete rather than lossy. Contrast C, where `MPI_Send` and `PMPI_Send` genuinely are two symbols — and which is exactly why `tool_integration.profiling_name` exists as its own field rather than as an alias entry.

> **Deliberately out of scope: linker symbols.** A Fortran compiler mangles `MPI_SEND` to something like `mpi_send_`, and the mangling differs between gfortran and ifort. That is compiler ABI, not source API, and is not derivable from the standard — so it is not modeled here, on the same principle that keeps buffer-overlap analysis in the consuming tool.

Because every real alias is covered per binding, there is no separate alias field. `apis.json` supplies an explicit Fortran 90 name only for the 18 callback typedefs (which also drop the `MPI_` prefix, e.g. `COMM_COPY_ATTR_FUNCTION`); for every other routine Extract upper-cases the C name.

---

## `return`

### `kind`

What the returned value *represents*, which the C type alone does not settle.

| Value | Meaning |
|---|---|
| `ERROR_CODE` | A status: success/failure, no other information |
| `RESULT` | The object the call produced — an allocation or address (`shmem_malloc`'s `void*`) |
| `value` | A datum the call computed or fetched (`shmem_my_pe`'s PE number, a typed atomic's fetched value) |
| `bool` | A predicate answer (`shmem_test_lock`, the `*_accessible` pair) |
| `void` | Nothing returned |

> **`int` is overloaded** in the OpenSHMEM-lineage APIs: a status for `shmem_team_split_strided`, a PE number for `shmem_my_pe`, a predicate for `shmem_test_lock`. Mapping "non-void ⇒ `ERROR_CODE`" mislabelled 58 entries, telling consumers that `shmem_malloc` returns a status rather than the allocation. See `workflow/extract/return_kind.py`.

### `value_kind`

What a returned datum **is**, in the vocabulary `parameters[].kind` uses — so a fact reads the same whether the call writes it through a pointer or returns it. `MPI_Comm_rank(comm, &rank)`'s `rank` is `RANK`, and so is `shmem_my_pe()`'s return.

Non-null only when `kind` is `value`. The schema has no conditional to say so, so `workflow/validate/consistency.py` checks it. `null` for every other `kind`, and for a value with no fitting kind (a fetched atomic, a time, a handle conversion).

| Value | Returned by |
|---|---|
| `RANK` | `shmem_my_pe`, `shmem_team_my_pe`, `shmem_team_translate_pe` and their NVSHMEM counterparts; `omp_get_thread_num`, `omp_get_ancestor_thread_num` |
| `TEAM_SIZE` | `shmem_n_pes`, `shmem_team_n_pes` and their NVSHMEM counterparts; `omp_get_num_threads`, `omp_get_team_size` |
| `DEVICE` | `omp_get_device_num`, `omp_get_default_device`, `omp_get_initial_device`, `omp_get_device_from_uid` — each returns a device number. `omp_get_num_devices` returns a count and stays `null`. |

> **Deliberately `null`.** `omp_get_max_threads` returns "an upper bound on the number of threads that could be used to form a new team" — a bound, not the size of a team. `omp_get_team_num` and `omp_get_num_teams` are a position in, and the count of, a teams region's *teams*; a team is not a member of one, so `RANK`/`TEAM_SIZE` would be near-misses.

### `possible_errors` / `possible_successes`

Arrays of short **tokens** (`"MPI_ERR_COMM"`, `"ncclSuccess"`), never sentences. An empty array is a real answer — a `void`-returning routine reports no status at all.

---

## `parameters[]`

### `memory_space`

What *kind* of memory the buffer lives in — deliberately not how to move it. Multi-GPU routing (GPUDirect RDMA vs. a staged host copy) is a consuming tool's job. See `docs/schema/gpu-memory-semantics.md`.

`either` is the CUDA-aware-MPI case: not fixed by the symbol, resolved at the call site, and always paired with a `tool_integration.context_dependencies` entry. `symmetric_heap` is its own value rather than folding into `device` because a symmetric address resolves to the same logical offset on every PE, so no address translation is needed.

### `length` and `array_type`

**Question:** is this parameter an array, and how many elements does it hold? Each value of `length` has exactly one meaning:

| `length` | Meaning | Example |
|---|---|---|
| an integer | that many elements | – |
| a sibling parameter's name | as many elements as that parameter's value, in units of the buffer's datatype where it has one | `MPI_Send`'s `buf`: `"count"`; `shmem_int_put`'s `dest`: `"nelems"`; `MPI_Cart_create`'s `dims`: `"ndims"` |
| a PPM constant | as many elements as that constant | `MPI_Comm_get_name`'s `comm_name`: `"MPI_MAX_OBJECT_NAME"` |
| `"*"` | an array whose length is not recorded as a number, parameter or constant: it depends on an object passed in, on several parameters, or on a terminator, or the source does not say. `desc` says more where the source does | `MPI_Allgatherv`'s `recvcounts` (group size of `comm`), `ncclAllGather`'s `recvbuff` (`sendcount` × ranks), a C string |
| `null` | **not an array**: a scalar, a handle, or a pointer to one value | `MPI_Send`'s `count`, `MPI_Comm_rank`'s `rank`, `cudaMalloc`'s `devPtr` |

`array_type` is `null` exactly when `length` is. Otherwise it is `fixed` (an integer or constant length), `2d` (a declared `T x[][n]`, such as `MPI_Group_range_incl`'s `ranges`; `length` holds the outer dimension and the C type the inner one) or `variable`.

**Not:** the number of bytes. A buffer's `length` counts elements of its datatype, as `semantics.formal`'s extent does.

`"*"` is the MPI Forum binding tool's own marker for an array no parameter counts, and `*` can never be a parameter name, so it cannot be misread as one. Extract sets both fields where the source states them (MPI's `apis.json`); `workflow/assemble/array_shape.py` completes them for every other array, and its docstring lists the rules. Lengths that come from a shape's extent are attributed to that assignment in the provenance report and are reviewed with it.

### `constraints.not_null`

`null` = **no nullability constraint asserted**, either because it cannot apply (a by-value parameter) or because a blanket `true` would be wrong (`MPI_STATUS_IGNORE`, `MPI_Init(NULL, NULL)`). A consumer derives no proof obligation from `null`.

### `kind`

`null` = no fitting value in this deliberately incomplete enum. New values are added only when a complete worked entry needs one; open candidates are listed in `docs/cross-ppm-analysis/known-gaps-and-open-questions.md`.

`BOOL` is a true/false *predicate answer* — MPI's `flag` out-parameter and by-value `reorder`. `STRING` is a text buffer — `port_name`, `datarep`, `comm_name`, `desc`, and friends. `OPAQUE_STATE` is a `void *` the implementation stores and hands back untouched (`extra_state`, `user_data`).

> **What `BOOL` is not.** Three near-misses were excluded by reading each parameter's own `desc`, and the distinction is the point of the value: `provided` is a thread-support *level* (`MPI_THREAD_SINGLE`…`MULTIPLE`), `result` is `MPI_Comm_compare`'s four-way `MPI_IDENT`/`CONGRUENT`/`SIMILAR`/`UNEQUAL`, and `periods` is an *array* of booleans while `BOOL` is scalar. `value` and `version` are excluded from `STRING` for a different reason — the corpus spells both with `char*` in some functions and `int*` in others, so neither is settleable by name alone. The MPI_T scalar-index family (`cat_index`, `cvar_index`, `pvar_index`, `source_index` — a position in a tool-interface table, neither a handle nor an array) stays null too.

`TEAM_SIZE` is the number of members of a team, group or communicator. The enum lives in `$defs/parameter_kind`, shared with `return.value_kind`. Rank and team-size out-parameters are not `SCALAR`: the `rank` of `MPI_Comm_rank`, `MPI_Group_rank`, `MPI_Cart_rank` and `ncclCommUserRank` is `RANK`; the `size` of `MPI_Comm_size`, `MPI_Comm_remote_size` and `MPI_Group_size`, and `ncclCommCount`'s `count`, are `TEAM_SIZE`.

> **Why not a bare `SIZE`, and why per function.** A pointer named `size` is a byte size in `MPI_Type_size` and `MPI_Pack_size` and a file offset in `MPI_File_get_size`, and those stay `SCALAR`. The name cannot tell them apart, so `TEAM_SIZE` comes from an explicit list of functions, never from the parameter name. `RANK` needed nothing new: it already covered every rank value (`dest`, `source`, `root`, `pe`), and a caller's own rank is one more.

Three more kinds, each with parameters in more than one model:

| Kind | What it is | Where |
|---|---|---|
| `THREAD_LEVEL` | A thread-support level (`MPI_THREAD_SINGLE`…`MULTIPLE` and the OpenSHMEM/NVSHMEM equivalents) | `required`/`provided` of `MPI_Init_thread`, `MPI_Query_thread`, `MPI_T_init_thread`; `requested`/`provided` of shmem/nvshmem `_init_thread` and `_query_thread` |
| `DEVICE` | A device number (ordinal), by value or through an `int*` | CUDA's `device`/`peerDevice`/`srcDevice`/`dstDevice`; OpenMP's `device_num`, `dev`, `src_device_num`/`dst_device_num`; `ncclCommCuDevice`'s `device` |
| `SIG_OP` | The signal operator of the OpenSHMEM/NVSHMEM `*_put_signal` family | `sig_op` |

> **Left out on purpose.** Arrays of devices (`devs`, `devlist`, `device_arr`) stay `null`: `DEVICE` is scalar, the same line that keeps `periods` out of `BOOL`. `verbosity` and `cb_safety` are levels, but not thread levels. `SIG_OP` is split from `OPERATION` because its values are signal-update constants, a domain disjoint from `MPI_Op`/`ncclRedOp_t`, so a consumer dispatching on `OPERATION` would mistake one for the other.


---

## `tool_integration`

### `invariants`

Preconditions in the shared reference grammar (`docs/schema/reference-grammar.md`). This is the **only** context where bare parameter names (`count >= 0`), bare PPM constants (`comm != MPI_COMM_NULL`), and the `comm_size()` built-in are legal — elsewhere the grammar requires the `param:` prefix. An empty array means the call has no symbol-level precondition, not that none was sought.

### `buffer_aliasing`

`forbidden` | `allowed` | `in_place_only` | `null`. Mirrors `semantics.collective.in_place`: a call with a documented in-place mode is `in_place_only` (the buffers may coincide, but only in exactly that form). `null` = the call has no user-supplied buffer parameters at all.

### `context_dependencies`

The escape hatch for any field *elsewhere in the same entry* whose effective value is not fixed by the function symbol. Each entry names the field by dotted path, states the default, and lists what it actually depends on. An empty array means every field in the entry is a fixed contract — the canonical users are NCCL's `blocking` (depends on communicator config and group nesting) and CUDA-aware MPI's `memory_space`.

---

## `semantics.formal`

Covered in full by `docs/schema/semantics-formal.md`; only the cross-cutting traps are repeated here.

- **`formal: null`** means the operational layer does not earn its keep for this entry (query/management calls whose correctness is carried by `execution.stages` and `tool_integration.invariants`). It must **never** mean "not yet computed": in intermediate checkpoints a field whose owning stage has not run is *omitted*, not null.
- **`participants[].calls_function: false`** is load-bearing. It tells a static analyzer that the passive target of a one-sided operation has no matching call site on that rank — a distinction naive collective-matching checkers get wrong.
- **`data_flow[].source`** is where the verification value lives. A write with `source: null` asserts the value came from unmodelled runtime state; do not use it as a placeholder for "not worked out".
- **Consistency with `execution.collective`.** If `execution.collective` is `true`, the formal block must say so too — a `many`-cardinality participant and a real `matching` rule. Collective lifecycle calls (`ncclCommInitRank`, `shmem_malloc`, …) therefore use `resource.collective_lifecycle`, not the single-participant `resource.lifecycle`; asserting both "every PE must call this" and "no matching applies" would make a matching checker skip exactly the calls most likely to deadlock.

---

## Known gaps this document does not paper over

- **OpenSHMEM's active-set collectives.** `shmem_broadcast32`'s participant set is `PE_start + i·2^logPE_stride` for `i < PE_size`, and its `PE_root` is an *ordinal within that active set*, not an absolute PE number. The selector grammar has no arithmetic (deliberately — arithmetic is legal only in `data_flow[].offset`), so neither is currently expressible. Logged, not guessed at.
- **`wait_until`-style value-dependent blocking.** Representing "block until this memory location satisfies a runtime predicate" would require extending the reference grammar to arbitrary value comparisons, which the design rules out. `nvshmem_{T}_wait_until` and `shmem_{T}_wait_until` therefore have no formal block.

See `docs/cross-ppm-analysis/known-gaps-and-open-questions.md` for the full list.
