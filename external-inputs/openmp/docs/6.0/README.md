# OpenMP API Specification 6.0 (the standard itself)

The OpenMP standard, the same tier as MPI's and OpenSHMEM's `tex/`. It lives
under `docs/` rather than `tex/` only because the OpenMP ARB publishes the
specification as PDF and HTML, never as source.

- **Source**: https://www.openmp.org/wp-content/uploads/OpenMP-API-Specification-6-0.pdf
- **Version**: 6.0, November 2024.
- **Retrieved**: 2026-09-12, sha256
  `bcadeebbc13e99a0b7cd4e58099875bd94411d1ae3c7817d5db82968874132db`.
- **Matches**: `external-inputs/openmp/standard/openmp-arb-6.0/`, the ARB's
  interface definition at the `openmp_api_60` tag. The two tiers are deliberately
  the same version: `identity.standard_refs` cites section numbers from this
  document for routines declared in that header.

## Licence

The specification's own notice permits this copy:

> Permission to copy without fee all or part of this material is granted,
> provided the OpenMP Architecture Review Board copyright notice and the title
> of this document appear.

Both appear above and in the vendored PDF itself.

## Layout

| Directory | Contents |
|---|---|
| `raw/` | the specification PDF exactly as downloaded |
| `text/` | `pdftotext -layout` output of it — the whole standard as one text file |
| `md/` | one Markdown file per `omp_*` routine, sliced out of `text/` |

`text/` is committed rather than produced at build time because `pdftotext` is a
third-party binary whose line breaking can shift between poppler releases; the
committed rendition is what `md/` was sliced from and what any future diff is
against. Generated with **poppler 21.01.0**, the same version the 5.2 rendition
beside it was generated with:

```sh
pdftotext -layout raw/OpenMP-API-Specification-6-0.pdf \
                  text/OpenMP-API-Specification-6-0.txt
python3 workflow/ingestion/openmp_spec_text.py \
        text/OpenMP-API-Specification-6-0.txt md
```

The slicer needed no changes for 6.0: it finds routine sections by their
headings and resolves each one's chapter from the document's own chapter
headings, rather than assuming the single chapter 5.2 used. 122 slices, matching
the ARB header's 122 declarations exactly.

## What reads it, and what it does not answer

`workflow/extract/openmp/adapter.py` reads `md/<routine>.md` for two things:

- **`identity.standard_refs`** — each routine's chapter and section. 6.0 spreads
  the runtime library over chapters 21–31 ("Parallel Region Support Routines",
  "Lock Routines", "Memory Management Routines", …) where 5.2 had a single
  chapter 18, which is why the chapter is recorded per slice rather than assumed.
- **Parameter names for `omp_get_memspace_num_resources` and
  `omp_get_submemspace`**, the only two routines the ARB header leaves unnamed.

It does **not** supply `identity.desc`. 6.0 removed the per-routine `Summary`
block that 5.2 published — a purpose-built one-liner, the same kind of source as
OpenSHMEM's `\apisummary{}` — and replaced it with a `Name`/`Category`/
`Properties` header plus a multi-sentence `Effect` paragraph. Condensing that
paragraph into a one-line description is the mechanism this project retired for
MPI and NVSHMEM in July, so `desc` still comes from `../5.2/md/`, which is kept
for exactly this purpose. The 28 routines 5.2 does not define carry `desc: null`.

A second thing 6.0 publishes and this project does not yet read: the per-routine
`Arguments` table, whose `Properties` column is a closed vocabulary
(`iso_c`, `value`, `intent(in)`, `omp`, `default`, …). It was evaluated as a
source for `parameters[].direction` and rejected — it gives
`omp_target_memcpy`'s written `dst` and `omp_free`'s released `ptr` the same
"iso_c, value", so it mirrors the C const-qualification and settles nothing the
header does not. The ARB Fortran module's INTENT does settle it, and is what the
adapter reads instead.
