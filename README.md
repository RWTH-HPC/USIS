# USIS — Unified Semantic Interface Specification

USIS is a format for describing the semantics of API-call-based parallel
programming models, for tools that generate code, optimize performance, or check
correctness. This repository also holds a deterministic workflow that builds
USIS instances for MPI, OpenSHMEM, NCCL and NVSHMEM, with experimental support
for OpenMP and CUDA (runtime-API scope).

One JSON schema describes every model, so that a tool implements against one
interface instead of one per model. `mpi_bcast`, `ncclBroadcast`,
`nvshmem_broadcastmem` and `shmem_broadcast32` are written up in the same
structure. Beyond classification (blocking, collective, one-sided, ...), each
entry has an operational layer, `semantics.formal`. It states which data moves
where and which synchronization it implies, in enough detail for a code
generator to emit the transfer and for a verifier to state proof obligations.

## Using the specifications

The built specifications, one `final-<ppm>-api.json` per programming model,
are published as assets on the
[GitHub releases](https://github.com/RWTH-HPC/USIS/releases) rather than
committed. Each file validates against
[`curated/schemas/api-schema.json`](curated/schemas/api-schema.json). For a
small, readable example, see
[`docs/schema/examples/mpi-api.json`](docs/schema/examples/mpi-api.json).

## Building from source

The workflow needs only Python 3 and its standard library.

```bash
python3 workflow/fetch/fetch.py      # once: the inputs that are not vendored (see below)
python3 workflow/build.py            # -> instances/final-<ppm>-api.json, one per model
python3 workflow/build.py --ppm mpi  # only some models
python3 workflow/build.py --help     # options; --list-stages shows the current state
```

The chain is `extract → classify → assign [curated] → assemble → validate →
provenance → split`. No stage calls a model or the network, so the same inputs
always produce byte-identical output. Next to each shipped file,
`provenance-<ppm>.json` has one record per value, saying which stage derived it,
how, and whether a human has approved it. [`workflow/README.md`](workflow/README.md)
describes every stage and option.

### Inputs that are fetched, not vendored

Most third-party sources are vendored under `external-inputs/`, because their
licences allow it. The four below are not, so `workflow/fetch/fetch.py`
downloads them. [`workflow/fetch/manifest.json`](workflow/fetch/manifest.json)
lists every URL the script downloads and every file it writes. Each file has
the sha256 of the copy the released corpus was built from, and a source is
installed only if every one of its files matches. Run
`fetch.py --dry-run` to see the full plan without downloading anything.

| Source | Needed for | Why it is not vendored | Downloaded from |
|--------|------------|------------------------|-----------------|
| CUDA 13.1 runtime headers | `cuda` | NVIDIA proprietary licence | NVIDIA's CUDA redist archive |
| CUDA 13.1 runtime-API prose pages | `cuda` | docs.nvidia.com, no redistribution licence | NVIDIA's archived 13.1.0 docs |
| NCCL 2.30 documentation | `nccl` | docs.nvidia.com, no redistribution licence | NVIDIA's archived 2.30.7 docs |
| NVSHMEM 3.7.0 documentation | `nvshmem` | docs.nvidia.com, no redistribution licence | NVIDIA's version archive (archive.docs.nvidia.com) |

The downloads come from NVIDIA's versioned archives, not the live sites, which
move on to newer releases. NVIDIA's archive serves the NVSHMEM 3.7.0 pages in a
newer page layout than the copy the corpus was first built from; the converter
reads both, and Extract gets identical values from either. `fetch.py --from-dir
DIR` installs from an existing local copy instead of downloading, checked
against the same checksums. `build.py` checks for these inputs before it
starts, so a missing one stops the build instead of producing a thinner corpus.

## Repository layout

Three top-level directories hold the workflow's data. They are separated by
who writes them:

| Directory | Contents | Written by |
|-----------|----------|------------|
| `external-inputs/` | Third-party source material: the MPI and OpenSHMEM standards (LaTeX, plus the MPI Forum's `apis.json`), implementation headers, OpenMP specification text, and the fetched inputs above. | Vendored or fetched. Nothing in the build writes here |
| `curated/` | Hand-authored or hand-corrected: the schema family (`schemas/`), the shape catalog (`shapes/`), the per-model supplement inputs, the shape-assignment proposals, the review records. | A human |
| `instances/` | Everything a build produces: the `final-<ppm>-api.json` files and their provenance, the checkpoints `0_`–`4_`, and the per-stage reports. Gitignored and safe to delete. | `workflow/build.py` |

`workflow/` holds the generation scripts, one directory per stage, each with
its tests. `docs/` holds the documentation; `docs/viz/` has the figures and interactive
HTML explorers of the schema and the workflow.
[`curated/README.md`](curated/README.md) explains what counts as curated and
which file to correct for which kind of mistake.

## Documentation

- [`docs/overview/project-vision.md`](docs/overview/project-vision.md): the problem and who USIS is for
- [`docs/overview/glossary.md`](docs/overview/glossary.md): terminology, including terms used with two meanings
- [`docs/schema/schema-overview.md`](docs/schema/schema-overview.md): the eight sections of an entry
- [`docs/schema/semantics-formal.md`](docs/schema/semantics-formal.md): the operational data-flow and synchronization layer
- [`docs/schema/field-semantics.md`](docs/schema/field-semantics.md): what each field means, and what it deliberately does not
- [`docs/schema/shape-catalog.md`](docs/schema/shape-catalog.md): how one description is reused across models
- [`docs/consumers/tool-consumption-model.md`](docs/consumers/tool-consumption-model.md): how a tool consumes `semantics.formal`
- [`docs/cross-ppm-analysis/known-gaps-and-open-questions.md`](docs/cross-ppm-analysis/known-gaps-and-open-questions.md): what the schema cannot represent yet
- [`workflow/README.md`](workflow/README.md): every stage and option, and the workflow's design notes

## Licence

The project's own work (the schema, curated data, workflow and docs) is
licensed under [Apache-2.0](LICENSES/Apache-2.0.txt). Vendored third-party
sources keep their upstream licences. The repository follows the
[REUSE](https://reuse.software/) specification: [`REUSE.toml`](REUSE.toml)
assigns a licence to every path, and [`LICENSES/`](LICENSES/) holds the texts.
Run `reuse lint` to check.
