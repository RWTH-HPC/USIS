# Glossary

Terms are grouped by area. Where a term has two meanings, both are given, with a note on telling them apart.

## Core schema terms

**PPM** — Parallel Programming Model. The category covering MPI, NCCL, NVSHMEM, OpenSHMEM, OpenMP, CUDA.

**Entry** — one function's complete description in the schema: an object with the eight required top-level sections (`identity`, `bindings`, `execution`, `semantics`, `parameters`, `return`, `tool_integration`, `relationships`). Keyed in the corpus by a string like `mpi:mpi_bcast` (`model:function_key`).

**`bindings` (entry-level)** — one of the eight sections. Per-language function signature info (C, Fortran90, Fortran08, LIS, C++). **Not the same thing** as shape-expansion bindings below — see Disambiguation.

**`bindings` (shape-expansion)** — the slot-name → `param:` reference map used when expanding a `shape_ref` against a shape template. **Not the same thing** as the entry-level `bindings` section above.

> **Disambiguation:** if you see `bindings` inside a top-level entry object, it's the per-language signature section. If you see `bindings` next to `shape_ref` and/or `extra`, it's the shape-expansion binding map. `field-provenance.json` explicitly separates these two uses under different `path` entries for exactly this reason.

**`param:name`** — the reference syntax used throughout `semantics.formal` (and elsewhere) to point at a `parameters[]` entry by name instead of repeating type information.

**Reference/selector grammar** — the one small, closed expression grammar (comparisons, `&&`/`||`/`!`, `in`, `param:` refs, a handful of built-ins like `rank`, `self`, `rank_in()`, `is_neighbor()`, `extent_size()`) reused everywhere a predicate is needed in the schema, instead of inventing new ad hoc string syntax per field. See `docs/schema/reference-grammar.md`.

## `semantics.formal` terms

**`participants[]`** — the roles a single call instance decomposes into (e.g. root vs. non-root in a broadcast, origin vs. passive target in a one-sided put). Each has `role_kind`, `calls_function` (false for a passive RMA target), `cardinality`, and a `selector`.

**`data_flow[]`** — one entry per memory access. `op` is one of `read`/`write`/`reduce`/`read_modify_write`. The `source` field states where a written value provably came from.

**`source` (tagged object)** — `structural` (copy from a sibling entry in the same call instance), `reduced` (aggregation over a scoped set of sibling reads, e.g. across `all_participant_instances` or the two-party RMA case `rma_target_prior`; optionally sliced per recipient via `offset`), `gathered` (per-participant assembly with no operator, each contribution at a `placement_offset`; allgather/fcollect), `matched` (resolved at runtime by a `sync.matching` rule against a separate call instance), or `null` (not modeled — implementation/runtime state).

**`sync`** — three parts: `events` (named points, or interval endpoints for epochs), `ordering` (happens-before relationships between events), `matching` (how separate call instances pair up — `collective_rendezvous`, `tag_match`, `peer_match`, `group_match`, `epoch_scoped`).

**Epoch** — an interval, not a point: `open_epoch`/`close_epoch` event types, optionally scoped `access`/`exposure`, bound to a handle. Generalizes the simpler "point event bound to a handle" pattern (used for request completion) to cover RMA synchronization windows (fence, lock/unlock, PSCW) and split collective I/O and persistent operations.

**`handle_lifecycle[]`** — tracks a handle (`REQUEST`, `WINDOW`, `COMMUNICATOR`, `DATATYPE`, `SYMMETRIC_ALLOCATION`, `FILE`, `SESSION`) across `create`/`use`/`destroy`. The same mechanism underlies request completion, RMA epochs, resource lifecycle tracking, split collective I/O and session management. `derived_from` is an optional field for `create` entries that also consume an existing handle (e.g. `Comm_split`).

## Shape catalog terms

**Shape** (`shape_template`) — an authoring-time-only `formal` block with named placeholders (`slots`) instead of concrete `param:` refs. Never appears in a shipped, schema-validated entry.

