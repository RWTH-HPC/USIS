# `curated/` — what a human decided

Everything here is hand-authored or hand-corrected. Nothing here is rebuilt by
a default `python3 workflow/build.py`; changing any of it is a deliberate act.
That is the whole distinction between this directory and `instances/`, which
holds only what a build produces and is safe to delete and regenerate.

The three roots:

| Directory | Contents | Rebuilt by a build? |
|-----------|----------|---------------------|
| `external-inputs/` | Third-party source material: standards (LaTeX), headers, mirrored HTML docs. Read-only to this workflow. | Never — vendored |
| `curated/` | This directory | No, unless asked |
| `instances/` | Every build artifact, including the derived staging schemas | Yes, every build |

`workflow/build.py --out / --curated-dir / --external-inputs` can point any of
the three somewhere else; see `workflow/README.md`.

## Contents

### `schemas/` — JSON Schemas only

Every file here is a schema, and every hand-edited JSON format in this project
has one (`workflow/validate/test_curated.py` checks each file against its
schema on every `--test` run):

| Schema | Validates |
|---|---|
| `api-schema.json` | every shipped entry — the project's actual deliverable |
| `shapes.schema.json` | `../shapes/shapes.json`'s envelope (the template internals are `$defs/shape_template` inside `api-schema.json`, enforced by `workflow/formal/validate.py`) |
| `supplement-input.schema.json` | `../supplement/supplement-<ppm>.json` |
| `field-provenance.schema.json` | `../field-provenance.json` |
| `review-record.schema.json` | `../review/*.review.json` |

**Not here:** `api-schema.staging.*.json`. Those are derived per stage from
`api-schema.json` + `field-provenance.json` at run time by
`workflow/staging/derive_schema.py` — they are not files at all any more.

### `shapes/`

`shapes.json` — the authoring-time shape catalog (27 shapes) — and
`seed-assignments.json` — for each of 58 real functions, which shape fits and how its
slots are filled, plus a per-shape provenance note on why the shape exists and
which functions motivated it.

`seed-assignments.json` is curated because a build stage reads it:
`workflow/formal/assign.py`'s first matching rule reuses an authored binding on
an exact `(ppm, function)` match, which is where 55 of the corpus's 1440 shape
proposals come from.

**Why this is a separate file from `../formal-assignments.json`** — a recurring
point of confusion, and *not* "one is hand-written, the other generated". Both
are AI-authored. The distinction is **input vs. output**: `assign.py` reads this
file and writes `formal-assignments.json`, wholesale, on every
`--regenerate formal`. What this file holds is specifically the assignments
`assign.py`'s own rules **cannot derive** — re-running it against an emptied
seed (measured 2026-07-22) changes 30 of the 58, dropping the entire RMA/window
family and both scatter/gather to `escalate_new_shape`. Merging the two would
make the stage read its own output, and would leave those 30 protected only by
convention rather than by construction.

The *expansion* each binding must produce is a third kind of thing — a pinned
test fixture, deliberately never regenerated — and lives with its test, in
`workflow/formal/testdata/expansions.json` (split 2026-07-22).
`workflow/formal/test_shapes.py` joins the two by `ppm:function` and fails if
either side lacks a counterpart.

Three assignments match no corpus entry (both `*_int_sum_reduce`,
`nvshmem_int_atomic_add`) and are kept on purpose: they record an Extract
coverage gap — NVSHMEM's typed API and SHMEM's reductions are absent from the
corpus entirely. `nvshmem_malloc` was the fourth until 2026-09-11, when the
NVSHMEM adapter learned the two declaration forms it had been missing and the
corpus gained it. See this file's `$comment_unmatched`.

Shapes are an authoring-time convenience, never a runtime concept:
`shape_ref`/`bindings`/`extra` never appear in a shipped entry.

**Not here:** `mpi-api.json`, the worked example entry, moved to
`docs/schema/examples/` on 2026-07-22. No build stage reads it — it is cited by
`docs/schema/reference-grammar.md` and rendered by the viz explorer, so it is
documentation, and `workflow/formal/test_grammar.py` validates it where it is
documented.

### `field-provenance.json`

