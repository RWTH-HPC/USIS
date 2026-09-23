# `workflow/` — the generation workflow

Everything that turns the raw PPM sources in `external-inputs/` into the shipped
`instances/final-<ppm>-api.json` files and their provenance report. This README
is the operational counterpart to `workflow/README.md`: that
document explains *what each component is for and why it exists*, this one
explains *what to type*.

**Start here:** `python3 workflow/build.py --help`.

---

## 1. The wrapper: `build.py`

```
python3 workflow/build.py
```

Runs the chain end to end and writes one `instances/final-<ppm>-api.json` per
programming model, plus `provenance-<ppm>.json` beside each and the two
whole-corpus reports. `4_final-api.json` is still written — it is the merged
corpus the split partitions — but it is an intermediate now, not the deliverable.

**Before the first build**, fetch the inputs this repository does not
redistribute (NVIDIA's CUDA headers and the NCCL/NVSHMEM/CUDA documentation
mirrors):

```
python3 workflow/fetch/fetch.py
```

`build.py` checks for them before Extract and stops if one of the selected
models' inputs is missing, rather than building a corpus with fewer
descriptions. See `fetch/` in §4.

`build.py` is a driver, not a stage. It owns no extraction, classification or
merge logic of its own — every stage is still the same standalone script it
always was, and the wrapper only ever invokes it in a subprocess. Anything
`build.py` can do, you can do by hand; it exists for ordering, preflighting,
and the curated-artifact guard in §2.

### The chain

| # | Stage | Script | Writes | Where |
|---|-------|--------|--------|-------|
| 0 | `extract` | `extract/cli.py` | `0_syntactic-api.json`, `extract-report.json` | out |
| 1 | `classify` | `classify/cli.py` | `1_syntactic-semantics-api.json`, `classify-report.json` | out |
| 2 | `assign` **[curated]** | `formal/assign.py` | `formal-assignments.json`, `review/formal-assignments.review.json` | curated |
| 3 | `assemble` | `assemble/assemble.py` | `2_…`, `3_…`, `4_final-api.json` | out |
| 4 | `validate` | `validate/consistency.py --report` | `validate-report.json` | out |
| 5 | `provenance` | `provenance/report.py` | `provenance-report.json` | out |
| 6 | `split` | `split/by_model.py` | `final-<ppm>-api.json`, `provenance-<ppm>.json` | out |

The last three all read a finished corpus and none of them modifies one:
`validate` re-checks it, `provenance` describes how it was derived, `split`
partitions it. An entry is never dropped, and a validation failure is
informational — the ~24 pure-prose semantic fields are only populated for the
functions the supplement covers, so most entries are missing a required field
and the report says which.

Two things a build deliberately does **not** materialize, because each would
only ever be a stale duplicate of something else:

- **the staging schemas** — each stage derives its own in memory from
  `curated/schemas/{api-schema,field-provenance}.json` (~0.2s). Print one with
  `python3 workflow/staging/derive_schema.py --stage post-extract`.
- **the supplement projection** — `assemble` calls
  `supplement/propose.py`'s `build_proposals()` directly, since which supplement
  values are eligible depends on which fields are still null in the very corpus
  being merged. Inspect it with `python3 workflow/supplement/propose.py
  --summary`; ineligible entries are logged in `4_final-api.json`'s
  `promotion_log` as `supplement_ineligible`.
- **a review worksheet** — the groups it held now live in the review record
  itself, `curated/review/formal-assignments.review.json`, next to the status
  fields a reviewer sets.

(A third used to be listed here: the consolidated provenance report. It became a
real stage on 2026-08-06 — it is not a duplicate of the three per-stage records,
it is their join, and it fills in the mechanical majority that appears in none
of them.)

`--list-stages` prints this table with the current on-disk size and mtime of
every artifact, and the three roots in force.

### The three roots, and which models

| Root | Holds | Option | Env var |
|------|-------|--------|---------|
| `external-inputs/` | Vendored third-party sources: standards, headers, docs mirrors | `--external-inputs` | `PPM_EXTERNAL_INPUTS_DIR` |
| `curated/` | Hand-authored/corrected: `schemas/`, `shapes/`, `examples/`, `supplement/`, `review/`, `field-provenance.json`, `formal-assignments.json` | `--curated-dir` | `PPM_CURATED_DIR` |
| `instances/` | Every build artifact: the checkpoints, the shipped per-model files, and the reports | `--out` | `PPM_OUT_DIR` |

`build.py` exports the chosen roots as those environment variables and every
stage resolves them through [`common/layout.py`](common/layout.py) — so the
stages stay argument-free and runnable standalone, and wrapper and stage can
never disagree about where a file lives. Setting a variable by hand works too:

