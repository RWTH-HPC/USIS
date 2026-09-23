# The Reference and Selector Grammar

One small, closed expression grammar, reused everywhere the schema needs a predicate or a reference, instead of inventing new ad hoc string syntax per field. This is a direct application of the "enumerable vocabulary over embedded logic" principle in `docs/schema/design-conventions.md` — it is deliberately *not* a general expression language.

## Where it's used

- `participants[].selector` — e.g. `"rank == param:root"`
- `tool_integration.invariants` — e.g. `"comm != MPI_COMM_NULL"`, `"count >= 0"`
- `data_flow[].offset` — indexed-shape offset expressions, e.g. `"rank_in(param:comm) * extent_size(param:count, param:datatype)"`
- Shape template slot substitution (embedded `{{slot_name}}` tokens inside larger selector strings)

## Tokens

| Token | Meaning |
|---|---|
| `param:name` | Reference to a `parameters[]` entry by name |
| `rank` | The calling process/PE's rank |
| `self` | Shorthand selector for "the calling thread of execution, cardinality one" |
| `rank_in(comm_ref)` | This rank's index within a communicator/team |
| `is_neighbor(rank, comm_ref)` | True if `rank` is a topology neighbor under `comm_ref`'s attached graph/Cartesian topology |
| `extent_size(count_ref, datatype_ref)` | Byte size of an extent, for offset arithmetic |
| `all_pes` | The default/global scope encompassing every participant in the running job — used on the right side of `in` when a function has no explicit `COMMUNICATOR`/`TEAM` parameter to reference at all (e.g. NVSHMEM's `nvshmem_barrier_all`, SHMEM's `shmem_barrier_all`), as opposed to `rank in param:comm`/`param:team` where one exists |
| `== != in && \|\| !` | Comparison and boolean composition |

## Formal grammar

Both consumer classes *must* parse these strings (a code generator lowers selectors and offsets; a verifier instantiates them), so the one part of the schema consumers parse gets the same rigor as the closed enums. This EBNF is the normative definition; the token table above is the readable summary. A prose table alone let an invented token (`scope:all_pes`) through before the EBNF existed.

```ebnf
selector    = "self" | or_expr ;             (* "self" only as the whole selector *)
or_expr     = and_expr , { "||" , and_expr } ;
and_expr    = unary , { "&&" , unary } ;
unary       = "!" , unary | "(" , or_expr , ")" | comparison ;
comparison  = operand , cmp_op , operand
            | operand , "in" , scope ;
cmp_op      = "==" | "!=" | ">=" | "<=" | ">" | "<" ;
scope       = param_ref | "all_pes" ;
operand     = "rank" | rank_in | is_neighbor | param_ref | integer
            | ppm_const | comm_size | ident ;      (* ppm_const/comm_size/bare ident:
                                                      invariants only, see notes *)
rank_in     = "rank_in" , "(" , param_ref , ")" ;
is_neighbor = "is_neighbor" , "(" , operand , "," , param_ref , ")" ;
comm_size   = "comm_size" , "(" , ( param_ref | ident ) , ")" ;

offset_expr = term , { ( "+" | "-" ) , term } ;   (* data_flow[].offset only *)
term        = factor , { "*" , factor } ;
factor      = "rank" | rank_in | extent_size | param_ref | integer
            | "(" , offset_expr , ")" ;
extent_size = "extent_size" , "(" , param_ref , "," , param_ref , ")" ;

param_ref   = "param:" , identifier ;
ppm_const   = UPPERCASE_IDENTIFIER ;              (* e.g. MPI_COMM_NULL — allowed
                                                     only in tool_integration.invariants *)
ident       = lowercase identifier ;              (* a bare parameter name — allowed
                                                     only in tool_integration.invariants *)
integer     = digit , { digit } ;
```

Notes:
- **Three usage contexts, three start symbols:** `participants[].selector` uses `selector`; `data_flow[].offset` uses `offset_expr` (the only context where arithmetic is legal — over structural quantities like ranks and extent sizes, never runtime data values); `tool_integration.invariants` uses `or_expr` and is the only context where three extra operand forms are legal: bare PPM constants (`MPI_COMM_NULL`), bare parameter names (`count >= 0` — invariants predate the `param:` prefix convention and refer to the entry's own parameters by plain name), and the `comm_size(comm)` builtin (the size of a communicator/team — used by the shipped `mpi_send` example's `dest < comm_size(comm)` invariant).
- **`sync.matching.match_keys` is a reference list, not an expression context:** each element is either a `param_ref` or one of a small set of documented match-key tokens — currently exactly one, `self_rank_as_source` (the sender's own rank standing in for the receiver-side source key). The validator checks match-key elements against exactly these two forms.
- Anything not derivable from this grammar is not a valid string for these fields — a binder or classifier producing one is a bug, not a soft extension. Growing the grammar means editing this EBNF (see the bar under "Deliberate incompleteness" below).
- **Enforcement:** `workflow/formal/grammar.py` — a pure recursive-descent validator for this EBNF (`validate_selector`/`validate_offset`/`validate_invariant`/`validate_match_key`, plus `validate_formal_grammar` walking a fully-inlined formal block). `workflow/formal/test_grammar.py` unit-tests it (including rejecting the exact `scope:all_pes` token that motivated it) and sweeps every golden expansion, the built corpus and the shipped `mpi-api.json` example. The Validate stage runs the same check over every entry. It validates *expansions*, never templates (a `{{slot}}` placeholder in post-expansion output is itself an error).

## Why `is_neighbor()` matters more than its size suggests

Covers MPI's neighborhood collective family (`Neighbor_allgather`, `Neighbor_alltoall`, and their `v`/`w`/nonblocking/persistent variants) without adding a single new shape. Communicator membership (`rank in param:comm`) cannot say "which participants are topology neighbors of the caller", a graph-aware condition. One built-in lets the entire neighborhood-collective family reuse the *existing* gather/alltoall shapes with only a different `scope_selector` binding — a direct validation of the "extend the grammar, not the shape count" preference when a gap is purely about which participants are selected, not about the data-flow shape itself.

## Deliberate incompleteness

This grammar is intentionally small. Its built-ins beyond the operators are `rank_in()`, `extent_size()`, `is_neighbor()` and `all_pes` (for `nvshmem_barrier_all`/`shmem_barrier_all`, which need a scope selector but have no `COMMUNICATOR`/`TEAM` parameter to point at). Any addition to this grammar should be held to the same bar: does it let an *existing* pattern reuse *existing* shapes/mechanisms more cleanly, or does it start turning the grammar into a general expression language? The latter is ruled out — see `docs/schema/design-conventions.md`.

Note: unlike `data_flow[].op`/`handle_kind`/other closed JSON-schema enums, grammar tokens are not schema-enforced (`participants[].selector` etc. are plain `string`-typed fields, validated only by convention/documentation) — so growing this grammar does **not** require an `api-schema.json` `$id` version bump, the way growing `semantics.formal`'s actual enums does. See `docs/schema/schema-versioning.md`.

## What this grammar is not used for

Anything that would require arithmetic over runtime *values* (not just structural properties like rank or communicator membership) has been deliberately kept out. The clearest example: SHMEM's `wait_until`-style value-dependent blocking ("block until this memory location satisfies a runtime predicate") has no representation anywhere in the schema, specifically because giving it one would mean extending this grammar to cover arbitrary value comparisons — too large a step toward a general predicate language. See `docs/cross-ppm-analysis/known-gaps-and-open-questions.md`.
