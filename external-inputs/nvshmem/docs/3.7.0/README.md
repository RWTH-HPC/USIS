# NVSHMEM 3.7.0 documentation (website-derived)

> Only this README is in git. The files it describes are not redistributed (see `why_not_vendored` in `workflow/fetch/manifest.json`); `python3 workflow/fetch/fetch.py` downloads them from NVIDIA's version archive (`archive.docs.nvidia.com/nvshmem/api/3.7.0/`) and checks each against the sha256 pinned there. The live site below now serves 3.8. The archive renders 3.7.0 in a newer theme, so its files differ from the 2026-07-15 mirror described below, but Extract reads identical values from them (all 93 NVSHMEM entries compared field by field, 2026-09-23).

NVSHMEM ships no LaTeX/text specification the way MPI and OpenSHMEM do — its
only spec-equivalent is the hosted HTML documentation. This directory is a
local mirror of that documentation, retrieved because it's the closest thing
NVSHMEM has to `mpi/tex/` or `shmem/tex/`. It is **not** the same kind of
artifact: it's a website snapshot, not a versioned standards document, so
treat it with correspondingly lower authority/stability than the MPI or
OpenSHMEM standard text.

- **Source**: https://docs.nvidia.com/nvshmem/api/index.html
- **Doc version**: 3.7.0, as specified by the project owner. Note this is
  close to but not identical to `external-inputs/nvshmem/implementation/libnvshmem-linux-x86_64-3.7.1_cuda13-archive`
  (3.7.1) — whether docs.nvidia.com hosts a separate 3.7.1 build was not
  checked; if header/doc drift between 3.7.0 and 3.7.1 turns out to matter,
  that's worth resolving before this corpus is treated as authoritative.
- **Retrieved**: 2026-07-15
- **Method**: every page linked from the site's `index.html` was fetched
  (`raw/*.html`, via `curl`), except Sphinx-generated machinery with no
  content of its own (`genindex.html`, `py-modindex.html`, `search.html`,
  `_static/`, `_sources/`). Each page was then converted to Markdown
  (`*.md`, mirroring the same relative path) by
  `workflow/ingestion/html_to_markdown.py`, a deterministic, dependency-free
  HTML→Markdown converter targeting the `<div itemprop="articleBody">`
  container both the NVSHMEM and NCCL doc sites use. `raw/` is kept
  alongside the Markdown as the true provenance artifact, so the conversion
  can be redone without re-fetching if the converter improves.
- **Scope**: full site — introduction, using-NVSHMEM, CUDA-model,
  memory/execution model, constants/handles/env vars, the full API
  reference (`gen/api/*`), Python bindings, examples, troubleshooting/FAQ,
  and legal — per explicit project-owner decision to take everything rather
  than pre-filter to "spec-like" pages only.

## Re-fetching for a new NVSHMEM release

1. Re-run the page-discovery step against the new version's `index.html`
   (page list may have changed — don't assume it's identical).
2. Fetch raw HTML for the discovered pages into a new `external-inputs/nvshmem/docs/<version>/raw/`.
3. Run `python3 workflow/ingestion/html_to_markdown.py <raw_dir> <out_dir> <base_url>`.
4. Update this README's version/date, and `nvshmem-docs` in `workflow/fetch/manifest.json`.
