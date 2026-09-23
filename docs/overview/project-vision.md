# Project Vision

USIS, the Unified Semantic Interface Specification, is one machine-readable description of the APIs of several parallel programming models (PPMs), written for tools rather than for people.

## The problem

Parallel programming models — MPI, NCCL, NVSHMEM, OpenSHMEM, and to a lesser extent OpenMP and CUDA — each have their own API documentation, their own conventions, and (with the partial exception of MPI) little to no machine-readable semantic description of what each function actually does at an operational level.

Tools that want to reason about programs written against these APIs — code generators, static analyzers, race detectors, formal verifiers — either hand-code per-function knowledge for each PPM separately, or work from documentation that's precise enough for a human to read but not precise enough for a tool to act on.

A running example is a data-race detector in an SPMD compiler IR. A classifier field like `semantics.collective.type = "broadcast"` tells a human "this is a broadcast." It tells a tool nothing about which memory gets touched, by whom, in what order, or when a buffer's "ownership" by an in-flight operation ends — which is exactly the information a race detector needs to catch bugs like mutating a send buffer while a nonblocking send is still in flight.

## The goal

One JSON schema, shared across every PPM, precise enough that:

1. A **code generator** can read an entry and emit an actual transfer or synchronization primitive — not just know that a transfer happens.
2. A **verification/analysis tool** can read an entry and derive a real proof obligation or a real bug-detection rule — data equality, ordering, cross-call matching — without hand-coding per-function logic.

Both consumers should be able to implement against a small, fixed, enumerable vocabulary (a handful of operation kinds, a handful of matching kinds, a handful of source-provenance kinds) regardless of how large the underlying corpus of PPM functions grows. The complexity is allowed to live in the size of the corpus; it is not allowed to live in the vocabulary a consumer has to understand.

## Why "unified" matters

MPI, NCCL, NVSHMEM, and SHMEM have overlapping operations that differ mostly in surface syntax: `mpi_bcast`, `ncclBroadcast`, `nvshmem_broadcastmem`, and `shmem_broadcast32` are the same broadcast, wearing four different parameter lists. A unified schema makes that reuse explicit and machine-visible (see `docs/schema/shape-catalog.md`) rather than requiring every consuming tool to rediscover it independently.

## What "precise enough" means in practice

Two design commitments follow directly from the two-consumer goal:

- **Operational, not just classificatory.** The schema needs a layer that states who reads/writes which memory, where a written value provably comes from, and which ordering and matching rules relate separate call instances to each other — not just a taxonomy label. This became `semantics.formal` (`docs/schema/semantics-formal.md`).
- **Honest about its own limits.** Where the current vocabulary genuinely can't represent something (MPI's partitioned communication, SHMEM's value-dependent `wait_until`), the schema says so explicitly (`null` plus a documented reason) rather than approximating with something that would silently mislead a code generator or a verifier. This matters at least as much as coverage.

## Scope

**In scope:** MPI, NCCL, NVSHMEM and OpenSHMEM as the primary targets. OpenMP and CUDA are experimental, covered in runtime-API scope only (the OpenMP ARB's `omp_*` routines, the CUDA Runtime API); OpenMP directives and the CUDA driver API are not.

**Deliberately out of scope**, and treated as the consuming tool's job rather than the schema's:
- Buffer-overlap / pointer-aliasing analysis (a race detector's own alias analysis, not something the schema encodes).
- Which physical GPU a device pointer belongs to, and transfer routing decisions (GPUDirect RDMA vs. staged host copy) — the schema states *what kind* of memory a buffer lives in (`memory_space`), not *how to move it*.
- Whole-program properties like "was every resource handle eventually freed" — the schema supplies the raw create/use/destroy facts per entry; whole-program reasoning over those facts is the consuming tool's job.
