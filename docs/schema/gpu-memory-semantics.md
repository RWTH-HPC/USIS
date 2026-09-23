# GPU and Heterogeneous Memory Semantics: `memory_space`

## The gap this fills

`execution.launch`, `execution.runs_on`, and `execution.gpu_scope` describe a call's *execution locus* — where in program text it may be issued from, what hardware processes it, at what granularity. None of them say where the **memory being touched** actually lives: host RAM, device memory, or a PGAS symmetric heap. This is a different axis, and — the key finding that motivated adding a field for it — **it is not derivable from the other fields.**

## The counterexample that proved it's a separate axis

CUDA-aware MPI. Its execution fields are unambiguous and give no hint of GPU involvement:

```json
"execution": { "launch": "cpu", "runs_on": "cpu", "gpu_scope": null }
```

Host-callable only, host-executed progress engine. And yet `buf` in `MPI_Send(buf, ...)` can legally be a **device pointer** — a CUDA-aware implementation detects this and routes through GPUDirect RDMA or a staged copy instead of a plain host `memcpy`. Same symbol, same `launch`/`runs_on`, two entirely different data paths depending on what pointer value shows up at the call site. Before this field existed, `data_flow`'s `buffer: "param:buf"` gave a code generator zero information about which path to emit.

## Where memory space is fixed vs. where it genuinely varies

| Case | Memory space | Why |
|---|---|---|
| `nvshmem_int_put`'s buffers | always `symmetric_heap` | Only symmetric-heap allocations can participate — structurally guaranteed |
| A CUDA kernel's device-pointer args | always `device` | Device code can't dereference an ordinary host pointer (barring managed memory) |
| `MPI_Send`'s `buf` under CUDA-aware MPI | `host` **or** `device` | Genuinely a property of the argument at the call site, not of the symbol |

## The field

Added to `parameters[]`, not to `data_flow` — keeping with the project's convention that `parameters` stays the single source of truth for anything about an argument, referenced elsewhere via `param:`. Duplicating it into `data_flow` would create a second place it could drift out of sync.

```json
{ "name": "buf", "kind": "BUFFER", "direction": "in",
  "memory_space": "host" | "device" | "symmetric_heap" | "unified" | "either" | null }
```

| Value | Meaning |
|---|---|
| `host` | Ordinary CPU-addressable memory |
| `device` | GPU-resident memory, not host-addressable |
| `symmetric_heap` | PGAS symmetric allocation — same logical offset resolves on every PE, no address translation needed the way an arbitrary device pointer would |
| `unified` | CUDA unified/managed memory, addressable from either side |
| `either` | Not fixed by the symbol — resolved at the call site; pairs with a `tool_integration.context_dependencies` entry |
| `null` | Not applicable (non-buffer parameters) |

For the `either` case, the existing "not fixed by the symbol alone" mechanism (already built for NCCL's runtime-dependent `blocking`, see `docs/schema/schema-overview.md` §`execution`) covers it without new machinery:

```json
{ "field": "param:buf.memory_space",
  "default_value": "host",
  "depends_on": ["pointer provenance of the argument bound to buf", "whether the MPI implementation was built with CUDA-aware support"],
  "note": "A code generator cannot resolve this from the symbol alone; requires the consumer's own pointer-provenance analysis." }
```

## Why `symmetric_heap` is its own value rather than folding into `device`

A symmetric-heap address resolves to the same logical offset on every PE, so a code generator doesn't need address translation or inter-process communication the way it would for an arbitrary device pointer on a remote GPU. That distinction was judged worth encoding explicitly rather than leaving for the consuming tool to rediscover.

## Explicit non-goals

`memory_space` states *what kind* of memory a buffer lives in. It deliberately does not attempt two adjacent questions, both logged as explicit non-goals rather than half-solved:

- **Which physical GPU** a device pointer belongs to, in a multi-GPU node.
- **Transfer routing** — whether a transfer should go through GPUDirect RDMA versus a staged host copy.

Both are backend/runtime decisions, not structural facts about the API symbol — the same reasoning that already kept buffer-overlap resolution out of `data_flow` and left it to a consuming compiler's own alias analysis (see `docs/consumers/tool-consumption-model.md`).

## Streams

A CUDA stream parameter (`ncclAllReduce`'s `stream`) has its own `parameters[].kind`, `STREAM`, rather than the nearest existing value (`KEY`).
