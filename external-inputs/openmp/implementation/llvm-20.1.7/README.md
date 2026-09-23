# LLVM 20.1.7 — OpenMP runtime header (vendored; no longer an extraction input)

- **File**: `include/omp.h` — the public header of LLVM's OpenMP runtime
  (libomp), as configured and installed by an LLVM 20.1.7 build (generated at
  build time from `openmp/runtime/src/include/omp.h.var`).
- **Origin**: the RWTH HPC cluster's `LLVM/20.1.7-GCCcore-14.2.0` module,
  `/cvmfs/software.hpc.rwth.de/Linux/RH9/x86_64/intel/sapphirerapids/software/LLVM/20.1.7-GCCcore-14.2.0/lib/clang/20/include/omp.h`
  (EasyBuild build of 2025-11-20).
- **Copied**: 2026-09-11, byte for byte
  (sha256 `f25901e3c7aa5eac1c6f6ea82380fabe9d35591f82082b39c3d624ec00e05454`).
- **Version caveat**: the header's `KMP_VERSION_MAJOR 5` / `KMP_VERSION_BUILD
  20140926` are libomp's own runtime-ABI macros — neither the LLVM release nor
  the OpenMP specification version. The LLVM release is what pins this file.
  Its declarations reach OpenMP 5.2 (`omp_in_explicit_task`, which the header
  itself files under "OpenMP 5.2").
<!-- REUSE-IgnoreStart -->
- **Licence**: Apache License 2.0 with LLVM Exceptions (the header's own
  `SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception`). `LICENSE.TXT` is
  `openmp/LICENSE.TXT` from llvm-project, byte-identical to that file at the
  `llvmorg-20.1.7` tag; it also carries the legacy University of Illinois/NCSA
  and MIT terms that still cover older contributions.
<!-- REUSE-IgnoreEnd -->
- **Scope**: the `omp_*` runtime library routines. The adapter skips libomp's
  `kmp_*` and LLVM's `ompx_*`/`llvm_*` extensions, which are not OpenMP API
  routines. The directive surface (`#pragma omp ...`) is out of scope by
  construction — see `docs/cross-ppm-analysis/known-gaps-and-open-questions.md`.

## Not read since 2026-09-12

`workflow/extract/openmp/adapter.py` read this file until 2026-09-12 and now
reads `external-inputs/openmp/standard/openmp-arb-6.0/` instead: the OpenMP
ARB's own C and Fortran interface definition, which names every parameter (this
header declares most without one, e.g. `omp_init_lock(omp_lock_t *)`) and states
argument INTENT in its Fortran half (C states none, so direction was a
const/pointer heuristic). See that directory's README for the full reasoning.

It stays vendored as the record of what a shipping runtime actually implements,
which the ARB header does not answer: libomp 20.1.7 declares **96** of the
122 routines in the corpus. The 26 it does not are 6.0 additions — the memory
space and allocator queries, device UIDs, free agents and memory partitioners.
That difference is logged as a row in
`docs/cross-ppm-analysis/known-gaps-and-open-questions.md`; it is deliberately
not a schema field, because "which implementation provides this" is a different
question from "what does this API mean", and answering it properly would mean
tracking every implementation rather than the one that happens to be installed
here.

This header also went the other way twice: `omp_target_memset` and
`omp_target_memset_async` are 6.0 routines libomp shipped ahead of the
specification, which is how they entered the corpus in the first place.

## Refreshing for a new LLVM release

Only worth doing to re-measure the coverage difference above.

1. Copy `lib/clang/<major>/include/omp.h` from the new LLVM installation, and
   `openmp/LICENSE.TXT` at that release's tag, into a new `llvm-<version>/`.
2. Update this README's version, date, checksum and the count of `omp_*`
   routines it declares.

No adapter path changes: nothing here is an extraction input.
