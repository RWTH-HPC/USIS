# OpenMP API 6.0 — the ARB's own interface definition (C and Fortran)

The OpenMP Architecture Review Board publishes the C/C++ and Fortran interface
definitions for the runtime library routines as source files alongside the
specification document, in a repository tagged per specification version. This
is the 6.0 tag of that repository, and it is the input
`workflow/extract/openmp/adapter.py` reads.

- **Source**: https://github.com/OpenMP/sources, tag `openmp_api_60`
  (tag object `85f3910170a5614e1c841bce62bce27cfab8dc0b`).
- **Retrieved**: 2026-09-12.
- **Files and checksums**:

  | File | sha256 |
  |---|---|
  | `include/omp.h` | `6576dae499d7c8c1bfff41281b6aba73226344491e1f5a6ba5ef8a47c9b08796` |
  | `fortran/omp_lib.f90` | `87cd68c165274543f47661c21dcbb12f0116434dfec728d4e21b1ba31db9d17d` |
  | `fortran/omp_lib.h` | `cad1d1e7ce2308a9c7e7444a1c0200c1a51c6b81e2db9550fb13f43851900d92` |
  | `fortran/omp_lib_kinds.h` | `5c76dbc04a5c7ea48e705ac041a263d404204a1db0732aa0518b5a15edba329b` |

## Why this and not an implementation's header

`external-inputs/openmp/implementation/llvm-20.1.7/` holds LLVM's generated
`omp.h`, which is what this project read until 2026-09-12. Two things the ARB
header does that libomp's does not made the switch worth it:

- **It names every parameter.** libomp declares `omp_init_lock(omp_lock_t *)`,
  so parameter names had to be recovered from the specification PDF's own
  prototypes — a cross-reference that only worked where the arities matched. The
  ARB header declares `omp_init_lock(omp_lock_t *lock)`, making names a literal
  read. Only `omp_get_memspace_num_resources` and `omp_get_submemspace` are still
  unnamed here, and the 6.0 specification's prototypes supply those two.
- **It comes with the Fortran half.** `fortran/omp_lib.f90` is the `omp_lib`
  module's explicit interfaces, which state **INTENT** — the one thing a C
  declaration cannot express. That is where `parameters[].direction` now comes
  from wherever it is stated (81 of the 191 dummy arguments it declares), including every `inout` in
  the OpenMP corpus: the lock routines' `svar` is `INTENT(INOUT)`, which the
  const/pointer heuristic had been reporting as `out`.

The trade is coverage versus realism: the ARB header declares 122 routines to
libomp's 96, so 26 entries now describe routines LLVM 20.1.7 does not implement.
That is recorded as a row in
`docs/cross-ppm-analysis/known-gaps-and-open-questions.md` rather than as a
schema field — the corpus describes the API, and which runtime implements how
much of it is a different question.

## What is here, and what is not

`include/` and `fortran/` hold only the files the adapter reads. The same
repository also ships `include/omp-tools.h` (the OMPT tool interface, 1101
lines) and `include/ompd-types.h`, and a `stubs/` directory of reference
implementations. None is vendored: OMPT and OMPD are separate API surfaces that
this project does not cover, and a vendored copy of an input nothing reads can
only go stale. If the tool interfaces come into scope, they are one `curl` away
at the same tag.

`bindings.fortran90` stays null for every OpenMP entry even though
`fortran/omp_lib.h` is vendored beside the module. OpenMP publishes one Fortran
binding in two forms — the `omp_lib` module and the `omp_lib.h` include file —
while the schema's `binding_fortran90` is shaped for MPI's genuinely distinct
`mpi` module, requiring `use_colons`, `index_overload` and `not_with_mpif`.
Those three fields have no OpenMP meaning, so the slot is left null and logged
rather than filled with invented values. `omp_lib.h` is vendored because
`omp_lib.f90` is not self-contained without its kinds, and because it is the
evidence for that gap.

## Licence

The repository's own notice, which permits this copy:

> Copyright (c) 1997-2024 OpenMP(R) Architecture Review Board.
>
> Permission to copy without fee all or part of this material is granted,
> provided that the OpenMP Architecture Review Board copyright notice appears.
> Notice is given that copying is by permission of the OpenMP Architecture
> Review Board.

The notice appears above and in each vendored file's own header comment. The
upstream README also states that these files "are provided as is and are a
non-normative supplement to the OpenMP API Specification document", and that the
ARB disclaims any warranties.

## Refreshing for a new specification version

1. `curl` the four files from the new tag (`openmp_api_<version>`) into a new
   `openmp-arb-<version>/`, and vendor the matching specification PDF under
   `external-inputs/openmp/docs/<version>/` — the two tiers must be the same
   version, or `identity.standard_refs` will cite sections that do not exist.
2. Point `_STANDARD_DIR` and `_SPEC_REF_DIR` in
   `workflow/extract/openmp/adapter.py` at them.
3. Update this README's tag, date and checksums.