```bash
python3 workflow/build.py --out /tmp/build-x       # scratch build; instances/ untouched
PPM_OUT_DIR=/tmp/build-x python3 workflow/extract/cli.py   # one stage, same redirect
```

A missing output directory is created, so a redirected build needs no setup.

`--ppm` (env `PPM_MODELS`) travels the same way and restricts which models a
build covers:

```bash
python3 workflow/build.py --ppm mpi              # MPI only
python3 workflow/build.py --ppm nccl,nvshmem     # the two NVIDIA models
```

Only `extract` reads it — it is the only stage that goes to `external-inputs/`
per model; every later stage processes whatever families are in the checkpoint
it is handed. So the chain and the curated artifacts need no per-model
variants, and `split` simply writes fewer files. The curated supplement is
authored against the full API surface, so a restricted build lists the
supplement entries it could not place in `provenance-report.json`'s
`supplement_entries_not_in_corpus` rather than recording them as provenance for
entries the corpus does not contain.

Checkpoints `0_`–`3_` are cumulative: each is the previous one plus one
overlay, so you can open any of them and see exactly what an entry looked like
at that point. `0_`–`3_` are still *generic* (one entry per `{T}` family);
only the `3_ → 4_` step (Concretize) expands families into concrete per-type
entries and null-fills the remainder.

### Choosing which JSONs get written

Stage selection is the mechanism — a stage that doesn't run doesn't write.

```bash
python3 workflow/build.py --to classify     # stop after 1_; nothing merges on top
python3 workflow/build.py --from assemble   # re-merge only, from existing 1_ + curated
python3 workflow/build.py --only extract    # exactly one stage
python3 workflow/build.py --skip classify   # everything except one stage
```

`--from`/`--to` take a stage name and select an inclusive span; `--only` and
`--skip` take comma-separated names. Before running anything, `build.py`
preflights: every input a selected stage needs must already exist on disk or
be produced by an earlier selected stage. A chain that cannot finish fails
immediately rather than after a long `extract`.

`--prune-intermediates` deletes `0_`–`3_` after a successful build, leaving the
shipped per-model files, `4_final-api.json` and the reports — for a minimal
`instances/`. It refuses to run unless `assemble` actually ran in the same
invocation, so it can never delete checkpoints that a stale `4_` was not
built from. The reports and the curated proposal files are never pruned.

`split --split-intermediates` does the opposite, partitioning `0_`–`3_` per
model as well. It is a debugging aid — nothing downstream reads a per-model
checkpoint — so it is off by default.

