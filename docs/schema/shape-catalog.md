# The Shape Catalog

An authoring-time mechanism, not a runtime concept of the schema: why it exists,
how it is structured, and the boundary that keeps it out of the shipped schema.

## Why it exists

Hand-authoring a full `participants`/`data_flow`/`sync`/`handle_lifecycle`
block for every entry would produce a large amount of *near-duplicated* JSON:
across MPI alone (about 450 symbols once large-count and persistent variants
are counted), plus NCCL, NVSHMEM and OpenSHMEM, a broadcast, a scatter and a
one-to-all neighborhood collective all produce structurally identical blocks
with different parameter names.

Most communication operations fall into a small number of canonical shapes. A
**shape** is a `formal` block with named placeholders (**slots**) instead of
concrete `param:` references. An entry does not author `formal` directly: it
names a `shape_ref` and gives a `bindings` map (slot name to concrete
reference), and the **expander** substitutes the bindings into the shape's
`template`, producing the fully inlined `formal` block.

## The boundary: shapes are erased before shipping

**No consumer of the shipped schema ever sees `shape_ref`.** It exists only to
reduce what a human or a model authors and reviews. The consumer walk in
`docs/consumers/tool-consumption-model.md` never learns that shapes exist; it
operates only on fully inlined `formal` blocks with concrete `param:`
references. A consumer that needed to understand `shape_ref` would mean the
abstraction had leaked into the wrong layer.

## Slot kinds

| Kind | Binds to |
|---|---|
| `buffer_slot` | a `param:` ref of `kind: BUFFER` |
| `extent_slot` | a `{count_ref, datatype_ref}` pair of `param:` refs |
| `selector_slot` | a predicate in the reference grammar, e.g. `rank == param:root` |
| `operation_slot` | a `param:` ref of `kind: OPERATION` |
| `handle_slot` | a `param:` ref of `kind: REQUEST` or `WINDOW` |
| `index_slot` | an expression describing a per-participant sub-extent (scatter) |
| `literal_slot` | a constant chosen at binding time, e.g. `role: "create"`, `epoch_scope: "access"`, or a whole `sync.matching` object |

## Authoring: `shape_ref` + `bindings` + `extra`

```json
{
  "shape_ref": "collective.one_to_all_uniform",
  "bindings": {
    "buffer": "param:buffer",
    "extent": { "count_ref": "param:count", "datatype_ref": "param:datatype" },
    "root_selector": "rank == param:root",
    "scope_selector": "rank in param:comm"
  }
}
```

The point-to-point shapes (`p2p.direct_send`/`direct_recv`,
`handle_bound.post_send`/`post_recv`) take their matching rule as a `matching`
slot, because every user needs one and the rule differs by model: MPI's
`tag_match`, NCCL's `peer_match`.

```json
{
  "shape_ref": "handle_bound.post_send",
  "bindings": {
    "buffer": "param:buf",
    "extent": {"count_ref":"param:count","datatype_ref":"param:datatype"},
    "handle": "param:request",
    "matching": { "kind": "tag_match", "match_keys": ["param:comm","param:tag","param:dest","self_rank_as_source"], "matched_across": "paired_call", "program_order_required": false }
  }
}
```

**`extra`** is a block of dotted-path patches, deep-merged onto the expansion
after substitution. It is reserved for a genuinely one-off quirk on an
otherwise good match; no golden example currently needs it. If several entries
need the same `extra` patch, that patch becomes a slot or a new shape instead,
so that `extra` does not become a second place for duplication to hide. Equally,
when no shape fits a function, a new shape is added rather than forcing a near
miss (see "Honest gaps over forced fits" in `docs/schema/design-conventions.md`).

## Files and checks

```
curated/shapes/shapes.json  ──┐
                              ├──▶  expander  ──▶  entries valid against api-schema.json
shape_ref + bindings        ──┘                   (formal fully inlined; shape_ref never appears)
```

- `curated/shapes/shapes.json` — the catalog. Each shape carries the reason it exists as a `$comment`, so the reasoning travels with the shape.
- `curated/shapes/seed-assignments.json` — golden examples: a real function's `shape_ref` + `bindings` and its correct expansion.
- `curated/formal-assignments.json` — the shape and bindings proposed for every function family; curated, so hand corrections are kept.
- `curated/schemas/shapes.schema.json` — validates the catalog's envelope (id, slots, template presence). The template internals are `$defs/shape_template` in `api-schema.json`, enforced by `workflow/formal/validate.py`.
- `api-schema.json` — the shipped schema, in which `formal` is always fully expanded or `null`.

The golden examples are the ground truth for the expander:
`workflow/formal/test_shapes.py` re-expands each one and compares it
byte-for-byte with its stored expansion, and fails if any shape has none. (The
generated corpus cannot serve as ground truth, since the same expander produces
it.) `workflow/formal/assign.py` also uses them: an exact `(ppm, function)`
match against a golden example is its first assignment rule. Review state per
shape is in `curated/review/shapes.review.json`.

## The catalog

