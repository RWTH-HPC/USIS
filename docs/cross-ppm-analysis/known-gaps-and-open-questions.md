# Known Gaps and Open Questions

What the schema and the generated corpus cannot represent yet, or represent only
partially, and what is out of scope on purpose. Every row was found by trying to
describe a real function and finding the vocabulary insufficient, the same method
that produced every addition to the schema. A logged gap is preferred to a
predicate language wide enough to swallow anything (see
`docs/schema/design-conventions.md`).

- **Open** — a real gap; closing it needs a decision or new vocabulary, and a direction is usually sketched.
- **Accepted** — a known limitation of the current corpus, kept deliberately; the reason is given.
- **Non-goal** — permanently out of scope. Not open work.

## `semantics.formal`

| Item | Status | Detail |
|---|---|---|
| Partitioned communication (MPI `Psend_init`/`Pready`/`Parrived`) | Open — the most significant gap | Needs per-partition sub-extents with independent completion; a `data_flow` entry describes one whole-buffer extent with one completion event |
| Value-dependent blocking (`shmem_{T}_wait_until` and friends) | Open, deliberately unmodeled | "Block until this location satisfies a runtime predicate" has no representation, and adding one would reopen the predicate-language door the formal layer is designed to keep shut |
| `_nbi` nonblocking family (OpenSHMEM/NVSHMEM `put_nbi`, `get_nbi`, `atomic_*_nbi`, `ctx_*`) | Open, judged tractable | No handle to bind completion to; completion is observable only through a later `quiet`/`fence`. Direction: a new `matching.kind` (e.g. `implicit_all_prior`) under which a quiet or fence closes every open window of that participant |
| `ncclGroupStart`/`ncclGroupEnd` | Open | A context bracket with no handle: thread-local call-stack state, not a value flowing through a parameter, so `handle_lifecycle` does not apply |
| `MPI_Type_commit`-style state transitions | Open | The handle stays valid but changes state, and using it before the transition is an error. A fourth `handle_lifecycle` role (`transition`) is plausible; two cases exist (`Type_commit`, `shmem_realloc`), not yet enough to add it |
| Variable-length collectives (OpenSHMEM `collect`; MPI `Gatherv`/`Scatterv`/`Alltoallv`, `Reduce_scatter`) | Open | Offsets assume a statically shaped extent per participant, not a per-participant runtime length |
| Alltoall (`collective.all_to_all_uniform`) | Open | Every PE pair needs an independent offset into *both* the sender's buffer (by destination) and the receiver's buffer (by source): two rank-dependent offset dimensions, where an entry has one `data_flow[].offset` |
| Fetching reads and atomics that return the value (`shmem_{T}_g`, `shmem_{T}_atomic_fetch`/`_swap`/`_compare_swap`/`_fetch_add`, `nvshmem_signal_fetch`, …) | Open | No `dest` parameter for the written value, and the reference grammar has no token for "this call's return value". Options: a `return` pseudo-target in the grammar; an implicit local buffer (a wrong fit: a returned scalar has no address); or declaring these out of formal scope. The `_nbi` fetching variants are unaffected: they take an explicit `fetch` destination |
| `MPI_Put`/`MPI_Get` target buffer | Open — current encoding is a stand-in | The target is `(win, target_disp)` resolved against memory a separate `MPI_Win_create` registered; there is no pointer argument. `rma.put`'s MPI golden binds `target_buffer` to the window handle, so a consumer expecting a region gets a handle. Direction: a tagged `window_region` buffer object. OpenSHMEM/NVSHMEM symmetric-heap puts have a real pointer and are unaffected |
| Typed OpenSHMEM/NVSHMEM collectives (`shmem_int_sum_reduce`, `nvshmem_int_broadcast`, …) | Open | Datatype and reduction operator are baked into the symbol, not passed as `DATATYPE`/`OPERATION` parameters, so `extent_slot.datatype_ref` and `operation_slot` have no `param:` reference to bind. The shapes bind literal tokens (`"type:int"`, `"literal:sum"`), outside the documented `param:` convention. Needs a decision, e.g. a literal-token form in the grammar. Also why `fcollect` fits `collective.gather_to_all` but has no golden example |
| By-value operands in shapes (`shmem_int_atomic_add(dest, value, pe)`) | Open | No slot kind means "a plain non-buffer parameter"; `rma.atomic` binds `value` through `literal_slot`, which stretches that kind's meaning |
| OpenSHMEM active-set collectives (`shmem_broadcast32`/`64`, `collect`, `fcollect`, `alltoall(s)`) | Open — current bindings are wrong | The participant set is arithmetic (`PE_start + i * 2^logPE_stride`, `i < PE_size`) and `PE_root` is an ordinal within it, but `participants[].selector` has no arithmetic. The binder emits `rank in all_pes` and `rank == param:PE_root`, both wrong here, and its `binder_notes` flag the unbound parameters. Direction: a closed `active_set(start, stride, size)` built-in, or declaring the family (deprecated since OpenSHMEM 1.5 in favour of teams) out of scope |
| `pSync`/`pWrk` work arrays | Open, tied to the row above | The active-set collectives synchronize through `pSync`, with checkable rules (initialized; not reused before completion), but it appears in no `data_flow`, `sync.events` or `handle_lifecycle` entry |
| Overlapping or nested RMA epochs on one window | Open | `valid_during` assumes well-nested, non-overlapping epochs; an (erroneous) interleaving of a fence and a lock epoch is not represented |
| Local copy, fill or migration within one process (`cudaMemcpy*`, `cudaMemset*`, `cudaMemPrefetch*`, `omp_target_memcpy*`, `omp_target_memset*`) | Open | Every shape moves data between participants; a single caller copying `src` to `dst` fits none. A `local.copy` shape looks small and waits for a worked example and review. `identity.api_group` is `null` for these too: none of its groups fits |
| Kernel and graph launch (`cudaLaunchKernel`, `cudaLaunchCooperativeKernel`, `cudaLaunchHostFunc`, `cudaGraphLaunch`, …) | Open — scope undecided | Enqueuing compute work is neither communication, lifecycle, inquiry nor synchronization; whether it belongs in this schema at all is undecided |