**Slot** — a named placeholder in a shape template. Seven kinds: `buffer_slot`, `extent_slot`, `selector_slot`, `operation_slot`, `handle_slot`, `index_slot`, `literal_slot` (the last added for plain enum/constant bindings like `role: "create"` that don't fit the other six).

**`shape_ref` + `bindings` + `extra`** — how an entry authors its formal layer against a shape at authoring time: pick a shape by ID, supply the slot bindings, optionally patch on extra fields (e.g. a `tag_match` matching rule) that the base shape doesn't include. Erased by the expander before shipping.

**Expander** — the deterministic algorithm/tool that substitutes `bindings` into a shape's `template`, producing the fully inlined `formal` block that actually gets validated and shipped. Implemented in `workflow/formal/expand.py`; zero model calls, byte-reproducible.

**Golden example** — a hand-verified `shape_ref` + `bindings` pair plus its correct expansion, checked in alongside a shape as part of authoring it. `workflow/formal/test_shapes.py` checks that every golden example still expands byte-identically.

## Workflow terms

The chain is `extract → classify → assign → assemble → validate → provenance → split`
(`workflow/build.py`); `workflow/README.md` describes each stage.

**Extract** — mechanical extraction from the sources in `external-inputs/`. Produces `0_syntactic-api.json`: every syntactic field populated, every field a later stage owns *omitted* (see Staging schema).

**Classify** (Heuristic Classification) — fills the `semantic_heuristic`-tier fields from naming conventions and co-located flags. Mechanical, no model calls, `workflow/classify/`; values carry `static` or `pattern` confidence.

**Supplement** — the curated per-model files `curated/supplement/supplement-<ppm>.json`, which supply the values that need reading the standard's prose (the `semantic` tier). They fill a field only where no earlier stage produced a value; `workflow/supplement/propose.py` computes which ones apply.

**Assign** (shape assignment) — proposes, per function family, which shape its `semantics.formal` follows and the slot bindings. Its output, `curated/formal-assignments.json`, is curated: a human corrects it in place, and a default build does not regenerate it.

**Assemble** — merges the formal assignments and the supplement into the corpus, runs Concretize and the final null-fill, and validates every concrete entry against the strict schema. Produces `2_`, `3_` and `4_final-api.json`.

**Concretize** — expands OpenSHMEM's and NVSHMEM's type-generic family entries (`{T}`/`{CT}` placeholders plus `identity.type_family`) into one concrete entry per type. Deterministic, `workflow/concretize/expand_types.py`.

**Validate** — checks the finished corpus and reports; never modifies or drops an entry. Cross-entry consistency (reference resolution, `variants`/`supersedes` symmetry, `parameters[].length` references, `semantics.formal` grammar and `matched.via` resolution) plus per-entry strict-schema conformance. `build.py --check` runs the same script as a gate that fails on findings.

**Provenance** — one record per value: `{entry, path, tier, state, stage, method, confidence, approved}`. `method` is `mechanical`, `standard_passage` or `model_assisted`; `approved` is set only for model-assisted values, the only ones with a review gate. Keyed by family.

**Split** — partitions the corpus and its provenance report by `identity.model` into the shipped `final-<ppm>-api.json` and `provenance-<ppm>.json`. A pure filter, so `4_final-api.json` is the merged intermediate, not the deliverable.

**Review records** — `curated/review/*.review.json`: which model-assisted proposals a human has read, and the verdict. Provenance reads them into `approved`; nothing is gated on them yet. See `docs/workflow/review-records.md`.

**Confidence levels** (`workflow/common/ir.py`) — named by *how* a value was derived, not by a magnitude: `static` (deterministically certain), `pattern` (a recognized naming or structural convention), `needs_approval` (model-assisted, to be reviewed by a human).

**Field-provenance tier** (`curated/field-provenance.json`) — how a schema field can be derived: `syntactic` (Extract), `semantic` (needs the prose; the supplement), `semantic_heuristic` (a naming heuristic gives a strong prior; Classify), `formal` (the shape mechanism; Assign and Assemble), `derived` (computed from other fields of the same entry), `authoring_only` (exists only before expansion, e.g. `shape_ref`). The tier also decides from which stage on a field must be present in a checkpoint; `semantics.atomic` and `relationships.variants` are the two fields where that stage is later than the one proposing their values.

**Staging schema** — a variant of `api-schema.json` for one intermediate checkpoint, derived in memory (`workflow/staging/derive_schema.py`) from `api-schema.json` and `field-provenance.json`. Fields a stage does not own yet are dropped from `required`, so they are omitted from its output. A `null` that does appear, at any stage, is always a considered answer from the field's owning stage, never a "not computed yet" placeholder.

## Shorthand

**R1–R8** — the eight original design requirements, of which R1 (every field present, explicitly null when inapplicable), R4 and R5 come up most. Full text in `docs/schema/design-conventions.md`.

**Schema versions** — the version is part of the schema's `$id` (currently v0.1.0); `docs/schema/schema-versioning.md` gives the versioning policy.