27 shapes. The counts are function families (a type-generic family such
as `shmem_{T}_put` counts once) in `curated/formal-assignments.json` that are
assigned each shape; OpenMP and CUDA use none. Of the corpus's
1475 families, 245 have a shape,
828 need none (queries and management calls), and
402 are still waiting for a shape that fits.

| Shape | MPI | OpenSHMEM | NCCL | NVSHMEM | Golden examples |
|---|---|---|---|---|---|
| `collective.one_to_all_uniform` | 3 | 14 | 4 | 2 | 4 |
| `collective.all_to_all_reduce` | 9 | 7 | 1 | 14 | 4 |
| `resource.lifecycle` | 2 | — | — | — | 2 |
| `rma.put` | 1 | 28 | — | 4 | 3 |
| `handle_bound.post_send` | 11 | — | — | — | 1 |
| `handle_bound.post_recv` | 4 | — | — | — | 1 |
| `handle_bound.wait_on_handle` | 1 | — | — | — | 1 |
| `sync_only.rendezvous` | 3 | 3 | — | 4 | 3 |
| `sync_only.local_fence` | — | 6 | — | 2 | 2 |
| `collective.one_to_all_indexed` | 1 | — | — | — | 1 |
| `collective.all_to_one_indexed` | 1 | — | — | — | 1 |
| `collective.all_to_one_reduce` | 3 | — | 1 | — | 2 |
| `collective.scan_prefix` | 1 | — | — | — | 1 |
| `rma.get` | 2 | 28 | — | 4 | 3 |
| `rma.atomic` | — | 1 | — | — | 2 |
| `rma.accumulate` | 1 | — | — | — | 1 |
| `epoch.fence` | 1 | — | — | — | 1 |
| `epoch.lock_unlock` | 2 | — | — | — | 2 |
| `epoch.pscw` | 4 | — | — | — | 4 |
| `epoch.file_split_collective` | 2 | — | — | — | 2 |
| `p2p.direct_send` | 5 | — | 1 | — | 2 |
| `p2p.direct_recv` | 2 | — | 1 | — | 2 |
| `collective.gather_to_all` | 12 | — | 1 | — | 2 |
| `collective.reduce_scatter` | 6 | — | 1 | — | 2 |
| `resource.collective_lifecycle` | — | 2 | 2 | 2 | 6 |
| `rma.put_signal` | — | 28 | — | 4 | 1 |
| `rma.put_scalar` | — | 2 | — | 1 | 2 |

**Reading the table:** `collective.one_to_all_uniform`, `collective.all_to_all_reduce`,
`sync_only.rendezvous` and the RMA shapes are used by three or four models,
which is the cross-model reuse the catalog exists for. The epoch shapes,
`rma.accumulate` and `epoch.file_split_collective` are MPI-only because the
other models have no such constructs.

**Not built:** `collective.all_to_all_uniform` (alltoall). Its pairwise,
doubly-indexed data movement has no vocabulary in `semantics.formal` yet, and
forcing it into `structural`/`reduced`/`gathered`/`matched` would produce a
shape that looks complete but is wrong. See
`docs/cross-ppm-analysis/known-gaps-and-open-questions.md`.

## The expansion algorithm

`workflow/formal/expand.py`:

```
function expand(templateNode, bindings):
    if templateNode is an array:
        return [expand(item, bindings) for item in templateNode]
    if templateNode is an object:
        return { key: expand(value, bindings) for key, value in templateNode }
    if templateNode is a string:
        if templateNode exactly matches "{{slot_name}}":
            return bindings[slot_name]   # whole-value substitution, preserves type (object, array, etc.)
        else:
            return templateNode with every "{{slot_name}}" substring replaced by
                   str(bindings[slot_name]) if bindings[slot_name] is a string
                   else JSON-stringify(bindings[slot_name])
    return templateNode  # numbers, booleans, null pass through unchanged
```

The two string modes matter: a slot like `extent` substitutes a whole object
(`{"count_ref": "...", "datatype_ref": "..."}`), while a slot like
`root_selector` is usually embedded in a larger selector string (e.g.
`"!( {{root_selector}} ) && {{scope_selector}}"` for the non-root participant of
a broadcast).

The function is pure and deterministic, with no model calls and no side
effects, so the same input always gives byte-identical output. The golden-example
test depends on that.

## Design decisions

- **Send and receive, put and get, are separate shapes.** They have different `op` directions (`read` vs. `write`) that cannot share one template without conditional logic inside the template, which the pure-substitution expander deliberately does not have.
- **`p2p.direct_send`/`direct_recv` exist beside `handle_bound.post_send`/`post_recv`.** Blocking MPI send/receive and NCCL's stream-ordered send/receive complete on the call's own return, with no request handle, so the handle-bound shapes were a near miss, not a match.
- **`resource.collective_lifecycle` exists beside `resource.lifecycle`.** Lifecycle calls that are themselves collective (`ncclCommInitRank`, `shmem_malloc`) contradict the single-participant template.
- **`rma.put_signal` exists beside `rma.put`.** The put-with-signal family's signal write would otherwise be silently dropped.
- **`collective.reduce_scatter` combines two mechanisms**: a `reduce` node and per-recipient slicing of its result (`offset` on the `reduced` source).