Which automation tier and workflow stage owns each of the ~148 field paths.
Lives at the curated root rather than in `schemas/` because it is config that
*governs* the schemas rather than being one: `workflow/staging/derive_schema.py`
derives every stage's staging schema from this file plus `api-schema.json`, so
a wrong tier here silently changes what a stage is allowed to emit.

### `supplement/`

`supplement-<ppm>.json` — hand-authored, web-researched or general-knowledge
values for `(entry, field)` pairs the PPM's own primary source structurally
cannot supply (MPI's `identity.desc` for functions whose standard prose is a
bare cross-reference; `identity.since`, which no MPI chapter records
machine-readably). Format: `curated/schemas/supplement-input.schema.json`.

The precedence rule is enforced in code, not just documented: a supplement
value is only ever proposed for a field whose owning stage has actually run and
produced a real, considered `null`. Supplement never overrides a value a stage
produced, not even a low-confidence one.

**This is the file to correct** when a supplement-sourced value is wrong.
There is no intermediate proposals file to edit: the assemble stage projects
these inputs onto the corpus in memory, deciding eligibility against the very
entries it is merging (removed 2026-07-22 — a materialized projection could
only ever be a stale duplicate of its two inputs). Run
`python3 workflow/supplement/propose.py --summary` to see what they currently
contribute, and what got skipped because the target field is no longer null.

### `formal-assignments.json`

Shape-assignment proposals: for each function family, which
`semantics.formal` shape (if any) fits, with what bindings. Every proposal is
`confidence="needs_approval"` — proposed, never asserted.

Unlike the supplement proposals, **corrections belong in this file itself**.
There is no hand-authored upstream file for them to live in: the alternatives
are changing `curated/shapes/shapes.json` (right when the *shape* is wrong) or
`workflow/formal/assign.py`'s matcher (right when the *rule* is wrong), but
neither is right when this one function simply needs a different answer. That
is why this file is curated and `workflow/build.py` will not regenerate it
without `--regenerate formal`.

### `review/`

Review state — which proposals a human has actually read, and what they
decided. Three records, each grouped by whatever makes two things *the same
decision* for that artifact:

| Record | Unit | Count | Refreshed by |
|---|---|---|---|
| `formal-assignments.review.json` | decision pattern | 132 groups / 1475 proposals | `build.py --regenerate formal` |
| `shapes.review.json` | the shape | 27 | `python3 workflow/review/scaffold.py --shapes` |
| `supplement.review.json` | judgment call (`field_path` + `method`) | 181 groups / 2135 values | `python3 workflow/review/scaffold.py --supplement` |

The last two exist because **authorship is not review**: the shape process
specifies human review of every shape but nothing recorded whether it happened,
and supplement values promote unreviewed by default with ~97% carrying no
citation at all.

The `status`/`reason`/`exceptions` fields on each group are yours to edit, and
regeneration merges rather than overwrites: a decision survives as long as its
group still exists, and one whose group has disappeared moves to
`orphaned_decisions` instead of being dropped. Format:
`docs/workflow/review-records.md`.

### `backups/`

Timestamped copies made by `workflow/build.py --regenerate` immediately before
it overwrites a curated file. Git-ignored; a local safety net, not history.
Delete freely.

## Editing rules

1. **Correct a value at its source.** A wrong supplement value → `supplement/`.
   A wrong shape *template* → `curated/shapes/shapes.json`. A wrong *assignment*
   for one function → `curated/shapes/seed-assignments.json`, which survives
   `--regenerate formal`; `formal-assignments.json` is rebuilt wholesale by it,
   so a fix made only there lasts until the next regenerate and no longer.
   Never patch a file in `instances/`; the next build overwrites it.
2. **After editing, re-merge:** `python3 workflow/build.py --from assemble`.
   That covers both curated proposal sources — the supplement inputs are
   projected onto the corpus during the merge itself.
3. **After editing `curated/schemas/api-schema.json` or `field-provenance.json`,
   just rebuild:** `python3 workflow/build.py --test`. The staging schemas each
   stage validates against are derived from those two files at run time, so
   there is nothing to regenerate by hand.
4. **A new schema vocabulary item needs a `$id` version bump and a documented
   rationale** — `docs/schema/schema-versioning.md`.
