# CUDA 13.1 runtime-API documentation (website-derived)

> Only this README is in git. The files it describes are not redistributed (see `why_not_vendored` in `workflow/fetch/manifest.json`); `python3 workflow/fetch/fetch.py` downloads them and checks each against the sha256 pinned there.

A local mirror of the behavioural prose pages of NVIDIA's CUDA Runtime API
documentation, alongside the vendored header in
`external-inputs/cuda/implementation/cuda-13.1.0/`.

- **Source**: https://docs.nvidia.com/cuda/archive/13.1.0/cuda-runtime-api/ —
  the *archived* 13.1 documentation set, chosen over the live pages so the docs
  match the vendored header's version exactly rather than whatever CUDA release
  is current (13.4 at the time of retrieval).
- **Retrieved**: 2026-09-11.
- **Method**: each page fetched with `curl` into `raw/`, then converted to
  Markdown (`md/`, mirroring the same names) by
  `workflow/ingestion/html_to_markdown.py`. `raw/` is kept as the true
  provenance artifact so the conversion can be redone without re-fetching.
  These archived pages are DITA-generated rather than Sphinx, which is why that
  converter gained a second container selector on the same day.
- **Authority**: a website snapshot, not a versioned standards document — the
  same caveat as `external-inputs/{nccl,nvshmem}/docs/`, and a weaker tier than
  MPI's or OpenSHMEM's standard text.

## Scope: the prose pages only, deliberately

The six pages mirrored here carry rules that exist **nowhere in the header**:

| Page | What it settles |
|---|---|
| `api-sync-behavior` | Which copies and fills are synchronous with respect to the host, per transfer direction and per pageable/pinned memory |
| `stream-sync-behavior` | The default stream's semantics, and what the per-thread default stream changes |
| `graphs-thread-safety` | Which graph APIs may be called concurrently |
| `driver-vs-runtime-api` | How the runtime API relates to the driver API |
| `version-mixing-rules` | Which toolkit/driver version combinations are supported |
| `deprecated` | The deprecated-routine list, with the release each was deprecated in |

`curated/supplement/supplement-cuda.json` cites the first of these for
`cudaMemcpy`'s and `cudaMemset`'s `execution.blocking`/`completion` — the values
the header's own doxygen does not state.

**Not mirrored: the 38 `group__*.html` API-reference pages.** They are generated
from the very doxygen comments in `cuda_runtime_api.h` that
`external-inputs/cuda/implementation/` already vendors, so mirroring them would
be a second copy of text the extraction adapter already reads at the source.
This is the opposite of NCCL and NVSHMEM, whose headers are bare signatures and
whose prose exists *only* on the website — which is why their whole doc sites
are mirrored and CUDA's is not.

## Re-fetching for a new CUDA release

```sh
B=https://docs.nvidia.com/cuda/archive/<version>/cuda-runtime-api
for p in api-sync-behavior stream-sync-behavior graphs-thread-safety \
         driver-vs-runtime-api version-mixing-rules deprecated; do
    curl -s -o raw/$p.html $B/$p.html
done
python3 workflow/ingestion/html_to_markdown.py raw md $B
```

Then update this README's version, date and page list (the set of prose pages
has changed between releases before).