Other flags worth knowing: `-n/--dry-run` (print the plan and the exact
commands, run nothing), `-q/--quiet` (suppress the stages' own stdout).

### Extras, reachable but not part of the chain

| Flag | Runs | Why it's not in the chain |
|------|------|---------------------------|
| `--check` | `validate/consistency.py`, without `--report` | Same script as the `validate` stage, but exits non-zero on findings — the form for a gate, not for a build |
| `--test` | the eight test suites, before the build; aborts on failure | Fast (~seconds), but not everyone wants it on every run |

---

## 2. Curated artifacts — the thing to understand before running anything

`curated/formal-assignments.json` holds shape-assignment **proposals**, not
derived output: every entry is `confidence="needs_approval"`, and a human reads
them, corrects wrong values *in that file*, and those corrections are what
ships. There is no hand-authored upstream file for a correction to live in
instead — changing `curated/shapes/shapes.json` is right when the *shape* is
wrong and changing `formal/assign.py` is right when the *matching rule* is
wrong, but neither is right when one function simply needs a different answer.

So a default build **does not run its stage**. It consumes whatever is on disk,
the same way a downstream consumer of this repo would:

```
assign      SKIPPED (curated) -- using curated/formal-assignments.json as-is
            (975 KiB, 2026-07-22 10:56); --regenerate formal to rebuild
```

Rebuilding it is an explicit act, and destroys hand corrections:

```bash
python3 workflow/build.py --regenerate formal   # or --regenerate all
```

Before overwriting, the old file is copied to
`curated/backups/<name>.<timestamp>.json` (git-ignored; disable with
`--no-backup`). Naming a curated stage in `--only` regenerates it too —
`--only assign` is the same as regenerating.

**The supplement inputs need no such guard.** They are already the
hand-authored source: `assemble` projects them onto the corpus in memory on
every run, so a correction to `curated/supplement/supplement-<ppm>.json` takes
effect on the next merge with nothing else to regenerate.

**Bootstrap exception:** if a curated artifact does not exist at all, there are
no edits to lose, so its stage runs automatically and says so in the plan.
`--no-bootstrap` turns that into an error instead.

The right loop when you correct a proposal by hand is therefore:

```bash
$EDITOR curated/formal-assignments.json
python3 workflow/build.py --from assemble        # re-merge only; nothing upstream is touched

$EDITOR curated/supplement/supplement-mpi.json
python3 workflow/build.py --from assemble        # projected in memory during the merge
```

See [`curated/README.md`](../curated/README.md) for what lives in each curated
sub-directory and which file to correct for which kind of mistake.

---

## 3. Design notes

**Why the chain splits at the end rather than running per model.** Exactly one
step is corpus-wide rather than per-entry: `assemble.py`'s
`_derive_supersedes()`, which inverts every entry's `superseded_by` across the
whole corpus. Two curated inputs are also deliberately cross-model (the shape
catalog and `formal-assignments.json`). Running per model would fragment them
and change what `_derive_supersedes` sees. Splitting afterwards is a pure
filter, so each per-model file is byte-for-byte the corresponding slice of the
corpus.

**Families, not concrete functions.** OpenSHMEM and NVSHMEM define most
routines once per data type (`nvshmem_int_put`, `nvshmem_long_put`, ...). Every
stage up to Assemble works on one generic family entry (`nvshmem_{T}_put`, with
`identity.type_family` listing the types), so each judgement is made and
reviewed once. Concretize expands the families into concrete entries only
at the end, from the same type tables Extract parsed.

**Provenance is a separate file, not a field on each entry.** A shipped entry
holds values and nothing else, so the consumer contract stays the eight
sections and their closed vocabularies. How each value was derived still has to
be recorded, so it ships beside the corpus under the same keys. The unit is the
family: Concretize copies a family's values unchanged into every typed entry.

**What is deliberately not written to disk.** The staging schemas, the
supplement projection and the assignment review worksheet are each derivable
from inputs their consumer already holds, so a checked-in copy could only go
stale. The staging schemas are derived per stage in memory
(`derive_schema.staging_schema_for`). Supplement eligibility depends on which
fields are still null in the corpus being merged, so `assemble.py` calls
`propose.build_proposals()` directly and logs ineligible entries in
`promotion_log`. The review groups live in the review record they feed.

**Rarely changed vs. regenerated.** The schema, the shape catalog and the
expander change only when the vocabulary grows, and every such change is
reviewed by a domain expert. Per-function entries are regenerated on every new
source release, and are reviewed by exception: Validate flags, a human reads
the flags. That asymmetry is why Validate carries as many automated checks as
it does. Re-running only the entries a new source release changed is not
designed yet.

---

## 4. Directory-by-directory

Every script below runs standalone with `python3 <path>`; only
`staging/derive_schema.py` and `validate/consistency.py` take arguments.

### Chain stages

- **`extract/`** — Extract. `cli.py` drives per-PPM adapters (`mpi/`, `shmem/`,
  `nccl/`, `nvshmem/`, `openmp/`, `cuda/`) that read `external-inputs/` (MPI `apis.json` +
  LaTeX, OpenSHMEM LaTeX, NCCL/NVSHMEM headers + the mirrored HTML docs, LLVM's
  `omp.h`, CUDA's `cuda_runtime_api.h` — the last two through the shared
  preprocessor-conditional and declaration reader `c_header.py`), assembles them through
  the shared null-padding layer in `emit.py`, validates each entry against the
  derived `post-extract` staging schema (`validate_entry.py`), and writes
  `0_syntactic-api.json` plus a report side-channel of skipped/low-confidence/
  note flags. Golden tests: `test_emit.py` against `golden_entries.json`.
- **`classify/`** — Heuristic Classification. Same shape as `extract/`
  (per-PPM modules + `emit.py` overlay + `cli.py` driver) for the nine
  `semantic_heuristic`-tier fields (`identity.api_group`, `execution.*`,
  `semantics.atomic.*`, `parameters[].kind`/`.constraints.not_null`,
  `relationships.variants.*`). Every value it produces is naming- or
  structure-derived, so it ships `pattern`-confidence with a `low_confidence`
  flag, never `static`. Golden tests: `test_emit.py`.
- **`formal/`** — Generate Formal. `assign.py` (the chain stage) matches each
  function family to a shape in `curated/shapes/shapes.json` and emits proposals plus
  the grouped review record in `curated/review/`, merging it with any decisions
  already recorded there. The rest is library code it and others use:
  `expand.py` (the deterministic shape-template → inlined `semantics.formal`
  expansion — pure function, zero model calls, byte-identical output for
  identical input), `validate.py` (structural check of an expanded block
  against `api-schema.json`'s `$defs`), `grammar.py` (enforces the normative
  EBNF in `docs/schema/reference-grammar.md`). Tests: `test_shapes.py`
  (re-derives every golden expansion and diffs it), `test_grammar.py`.
- **`supplement/`** — `propose.py`'s `build_proposals()` reads the hand-authored
  `curated/supplement/supplement-*.json` files and yields values only for fields
  that are still null (supplement never overrides an earlier stage). Called by
  `assemble.py`; run it directly (`--summary`, `--out FILE`) only to inspect
  what it would contribute.
- **`assemble/assemble.py`** — the corpus merge stage: applies both proposal files to `1_` (→ `2_`, `3_`),
  completes `parameters[].length`/`array_type` for every array Extract could not
  size (`assemble/array_shape.py`, whose docstring states the rules), runs
  Concretize and the final null-fill (→ `4_`), and validates every concrete
  entry against the strict schema. Entries that fail are still emitted;
  `validation_errors` and `unfillable_required_fields` in `4_final-api.json`
  record what's wrong rather than silently dropping them.

### Supporting

- **`fetch/fetch.py`** — installs the third-party inputs that are not
  vendored, for licensing reasons, into `external-inputs/`. `manifest.json`
  beside it lists every URL it downloads and every file it writes, each with
  the sha256 of the file the shipped corpus was built from; a source is
  installed only if every one of its files matches. The docs are fetched as
  raw HTML and converted locally by `ingestion/html_to_markdown.py`, and the
  Markdown is checked too. `--dry-run` shows the plan, `--check` verifies
  what is on disk, and `--from-dir DIR` copies from an existing
  `external-inputs/`-shaped tree instead of downloading. A source can be marked
  `unavailable` in the manifest, with a reason, if its downloads disappear.
  `build.py`'s preflight calls its `missing_inputs()`.
- **`concretize/`** — `expand_types.py` (one generic `{T}` family → N concrete
  entries) and `materialize_nulls.py` (every still-absent field → explicit
  `null`, satisfying R1 without any earlier stage inventing defaults).
  Called by `assemble.py` and `subset.py`; not run directly.
- **`staging/derive_schema.py`** — mechanically derives the staging schema for
  a workflow stage from `curated/schemas/api-schema.json` +
  `field-provenance.json`, so a stage's output is validated against exactly the
  fields that stage owns — after Extract runs, `semantics.formal` legitimately
  isn't there yet, and validating against the full schema would fail every
  entry. The derived schemas are build output and land in the output directory.
  `--stage {post-extract,post-heuristic-classification,post-generate-formal}`.
  Nothing reads a checked-in copy — `staging_schema_for(stage)` derives one in
  memory at each stage's startup — so the CLI exists purely to print one for a
  human (stdout by default, `--out FILE` to keep it). `test_staging_schema.py`
  checks that every known stage still derives into a non-degenerate schema.
- **`validate/consistency.py`** — the Validate stage, and the hand-run checker
  it grew out of. Its own checks run over the merged generic corpus
  (`3_…`) and are the ones per-entry schema validation structurally cannot
  make (reference resolution and model qualification, variants/supersedes
  symmetry, the `parameters[].length` convention, `semantics.formal` grammar
  and `matched.via` resolution). Under
  `--report` — how the stage runs it — it additionally re-validates every
  concrete entry of `4_final-api.json` against the strict schema and writes
  `validate-report.json`, exiting 0 so a corpus with known gaps doesn't fail
  every build. Re-validating rather than copying `assemble`'s own inline result
  is the point: the report records any disagreement between the two as
  `disagreements_with_assemble`. Without `--report` it exits 1 on findings,
  which is what `build.py --check` uses.
- **`provenance/report.py`** — the Provenance stage. Joins `extract-report.json`,
  `classify-report.json`, `4_final-api.json`'s `promotion_log`,
  `curated/field-provenance.json` and the review records into one record per
  value: `{entry, path, tier, state, stage, method, confidence, approved}`.
  `stage` is `extract`, `classify`, `assign`, `supplement`, or `assemble` for
  the array lengths `assemble/array_shape.py` derives during the merge.
  `method` is WR1's three-way distinction (`mechanical`, `standard_passage`,
  `model_assisted`); `approved` is non-null only for model-assisted values,
  which are the only ones with a review gate. Keyed by authored family, not by
  concrete entry — Concretize copies a family's values unchanged, so 25 typed
  broadcast entries share one derivation. `--summary` prints the tally.
  Tests: `test_report.py`.
