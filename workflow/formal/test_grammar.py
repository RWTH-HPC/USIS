"""
Tests for workflow/formal/grammar.py -- the reference-grammar validator.

Two halves:
  1. unit cases: known-good and known-bad strings for each of the three
     start symbols, including the exact real strings from the shipped
     mpi-api.json example, and the exact bad token
     (`scope:all_pes`) that motivated building this validator at all.
  2. corpus sweep: every golden example's expected_expansion in
     curated/shapes/seed-assignments.json, every entry in
     instances/4_final-api.json when a build has produced it (formal blocks +
     tool_integration.invariants), and docs/schema/examples/mpi-api.json's own invariants must all
     validate clean.

Run: python3 workflow/formal/test_grammar.py
"""

import json
import os
import sys

_LAYOUT_COMMON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common")
sys.path.insert(0, _LAYOUT_COMMON)
from layout import OUT_DIR  # noqa: E402

sys.path.insert(0, os.path.dirname(__file__))
from grammar import (  # noqa: E402
    GrammarError,
    validate_formal_grammar,
    validate_invariant,
    validate_match_key,
    validate_offset,
    validate_selector,
)

_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
_EXPANSIONS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "testdata", "expansions.json")
_FINAL_PATH = os.path.join(OUT_DIR, "4_final-api.json")
# The documented worked example, validated where it is documented -- so the
# example in docs/schema/reference-grammar.md is machine-verified, not just asserted.
_MPI_EXAMPLE_PATH = os.path.join(_ROOT, "docs", "schema", "examples", "mpi-api.json")

GOOD_SELECTORS = [
    "self",
    "rank == param:root",
    "rank in param:comm",
    "rank in param:team",
    "rank in all_pes",
    "!( rank == param:root ) && rank in param:comm",
    "is_neighbor(rank, param:comm)  == 1",
]

BAD_SELECTORS = [
    "rank in scope:all_pes",     # the invented pilot token this validator exists to catch
    "rank == root",              # bare identifier outside invariants
    "rank ==",                   # truncated
    "rank == param:root extra",  # trailing garbage
    "comm_size(comm) > 0",       # comm_size is invariant-only
    "",
]

GOOD_OFFSETS = [
    "rank_in(param:comm) * extent_size(param:sendcount, param:sendtype)",
    "rank_in(param:comm) * extent_size(param:recvcount, param:recvtype)",
    "rank * 4 + 1",
    "(rank_in(param:team) + 1) * extent_size(param:count, param:datatype)",
]

BAD_OFFSETS = [
    "rank == param:root",        # boolean, not arithmetic
    "extent_size(param:count)",  # arity
    "rank_in(comm)",             # bare identifier argument
    "rank *",
]

GOOD_INVARIANTS = [
    "comm != MPI_COMM_NULL",
    "count >= 0",
    "dest >= 0 && dest < comm_size(comm)",
    "param:count >= 0",
]

BAD_INVARIANTS = [
    "count >= ",
    "dest < comm_size()",
    "buffer_after(buf) == buffer_before(buf)",  # Option-C-style function -- not in the grammar
]

GOOD_MATCH_KEYS = ["param:comm", "param:tag", "self_rank_as_source"]
BAD_MATCH_KEYS = ["scope:all_pes", "comm", "param:", "rank"]


def _unit_cases():
    failures = []
    for good, fn in ((GOOD_SELECTORS, validate_selector), (GOOD_OFFSETS, validate_offset),
                     (GOOD_INVARIANTS, validate_invariant), (GOOD_MATCH_KEYS, validate_match_key)):
        for s in good:
            try:
                fn(s)
            except GrammarError as e:
                failures.append(f"expected VALID but rejected: {s!r} -- {e}")
    for bad, fn in ((BAD_SELECTORS, validate_selector), (BAD_OFFSETS, validate_offset),
                    (BAD_INVARIANTS, validate_invariant), (BAD_MATCH_KEYS, validate_match_key)):
        for s in bad:
            try:
                fn(s)
                failures.append(f"expected INVALID but accepted: {s!r}")
            except GrammarError:
                pass
    return failures


def _corpus_sweep():
    failures = []

    with open(_EXPANSIONS_PATH) as f:
        expansions = json.load(f)["expansions"]
    n_formal = 0
    for key, expansion in sorted(expansions.items()):
        errs = validate_formal_grammar(expansion)
        n_formal += 1
        for e in errs:
            failures.append(f"pinned expansion {key}: {e}")

    if os.path.exists(_FINAL_PATH):
        with open(_FINAL_PATH) as f:
            final = json.load(f)
        for key, entry in final.get("entries", {}).items():
            errs = validate_formal_grammar((entry.get("semantics") or {}).get("formal"))
            for e in errs:
                failures.append(f"corpus {key}: {e}")
            for i, inv in enumerate((entry.get("tool_integration") or {}).get("invariants") or []):
                try:
                    validate_invariant(inv)
                except GrammarError as e:
                    failures.append(f"corpus {key}: tool_integration.invariants[{i}]: {e}")

    with open(_MPI_EXAMPLE_PATH) as f:
        mpi_example = json.load(f)
    for entry_key, entry in mpi_example.items():
        if not isinstance(entry, dict) or "tool_integration" not in entry:
            continue
        for i, inv in enumerate(entry["tool_integration"].get("invariants") or []):
            try:
                validate_invariant(inv)
            except GrammarError as e:
                failures.append(f"mpi-api.json {entry_key}: invariants[{i}]: {e}")
        errs = validate_formal_grammar((entry.get("semantics") or {}).get("formal"))
        for e in errs:
            failures.append(f"mpi-api.json {entry_key}: {e}")

    return failures, n_formal


def run():
    failures = _unit_cases()
    corpus_failures, n_formal = _corpus_sweep()
    failures += corpus_failures

    if failures:
        print(f"{len(failures)} FAILURE(S):")
        for f_ in failures:
            print(f"  - {f_}")
        return 1

    print(f"unit cases pass; corpus sweep clean ({n_formal} golden expansions, "
          f"the built corpus when present, and the shipped mpi-api.json example all conform "
          f"to docs/schema/reference-grammar.md's EBNF).")
    return 0


if __name__ == "__main__":
    sys.exit(run())
