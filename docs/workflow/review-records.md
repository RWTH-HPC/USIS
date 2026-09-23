# Review Records

The format of `curated/review/<artifact>.review.json` — one file per reviewable
artifact, recording **which proposals a human has actually read, and what they
decided**. Review state is a curated fact (it says what a person did), so it
lives in `curated/` and no build overwrites it.

    formal-assignments.review.json   reviews curated/formal-assignments.json
    shapes.review.json               reviews curated/shapes/shapes.json
    supplement.review.json           reviews curated/supplement/supplement-<ppm>.json

Naming rule: `<artifact-stem>.review.json`, so "is this reviewed?" is
answerable from a filename. All three are machine-checked against
`curated/schemas/review-record.schema.json` by
`workflow/validate/test_curated.py`.

## Three records, three review units

The unit is whatever makes two things *the same decision* to a reviewer. That
differs per artifact, and getting it wrong is what makes review not happen:

| Record | Unit | Count | Written by |
|---|---|---|---|
| `formal-assignments` | decision pattern (`outcome` + `shape_ref` + `rationale` + binder notes) | 130 groups over 980 proposals | `workflow/formal/assign.py` |
| `shapes` | the shape itself | 27 | `workflow/review/scaffold.py` |
| `supplement` | judgment call (`field_path` + `method`) | 180 groups over 2146 values | `workflow/review/scaffold.py` |

The shapes and supplement records exist because **authorship is not review**.
The Author Shapes process specifies "human review, every time, no sampling",
but nothing recorded whether that happened for a given shape. Supplement values
are `needs_approval` by construction yet promote into entries unreviewed by
default — 2146 of them, ~97% carrying `method: general_knowledge`, meaning
there is no citation to check them against, only a human who knows the PPM.
That is the corpus's largest body of unverified content.

The supplement grouping deliberately drops the PPM from the key: including it
gives 347 groups and splits one judgment ("`identity.since` from general
knowledge") across four files for no reviewer benefit. The largest group holds
524 values — one decision made 524 times, not 524 decisions.

`workflow/review/record.py` holds the one implementation of merging decisions
forward, shared by all three producers, so a decision can never be treated
differently depending on which artifact it belongs to.

## Refreshing the records

```bash
python3 workflow/review/scaffold.py              # shapes + supplement
python3 workflow/review/scaffold.py --shapes     # one of them
python3 workflow/build.py --regenerate formal    # the assignment record
```

## The file format

Identical across the three records; only the grouping and a few
artifact-specific fields differ. The assignment record, shortened:

```json
{
  "reviews": "curated/formal-assignments.json",
  "generated_at": "2026-07-22T…",
  "status_vocabulary": ["unreviewed", "approved", "withheld"],
  "summary": { "groups": 130, "groups_reviewed": 0, "proposals_covered": 980, … },
  "groups": [
    {
      "group_id": "no_formal_applicable:1a2b3c4d",
      "outcome": "no_formal_applicable",
      "shape_ref": null,
      "rationale": "identity.api_group='query' -- matches the established convention that query/management calls carry no semantics.formal",
      "binder_notes": [],
      "member_count": 224,
      "members": ["mpi:mpi_abi_get_fortran_booleans", "…"],
      "exemplar": { "…one fully-worked proposal…" },

      "status": "unreviewed",
      "reason": null,
      "reviewed_at": null,
      "exceptions": {}
    }
  ],
  "orphaned_decisions": []
}
```

**Yours to edit:** `status`, `reason`, `reviewed_at`, `exceptions` on each
group. Everything else is regenerated. The shapes record adds `slots` and
`justification` (the shape's own `$comment`) to each group; the supplement
record adds `field_path`, `method` and a per-PPM `ppms` count.

**`status`** is a closed three-value vocabulary:

| Value | Meaning |
|-------|---------|
| `approved` | Read, and correct. |
| `withheld` | Read, and rejected — do not ship these values. |
| `unreviewed` | Nobody has looked yet. The default for a new group. |

**`exceptions`** handles members that deviate from their group's decision:
`{"mpi:mpi_send": {"status": "withheld", "reason": "…"}}`, keyed by entry key
(add `::<field_path>` when a decision is about one field rather than the whole
proposal).

## Regeneration merges, never clobbers

Re-running `assign.py` (via `build.py --regenerate formal`) rebuilds the
`groups` list but preserves your decisions:

- A group whose `group_id` still exists keeps its `status`/`reason`/
  `reviewed_at`/`exceptions` verbatim.
- A group that no longer exists — because the matcher changed, or its rationale
  was reworded — moves to `orphaned_decisions` with an `orphaned_at` stamp,
  rather than being deleted. A reviewed decision is never silently dropped.
- `group_id` is a hash of the pattern itself, so a reworded rationale
  deliberately produces a *new*, unreviewed group. A decision never carries
  over to something a human has not actually read.

## What reads these records

The build chain is **ungated**: `workflow/assemble/assemble.py` applies every
proposal at face value, and review is applied to the chain's best-effort result
rather than interleaved with generating it. So a record here documents a human
judgment — real, durable and readable — but changes no *corpus* value.
Introducing gating (`withheld` actually withholding a value; `promotion_log`
distinguishing reviewed from unreviewed promotions) would be a deliberate
decision, not a side effect of editing a file here.

The one reader is the `provenance` stage
(`workflow/provenance/report.py`) reads each record's group `status` and sets
`approved` on every provenance record for that group's members: `true` for
`approved`, `false` otherwise, and `null` for values that have no review gate at
all (everything `mechanical` or `standard_passage`). That is a report about the
review state, not a gate on it — nothing is withheld — but it means a `status`
edit here is visible in a shipped artifact, and the current state is legible:
while every group is `unreviewed`, no reviewable value counts as approved. The join keys are the ones each record already carries:
the supplement record's `field_path` is in the same by-name form the promotion log
uses (`parameters[buf].memory_space`), and the assignment record's groups are
implicitly about `semantics.formal`.
