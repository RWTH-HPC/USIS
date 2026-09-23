# NCCL 2.30 documentation (website-derived)

> Only this README is in git. The files it describes are not redistributed (see `why_not_vendored` in `workflow/fetch/manifest.json`); `python3 workflow/fetch/fetch.py` downloads them and checks each against the sha256 pinned there. The pages are fetched from NVIDIA's archived 2.30.7 documentation (`/deeplearning/nccl/archives/nccl_2307/`), which serves them byte-identical to the live-site mirror described below; the Markdown keeps the original live-site URLs it was converted with.

NCCL ships no LaTeX/text specification the way MPI and OpenSHMEM do — its
only spec-equivalent is the hosted HTML documentation. This directory is a
local mirror of that documentation, retrieved because it's the closest thing
NCCL has to `mpi/tex/` or `shmem/tex/`. It is **not** the same kind of
artifact: it's a website snapshot, not a versioned standards document, so
treat it with correspondingly lower authority/stability than the MPI or
OpenSHMEM standard text.

- **Source**: https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/index.html
- **Doc version**: 2.30 (matches the minor version of
  `external-inputs/nccl/implementation/nccl_2.30.7-1+cuda13.3_x86_64`; the docs site is not
  patch-versioned so an exact 2.30.7 doc build doesn't exist to pin to)
- **Retrieved**: 2026-07-15
- **Method**: every page linked from the site's `index.html` was fetched
  (`raw/*.html`, via `curl`), except Sphinx-generated machinery with no
  content of its own (`genindex.html`, `py-modindex.html`, `search.html`,
  `_static/`, `_sources/`). Each page was then converted to Markdown
  (`*.md`, mirroring the same relative path) by
  `workflow/ingestion/html_to_markdown.py`, a deterministic, dependency-free
  HTML→Markdown converter targeting the `<div itemprop="articleBody">`
  container both the NCCL and NVSHMEM doc sites use. `raw/` is kept
  alongside the Markdown as the true provenance artifact, so the conversion
  can be redone without re-fetching if the converter improves.
- **Scope**: full site — overview/setup, using-NCCL (communicators,
  collectives, data handling, specialized topics), the full API reference
  (`api/*`), Python bindings (NCCL4Py), migration/examples/MPI-integration,
  environment variables, and troubleshooting — per explicit project-owner
  decision to take everything rather than pre-filter to "spec-like" pages
  only.

## Re-fetching for a new NCCL release

1. Re-run the page-discovery step against the new version's `index.html`
   (page list may have changed — don't assume it's identical).
2. Fetch raw HTML for the discovered pages into a new `external-inputs/nccl/docs/<version>/raw/`.
3. Run `python3 workflow/ingestion/html_to_markdown.py <raw_dir> <out_dir> <base_url>`.
4. Update this README's version/date, and `nccl-docs` in `workflow/fetch/manifest.json`.