## Vocabulary and conventions

| Item | Status | Detail |
|---|---|---|
| Parameter kinds without an enum value | Open | Candidates: `CONTEXT`, `SIG_ADDR`/`SIGNAL`, `CONFIG`, `COLOR`; MPI_T scalar indices (`cat_index`, `cvar_index`, …: a position in a tool table, neither a handle nor an index *array*); level-valued `verbosity`/`cb_safety`; OpenMP locks, CUDA events, graph, node, memory-pool, texture and surface handles, and `cudaMemcpyKind`. Each stays `null` until a complete entry needs it and more than one caller exists |
| Cross-model vocabulary: MPI communicator, OpenSHMEM/NVSHMEM team, PE | Open, not evaluated | No standard defines a shared abstraction, so the kinds stay distinct (`COMMUNICATOR`, `TEAM`). Whether a shared "process group" notion would help shape reuse or just be a wrong fit has not been evaluated |
| `inputs[].scope` registry | Open | The registry in `docs/schema/semantics-formal.md` is not yet enforced by Validate |

## Corpus values

| Item | Status | Detail |
|---|---|---|
| `mpi_init`'s `argc`/`argv` have `constraints.not_null = true` | Open, unconfirmed | `MPI_Init(NULL, NULL)` is believed to be standard-legal, which would make both wrong, but no statement was found in the vendored standard sources. Left unchanged until confirmed |
| `execution.procedure_class` is null for 15 MPI procedures whose `I` marker is not in the first name segment (`MPI_Comm_idup`, `MPI_File_iread*`/`iwrite*`, `MPI_*_iflush*`) | Open, narrow | The Forum's `apis.json` assigns `procedure_class` only to operations, and the heuristic reads the marker only as a `mpi_i…` prefix. `heuristics.mpi_nonblocking_by_name` already classifies `execution.blocking` correctly for all 15; applying it here also needs a review of `stages` |
| NVSHMEM AMO and RMA parameter directions | Open | The NVSHMEM docs have no `[IN]`/`[OUT]` labels for the AMO parameters (and for RMA only for `TILE_PUT`/`TILE_GET`), so directions come from const-qualification and are flagged `low_confidence`. Where that heuristic is wrong — `dest` of a read-modify-write atomic — a closed list in the adapter overrides it |
| `semantics.collective.comm_scope = "both"` for `mpi_allreduce`; `topology_aware = false` for `nvshmem_{T}_broadcast` | To verify | Model-assisted values accepted as best available; neither was checked against the exact standard wording |

