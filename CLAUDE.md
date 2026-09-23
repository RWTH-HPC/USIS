# CLAUDE.md

This file is persistent working memory for Claude Code sessions on this project. It does not duplicate the full documentation — it tells you what the project is, what to read first, and what must stay true across every future session.

## Project overview

This project is **USIS**, the **Unified Semantic Interface Specification** — a single JSON schema describing the API surface of multiple parallel programming models (PPMs): MPI, NCCL, NVSHMEM, OpenSHMEM (SHMEM), with OpenMP and CUDA as experimental, lower-priority additions — covered since 2026-09-11 in runtime-API scope (the OpenMP ARB's `omp_*` routines, the CUDA Runtime API). One JSON schema, one entry format, used across all of them, so that tools consuming this data (code generators, formal verifiers, race detectors) implement against one interface instead of one per PPM.

The schema has two audiences downstream:
1. **Code generators** — need enough operational detail to emit an actual data transfer or synchronization primitive, not just a classification label.
2. **Verification/analysis tools** — need enough detail to write real proof obligations (data-equality, ordering, matching) and catch real bugs (e.g. a race detector for the SPMD IR tool catching buffer-reuse-during-in-flight-send bugs).

That two-audience requirement is why the schema evolved from a pure classification format into one with an operational data-flow/synchronization layer (`semantics.formal`) — see `docs/schema/semantics-formal.md`.

## Project philosophy

- **Enumerable vocabulary over embedded logic.** Every field is a closed enum, a structured object, or a reference into another field — never a predicate/expression language a consumer has to parse. When a real case doesn't fit the current vocabulary (e.g. MPI's partitioned communication, SHMEM's `wait_until`), the answer is to log it as an explicit gap (`null` + documented reason), not to add a general-purpose expression grammar that could swallow anything. This has been the single most consistently defended design principle across the whole project — do not compromise it to make one hard case fit.
- **"Always present, explicitly null" beats "present or omitted" — for the final entry.** A field that doesn't apply to a given entry is still present in the JSON with value `null`, never left out, once every workflow stage has run. **Resolved 2026-07-20:** this does *not* extend to intermediate staging artifacts. A field's owning stage hasn't run yet → the field is *omitted*, not null; a field's owning stage has run and found nothing → the field is present as `null`. The old approach (staging schemas widening not-yet-legitimate fields to also accept `null`) left a real ambiguity unresolved — a staging `null` and a final `null` were byte-identical once a field also had a legitimate final-state null. Omission removes that ambiguity outright.
- **Design by concrete example, not by abstraction first.** Every mechanism in this schema (the tagged `source` object, `handle_lifecycle`, the shape catalog, `memory_space`) was arrived at by trying to write a real worked example for a real function, finding the vocabulary insufficient, and extending it minimally. Don't design new schema mechanisms speculatively — find the function that needs it first.
- **Don't force a wrong fit.** When an operation is close-but-not-quite covered by an existing shape or pattern (e.g. `MPI_Compare_and_swap` vs. the SHMEM-shaped `rma.atomic`), write it out fully rather than silently reusing the near-miss. A wrong fit is worse than an honest gap, because it produces plausible-looking wrong output instead of an obvious missing one.
- **Shapes are an authoring-time convenience, not a runtime concept.** `shape_ref`/`bindings`/`extra` never appear in a shipped, schema-validated entry. They exist purely so a human (or model) doesn't hand-write near-identical JSON for every broadcast-shaped function across four PPMs. If this boundary ever gets fuzzy, that's a bug in the design, not a feature.
- **Cross-PPM reuse is the real payoff, not within-PPM reuse.** The shape catalog earns its complexity because `mpi_bcast`, `ncclBroadcast`, `nvshmem_broadcastmem`, and `shmem_broadcast32` are the same shape. Point-to-point mode variants (`Send`/`Ssend`/`Bsend`/`Rsend` × blocking/nonblocking/persistent) are the one significant within-MPI reuse case.

## Architecture summary

Two layers, one build workflow connecting them:

1. **The schema itself** (`curated/schemas/api-schema.json`, currently v0.1.0) — 30 `$defs`. Base 8-section entry format (`identity`, `bindings`, `execution`, `semantics`, `parameters`, `return`, `tool_integration`, `relationships`) plus the `semantics.formal` sub-layer (`participants`, `data_flow`, `sync`, `handle_lifecycle`) plus `parameters[].memory_space`. See `docs/schema/` for the full breakdown.
2. **The generation workflow** — built and running end to end for all six PPMs (OpenMP and CUDA since 2026-09-11). Raw PPM sources (MPI tex + the Forum's `apis.json`, OpenSHMEM tex, NCCL/NVSHMEM headers + a website-derived `docs/` mirror, the OpenMP ARB's own `omp.h` and `omp_lib.f90`, and the vendored `cuda_runtime_api.h` + `cuda_device_runtime_api.h`, each beside its own reference tier: the OpenMP 6.0 specification sliced per routine for section references, the 5.2 one kept for the per-routine summaries 6.0 dropped, and CUDA's behavioural doc pages) get mechanically extracted into syntactic-only entries, then enriched (heuristic classification, `semantics.formal` via the shape catalog, the curated per-PPM supplement), merged, concretized, validated, described, and split. See `docs/workflow/`.

   The chain is `extract → classify → assign [curated] → assemble → validate → provenance → split` (`workflow/build.py`). **No stage makes a model call** — every one is a pure function of its inputs, so re-running on unchanged inputs reproduces byte-identical output. Model-assisted material enters only as *curated inputs* (`curated/shapes/`, `curated/formal-assignments.json`, `curated/supplement/`), each gated by a review record in `curated/review/`. The chain runs once over the selected models and **splits at the end**: `instances/4_final-api.json` is the merged intermediate, and the shipped artifacts are `instances/final-<ppm>-api.json` plus `provenance-<ppm>.json` beside each. `--ppm mpi,nccl` restricts which models a build covers (only Extract reads it).

## Repository layout

Three roots, separated by who writes them — `external-inputs/` (vendored third-party sources, one `implementation/` and optional `tex/`/`docs/` per PPM), `curated/` (hand-authored or hand-corrected), `instances/` (everything a build produces, safe to delete). Inside `curated/`: `schemas/` holds **only** JSON Schemas — one per hand-edited format, all checked by `workflow/validate/test_curated.py` — while `shapes/` holds the shape catalog, `supplement/` the per-PPM supplement inputs, `review/` the review records, and `field-provenance.json` sits at the root because it governs the schemas rather than being one. The worked example `mpi-api.json` lives in `docs/schema/examples/`; no stage reads it, `test_grammar.py` validates it in place. `workflow/build.py` runs the whole chain and can redirect all three (`--out`, `--curated-dir`, `--external-inputs`) and select models (`--ppm`), all plumbed to the stage scripts as env vars through `workflow/common/layout.py` — the stage scripts stay argument-free by design. Read `workflow/README.md` and `curated/README.md` before running or moving anything.

What is and is not in git, for licensing and size reasons:

- **`instances/` is gitignored.** The shipped `final-<ppm>-api.json` files are published as GitHub release assets, not committed.
- **Not every input is vendored.** NVIDIA's CUDA headers are proprietary, and the NVIDIA documentation mirrors (`external-inputs/{cuda,nccl,nvshmem}/docs/`) carry no redistribution licence, so none of them is in the repository; `workflow/fetch/fetch.py` installs them from the URLs and sha256s pinned in `workflow/fetch/manifest.json`, and `build.py` refuses to run Extract for a model whose fetched inputs are missing. All downloads come from NVIDIA's versioned archives, not the live sites. The NCCL/NVSHMEM headers (Apache-2.0) and every other PPM's sources are vendored.
- **Licensing follows REUSE.** `REUSE.toml` assigns every path its licence, `LICENSES/` holds the texts; vendored files keep their upstream licence and are never edited to add headers. A new vendored tree needs its own `[[annotations]]` entry.

Older commit messages and documents may use pre-2026-07-22 paths (`inputs/`, `schemas/`, `inputs/<ppm>/supplement.json`); they map to `external-inputs/`, `curated/schemas/` or `curated/shapes/`, and `curated/supplement/supplement-<ppm>.json`.

## Documentation map — read in this order

1. `docs/overview/project-vision.md` — why this project exists, who it's for.
2. `docs/overview/glossary.md` — terminology; several terms are overloaded (e.g. "bindings" means two different things depending on context) and this resolves that.
3. `docs/schema/schema-overview.md` — the base 8 sections.
4. `docs/schema/semantics-formal.md` — the operational layer; this is the technically deepest document in the repo.
5. `docs/schema/field-semantics.md` — what each individual field/subfield actually means, and what it deliberately does *not* mean. Read this before populating or reviewing any field value; it exists because three fields with empty descriptions were each filled corpus-wide under a plausible-but-wrong reading (2026-07-21 field audit).
6. `docs/schema/shape-catalog.md` — the authoring-time reuse mechanism.
7. Everything else in `docs/schema/`, `docs/consumers/`, `docs/cross-ppm-analysis/`, `docs/workflow/` as needed for the task at hand.

## Coding conventions

The workflow is **Python**, standard library only, one script per stage under `workflow/`, each with its own tests beside it.

- Every stage is a pure, deterministic function of its inputs, with zero model/network calls in it — the same inputs always produce byte-identical output. This applies in particular to the formal-layer **expansion** (`workflow/formal/expand.py`: shape template + bindings → fully inlined `semantics.formal`).
- Any tool consuming `semantics.formal` should only ever need to understand: 4 `data_flow[].op` values, 5 `source.kind` values (including `null`), 3 `handle_lifecycle[].role` values, and 5 `sync.matching.kind` values — plus the two string-valued surfaces that are honestly also part of the consumer contract: the reference/selector grammar (now formally specified as EBNF in `docs/schema/reference-grammar.md`) and the `inputs[].scope` registry (`docs/schema/semantics-formal.md`). If a design change would require a consumer to understand more than this small fixed vocabulary, that's a signal the change is wrong — re-read the philosophy section above.

## Design conventions

See `docs/schema/design-conventions.md` for the full list. The short version: closed enums over free text wherever possible; one shared reference/selector grammar reused everywhere instead of ad hoc per-field expression strings; nullable-but-present over omitted; new schema mechanisms justified by a real worked example, not speculation.

## Workflow conventions

- New schema vocabulary (new `data_flow[].op` value, new `source.kind`, new shape) requires a `$id` version bump and a documented rationale — see `docs/schema/schema-versioning.md`.
- **Resolved (2026-07-16), supersedes the original ≥2-function reuse threshold:** when Generate Formal's assignment step finds that no existing shape fits a function, it always escalates to Author Shapes, which always mints a brand-new shape immediately — even for a single current caller — rather than either improvising an inline `formal` block on the spot or leaning on the `extra` deep-merge escape hatch as a holding pattern until a second user shows up. Rationale: a second reuser tends to show up eventually, so waiting doesn't pay for itself, and `extra` used as a waiting room duplicates exactly the pattern the shape catalog exists to avoid. `extra` itself still exists, but is now scoped narrowly to genuinely one-off, non-reusable quirks on an otherwise-good shape match (see `docs/schema/shape-catalog.md`) — never to a near-miss awaiting a second function.
- Every open question or known gap in this project has been deliberately logged rather than silently resolved with a guess. Check `docs/cross-ppm-analysis/known-gaps-and-open-questions.md` before assuming something is undecided by omission rather than by design.

## Source notes

- **MPI**: the MPI Forum's LaTeX repository, plus the machine-readable `apis.json` it ships (since MPI 4.0), both under `external-inputs/mpi/tex/mpi-standard/`.
- **OpenSHMEM**: the specification's own LaTeX sources, `external-inputs/shmem/tex/shmem-standard/`.
- **NCCL/NVSHMEM**: the headers are largely bare signatures, not doxygen-annotated with per-parameter prose. The prose (semantics, memory model, ordering guarantees, per-function descriptions) exists only on each product's hosted HTML documentation (docs.nvidia.com), mirrored as raw HTML + converted Markdown via `workflow/ingestion/html_to_markdown.py` — a website snapshot, not a versioned standard, and not redistributed (see Repository layout).

## Important constraints

- The schema must stay tool-agnostic — do not encode assumptions specific to one downstream consumer (e.g. the SPMD IR race detector) into the schema itself. Buffer-overlap/alias analysis, for example, is explicitly the consuming tool's job, not the schema's.
- Do not add a predicate/expression language to solve a hard case. This has been rejected repeatedly and deliberately; see philosophy above.
- Backward compatibility: `formal` being `null` must always be a safe, meaningful state (query/management calls) — never repurpose `null` to mean "not yet computed" inside the final, shipped schema. **Resolved 2026-07-20:** omission in staging artifacts is what actually keeps this promise now — `semantics.formal` (and every other not-yet-owned field) is *omitted* from staging artifacts until its owning stage has run, so a `null` that does appear, at any stage, is always a real, considered answer, never a placeholder.

## Current status

The chain is built and runs end to end for all six PPMs. The live priority is **review**: all formal-assignment, shape and supplement groups in `curated/review/` are still `status: "unreviewed"`, so the provenance report counts no model-assisted value as approved yet. Nothing is gated on that by design — see `docs/workflow/review-records.md`.

## Recommended development workflow

1. Prefer extending existing `$defs` in `api-schema.json` over adding parallel/duplicate structures — check `docs/schema/` for whether something already exists before adding.
2. Any new shape or new `formal`-layer vocabulary should be grounded in an actual function from an actual PPM spec, worked through by hand first (see "Design by concrete example" in `docs/schema/design-conventions.md`), before being generalized.
3. When in doubt about scope (is this the schema's job, or the consuming tool's job?), default to keeping it out of the schema — this project has consistently erred toward a smaller, closed vocabulary over a more expressive one.

## Guidance for future Claude sessions

- This project's design process valued **explicit gaps over confident guesses**. If you find yourself inventing a plausible-sounding value for something the docs mark as an open question, stop — flag it instead, the way the rest of this project does.
- The project owner works in German and English interchangeably in working notes; documentation and code should stay in English.
