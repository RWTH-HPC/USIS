# OpenMP API Specification 5.2 (the standard itself) — kept for `identity.desc`

Unlike `external-inputs/{nccl,nvshmem,cuda}/docs/`, this is **not** a website
snapshot: it is the OpenMP standard, the same tier as MPI's and OpenSHMEM's
`tex/`. It lives under `docs/` rather than `tex/` only because the OpenMP ARB
publishes the specification as PDF and HTML, never as source.

- **Source**: https://www.openmp.org/wp-content/uploads/OpenMP-API-Specification-5-2.pdf
- **Version**: 5.2, November 2021 (669 pages).
- **Retrieved**: 2026-09-11, sha256
  `3a176ab131d7f83ff525aa5449f0e0880138ab444a69d19b4365f7f318381946`.
- **Why the PDF and not the HTML edition**: openmp.org also publishes
  `spec-html/5.2/`, but every routine page of Chapter 18 (Runtime Library
  Routines) returns HTTP 404 there — checked page by page on 2026-09-11, and
  the 5.1 HTML edition carries no routine text either. The PDF is the only
  complete form of the chapter this project needs.

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
against. Generated with **poppler 21.01.0**:

```sh
pdftotext -layout raw/OpenMP-API-Specification-5-2.pdf \
                  text/OpenMP-API-Specification-5-2.txt
python3 workflow/ingestion/openmp_spec_text.py \
        text/OpenMP-API-Specification-5-2.txt md
```

## What reads it, and why 5.2 is still here

**This tier exists for one field: `identity.desc`.** Everything else OpenMP
extraction needs now comes from 6.0 — the routine set and parameter names from
`external-inputs/openmp/standard/openmp-arb-6.0/`, and section references from
`../6.0/`.

5.2 publishes a per-routine **`Summary`** block: one purpose-built sentence, the
same kind of source as OpenSHMEM's `\apisummary{}` macro, which is why
`workflow/extract/openmp/adapter.py` ships it at `static` confidence. **OpenMP
6.0 removed that block.** It replaced it with a `Name`/`Category`/`Properties`
header and a multi-sentence `Effect` paragraph, and condensing a paragraph into
a one-line description is the mechanism this project retired for MPI and NVSHMEM
in July 2026. Rather than reintroduce it, or drop descriptions outright, 5.2
stays vendored and keeps answering the one question it answers better.

Coverage, as a result: of the 122 routines the ARB 6.0 header declares, 94 have
a 5.2 section and therefore a description; the 28 that 6.0 added carry
`desc: null`, flagged and logged the same way any other honest gap is. Two
routines run the other way — `omp_set_nested` and `omp_get_nested` are deprecated,
still declared in the header, and documented here but no longer in 6.0, so they
take their description from this tier and have no `standard_refs`.

`md/` also still carries each routine's own C prototype, which is what supplied
parameter names while LLVM's unnamed declarations were the input. Nothing reads
those any more: the ARB header names its parameters.

If a later specification version restores a one-line summary, this whole
directory becomes deletable — that is the only thing keeping it.