## Accepted limitations

| Item | Detail |
|---|---|
| NVSHMEM `half` extended-AMO routines (`nvshmem_half_atomic_*`) excluded | The header declares them only under `__cplusplus`, and maps `half` to `__half` there but to `half` elsewhere; Concretize resolves `{CT}` from one flat map per model. Including them needs a per-family type map first. `build_typename_ctype_map()` raises if a typename ever maps to two C types |
| 26 of the 122 OpenMP entries are not implemented by the vendored LLVM runtime | The corpus follows the OpenMP ARB's 6.0 header; LLVM 20.1.7's libomp declares 96 of the routines. The schema has no "which implementation provides this" field, and tracking implementations is out of scope; a consumer should check its own runtime |
| `identity.desc` is null for the 28 OpenMP routines only 6.0 defines | OpenMP 5.2 had a one-sentence summary per routine; 6.0 removed it. Condensing 6.0's multi-sentence `Effect` text is the approach retired for MPI and NVSHMEM, so these wait for a supplement entry |
| `bindings.fortran90` is null for every OpenMP entry | `binding_fortran90` is shaped for MPI and requires three MPI-only fields. The `omp_lib` module form is in `bindings.fortran08`, which fits; the `omp_lib.h` include form has no slot without inventing values |
| `execution.launch` is null for most OpenMP routines | `omp.h` is the same header for host and device compilation, so it cannot say which routines may be called in a target region. Filled from the supplement where known |
| Released handles' `parameters[].direction` corrected by a list | C headers state only const-ness and pointer-ness, so a released pointer (`cudaFree`, `omp_free`, `ncclMemFree`, …) would read as `out`. `workflow/extract/c_header.py`'s `RELEASED_PARAMETERS` names the eight cases, each with the quotation that settles it |

## Non-goals

| Item | Why |
|---|---|
| OpenMP directives (`#pragma omp …`) | The schema models function calls; directives are not functions. The OpenMP runtime library (`omp_*`) is covered |
| Resource leak and double-free detection | A whole-program property. The schema supplies per-entry create/use/destroy facts; the consuming tool reasons across the program |
| Buffer overlap and pointer aliasing | The schema states when an access window is open and on what region; the tool's own alias analysis decides overlap. See `docs/consumers/tool-consumption-model.md` |
| Multi-GPU topology and transfer routing | Which device a pointer belongs to, and GPUDirect RDMA vs. a staged copy, are runtime decisions. `memory_space` states *what kind* of memory, not *how to move it* |
| Generalized requests (`MPI_Grequest_*`) | Completion is arbitrary user code by design; `formal` is `null` |
| MPI Tools Interface (`MPI_T_*`) formal semantics | Introspection into the implementation, not communication between ranks |
| Dynamic process management (`Comm_spawn`, `Comm_accept`/`connect`, `Open_port`) | Creating processes is a different axis from data movement within a fixed participant set |
