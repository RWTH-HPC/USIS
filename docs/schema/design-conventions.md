# Design Conventions

The principles the schema is built on, with the reason for each. For what an
individual field means, see `docs/schema/field-semantics.md`.

## The requirements (R1–R8)

- **R1 — Unified schema.** Every PPM shares an identical top-level field structure. Inapplicable fields are explicit `null`, never omitted.
- **R2 — Semantic completeness.** Captures everything a tool would otherwise extract from the standard: execution properties, memory completion semantics, collective classification, one-sided epoch requirements, correctness invariants and deadlock conditions.
- **R3 — Language-binding coverage.** C, Fortran 90, Fortran 2008, LIS and C++ are described in a consistent sub-structure; unsupported bindings are `null`, never silently absent.
- **R4 — Extensibility.** New PPMs and new fields can be added without breaking existing entries or existing tool consumers.
- **R5 — Tool agnosticism.** No section encodes knowledge specific to one tool; invariants and diagnostics use a vocabulary any tool can consume.
- **R6 — GPU/heterogeneous-context awareness.** Represents CPU/GPU callability, GPU parallelism granularity, and CUDA-stream awareness, as needed for NVSHMEM device functions and GPU-callable extensions.
- **R7 — API lifecycle tracking.** `since`/`deprecated_in` are version strings (not booleans), with a `relationships.superseded_by` key and its derived inverse `relationships.supersedes`, enabling version-qualified diagnostics. `identity` answers *whether and when* a call was deprecated; `relationships` answers *what replaced it*, because the replacement is a reference to another entry.
- **R8 — Machine readability.** Plain JSON, parseable with any standard library.

Three of them shape many concrete decisions:

**R1 — all sections always present, nulls explicit.** `semantics.formal` is nullable but always present, never an optional key, and `data_flow` is an empty array (not omitted) for pure synchronization operations such as barriers. R1 governs the *final* entry. Intermediate checkpoints follow a separate rule: a field whose owning workflow stage has not run yet is *omitted*; once that stage has run and found nothing, the field is present as `null`. So a `null` at any stage is always a considered answer, never a placeholder.

**R4 — extensibility.** New operational machinery is nested under `semantics.formal` instead of becoming a new top-level section. Promoting it later stays cheap; restructuring the top level would break consumers.

**R5 — tool agnosticism.** Some concerns stay *out* of the schema. Buffer-overlap and alias analysis, for example, belong to the consuming tool: the schema states facts (an access window is open, of a certain kind, on a certain region); it does not replace a compiler's own memory model.

## Enumerable vocabulary over embedded logic

The most important principle. Every field in `semantics.formal` is a closed enum, a structured object, or a reference — never a string a consumer has to parse as an expression.

- Hoare-style logical contracts were considered for the data-flow layer and rejected: they would need a whole expression language with quantifiers and array semantics, a far larger surface than the chosen design, and exactly the logic-in-strings pattern earlier schema versions had removed.
- Where a real case would need more expressive power (OpenSHMEM's value-dependent `wait_until`), it stays unmodeled rather than opening the door to a predicate language.

**Consequence:** a consumer implements against a small, fixed vocabulary — 4 `data_flow[].op` values, 5 `source.kind` values, 3 `handle_lifecycle[].role` values, 5 `sync.matching.kind` values — however large the corpus grows. A change that would grow this consumer-facing vocabulary substantially is a reason to reconsider the design, not just a cost to accept. (`source.kind` grew once, by `gathered`, because two of NCCL's five collectives were unrepresentable without it.)

Two string-valued surfaces are part of the consumer contract as well, and are held to the same bar: the reference/selector grammar (`participants[].selector`, `data_flow[].offset`, `tool_integration.invariants`), which consumers do parse and which is specified as EBNF in `docs/schema/reference-grammar.md`; and the `data_flow[].inputs[].scope` registry (`docs/schema/semantics-formal.md`), open in the schema to avoid version churn but closed at the consumer-contract level.

## One shared reference/selector grammar

Rather than a new string syntax for every field that needs a predicate or a reference, one small grammar (`param:` references, comparisons, boolean composition, a handful of built-ins) is used everywhere: `tool_integration.invariants`, `participants[].selector`, `data_flow[].offset`, and slot substitution in shape templates. See `docs/schema/reference-grammar.md`.

## Structured tokens over free text

Where a value has structure, it is modelled as structure: named slots with typed kinds in the shape catalog rather than free-text templating, objects rather than type strings for language bindings.

## Design by concrete example

No mechanism is added speculatively. The tagged `source` object, `handle_lifecycle`, the epoch interval mechanism, `memory_space` and the shape catalog each came from writing out a real function (often across several PPMs), finding the vocabulary insufficient, and extending it by the minimum needed. Cross-checking against the full MPI standard worked the same way and added only a new `reduce` input scope and two `handle_kind` values.

## Honest gaps over forced fits

When an operation is close to, but not quite, covered by existing machinery, it is written out fully or left explicitly unmodeled (`null` plus a documented reason) — never forced into the near miss. `MPI_Compare_and_swap` is not bound to the OpenSHMEM-shaped `rma.atomic` pattern: OpenSHMEM and NVSHMEM pass the swap value and comparand by value, MPI passes three separate local buffers, and reusing the shape would silently drop two of them. A wrong fit is worse than a gap because it produces plausible-looking wrong output instead of an obviously missing one.

For the shape catalog this means: when no shape fits a function, a new shape is added right away, even for a single caller, rather than waiting for a second function or parking the difference in `extra`. A second caller tends to appear across six PPMs, so waiting only adds cost. `extra` is reserved for genuinely one-off patches on an otherwise good match (e.g. MPI's tag matching on `handle_bound.post_send`). See `docs/schema/shape-catalog.md`.

## Shapes are erased before shipping

`shape_ref`, `bindings` and `extra` exist only in authored, pre-expansion material. No consumer of the shipped schema, neither a code generator nor a verifier, ever needs to know what a shape is. If that boundary blurs in the implementation, the abstraction has leaked into the wrong layer.

## Versioning discipline

The schema uses closed `enum` arrays throughout, so adding an enum value is additive for data but not for validation: a validator built against an older `$id` rejects a newer, valid document. Any vocabulary growth therefore bumps `$id`, and consumers validate against the version an instance declares, rather than relaxing enums to avoid version bumps. See `docs/schema/schema-versioning.md`.

## Cross-PPM reuse is the payoff

Shape reuse *within* one PPM is real but modest (MPI's send-mode family is the main case). The large effect is reuse *across* PPMs: broadcast, allreduce and the other collectives appear nearly identically in MPI, NCCL, NVSHMEM and OpenSHMEM, differing mostly in parameter names. That reuse is a consequence of the unification goal, not an optimization layered on top of it.