- **`split/by_model.py`** — the Split stage, and the sole producer of the
  shipped `final-<ppm>-api.json` files. A pure filter: it partitions `4_final-api.json` and
  `provenance-report.json` by `identity.model`, slices the logs the same way,
  recomputes each summary, and stamps each document with the `schema_version`
  read from the schema's `$id`. `--split-intermediates` partitions `0_`–`3_`
  too. Tests: `test_by_model.py`, which checks conservation — every corpus
  entry in exactly one file, byte-identical, with the counts adding up.
- **`review/`** — `record.py` is the one implementation of merging review
  decisions forward (a decision survives while its group exists; a vanished
  group moves to `orphaned_decisions`), shared by all three record producers.
  `scaffold.py` builds the shapes and supplement records, which no stage
  produces because both artifacts are hand-authored. See
  `docs/workflow/review-records.md`.
- **`validate/test_curated.py`** — validates every hand-edited curated file
  against its schema in `curated/schemas/`, plus the cross-references a schema
  cannot express (a tier that isn't in the `tiers` map, duplicate shape ids, a
  golden example naming a shape that doesn't exist, duplicate review group ids).
  The corpus has always been schema-checked; the files that *govern* it were
  not, and this closes that asymmetry.
- **`common/`** — shared machinery: `layout.py` (the three directory roots and
  their env-var overrides — every script resolves paths through it, so a
  redirected build stays consistent), `status.py` (`Flag`/`Report`), `ir.py`
  (`Confident` and the three confidence levels), `paths.py` (the dotted-path
  get/set used by both `propose.py` and `assemble.py`, shared so their notion
  of "this field's location" can't drift).
- **`ingestion/`** — one-off-ish converters, run when refreshing a vendored
  source, never as part of a build. `html_to_markdown.py` turns mirrored doc
  pages into the Markdown under `external-inputs/{nccl,nvshmem,cuda}/docs/`
  (Sphinx `articleBody` pages and the DITA topics the archived CUDA docs use).
  `openmp_spec_text.py` slices the `pdftotext` rendition of a vendored OpenMP
  specification into one Markdown file per routine, resolving each routine's
  chapter from the document's own headings rather than assuming one. It is run
  for both vendored versions: `docs/6.0/md/` supplies `identity.standard_refs`
  and the two parameter names the ARB header omits, and `docs/5.2/md/` supplies
  `identity.desc`, because 6.0 removed the per-routine `Summary` block 5.2
  published.
- **`viz/sync_schema_index.py`** — regenerates the schema-explorer data block
  embedded in `docs/viz/formal-semantics.html` from the schema.
  Run after a schema version bump.

### All test suites

```bash
python3 workflow/extract/test_emit.py
python3 workflow/classify/test_emit.py
python3 workflow/formal/test_shapes.py
python3 workflow/formal/test_grammar.py
python3 workflow/staging/test_staging_schema.py
python3 workflow/validate/test_curated.py
python3 workflow/split/test_by_model.py
python3 workflow/provenance/test_report.py
```

or `python3 workflow/build.py --test …` to run all eight before a build. The
last two check artifacts rather than golden files, so they skip cleanly when
`instances/` is empty. The first two follow the model selection: under
`build.py --test --ppm mpi,nccl` (or `PPM_MODELS=mpi,nccl`) they check only
those models' golden cases and say how many they skipped, so a build that
leaves CUDA out does not need its fetched headers. Run bare, they cover every
model and so need every fetched input.

---

## 5. Common recipes

```bash
# Fresh clone: fetch the non-vendored inputs first (see what it would do with --dry-run).
python3 workflow/fetch/fetch.py

# Full rebuild from sources, reusing curated proposals, then check it.
python3 workflow/build.py --test --check

# I edited curated/schemas/api-schema.json or field-provenance.json.
python3 workflow/build.py --test          # staging schemas re-derive themselves

# I hand-corrected curated/formal-assignments.json.
python3 workflow/build.py --from assemble

# I edited a curated/supplement/ input.
python3 workflow/build.py --from assemble

# Trial build somewhere else; instances/ stays as it is.
python3 workflow/build.py --out /tmp/build-x

# One model only -- everything downstream just sees a smaller corpus.
python3 workflow/build.py --ppm mpi

# Re-split and re-describe an existing corpus without rebuilding it.
python3 workflow/build.py --from validate

# I changed an extraction adapter and want to see its output only.
python3 workflow/build.py --only extract

# I changed shapes.json and want new assignment proposals (overwrites edits).
python3 workflow/build.py --regenerate formal

# Ship-shaped output: the per-model files, the merged corpus and the reports.
python3 workflow/build.py --prune-intermediates
```
