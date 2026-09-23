"""
Shared return.kind classification for the two OpenSHMEM-lineage extractors
(workflow/extract/shmem/adapter.py, workflow/extract/nvshmem/adapter.py).

**Why this exists (fixed 2026-07-21).** Both adapters previously mapped their
C return type with the same one-line rule -- "void -> void, anything else ->
ERROR_CODE" (SHMEM) / "int -> ERROR_CODE, void -> void, anything else ->
value" (NVSHMEM). That rule is right for the majority of each API and wrong
for two whole families, in a way that inverts the field's meaning rather than
merely blurring it: a consumer reading `return.kind == "ERROR_CODE"` on
`shmem_malloc` concludes the call returns a status when it actually returns
the allocation, and on `shmem_int_atomic_fetch` that it returns a status when
it actually returns the fetched datum.

Audited against instances/0_syntactic-api.json (2026-07-21), the old rule
mislabelled 40 SHMEM and 9 NVSHMEM entries:

  - 23 SHMEM `TYPE`-returning typed atomics (`shmem_TYPE_atomic_fetch`,
    `_fetch_add`, `_swap`, `_g`, ...) -- the fetched value.
  - 8 SHMEM + 8 NVSHMEM `size_t` and 2 SHMEM + 1 NVSHMEM `uint64_t` returns
    -- queried sizes and fetched signal values.
  - 7 SHMEM `void *` returns (`shmem_malloc`, `_align`, `_calloc`,
    `_realloc`, `shmem_ptr`, ...) -- the allocation/address itself.
  - the PE-number and boolean-predicate `int` families in both PPMs.

**The rule, and where it deliberately stops.** The C return type settles
everything except `int`, because `int` is genuinely overloaded in both APIs:
a status for `shmem_team_split_strided`, a PE number for `shmem_my_pe`, a
predicate for `shmem_test_lock`. Rather than guess per function, only the two
families whose naming convention is unambiguous across both corpora are
carved out by name (`_my_pe`/`_n_pes`/`_translate_pe`; the
`_accessible`/`_test*`/`test_lock` predicates) -- everything else `int` keeps
ERROR_CODE, which is correct for all 40 remaining int-returning functions in
the two corpora (every collective, every `_split_*`, `_ctx_create`,
`_init_thread`, ...). This follows the project's "closed, grounded vocabulary
over a general guess" convention: the carve-outs are literal naming families
confirmed against the corpus, not a heuristic that could drift.
"""

import re

# `int`-returning names whose int is a PE number or PE count, not a status.
# Suffix-anchored so only the real family matches: shmem_my_pe, shmem_n_pes,
# shmem_team_my_pe, shmem_team_n_pes, shmem_team_translate_pe and their four
# NVSHMEM counterparts -- confirmed to be exactly the corpus's PE-query set.
_PE_VALUE_RE = re.compile(r"_(my_pe|n_pes|translate_pe)$")

# `int`-returning names whose int is a 0/1 (or 0/nonzero) predicate answer.
# Two families: the `*_accessible` reachability pair, and the point-poll
# `_test` family -- anchored exactly as workflow/classify/heuristics.py's
# _SHMEM_TEST_FAMILY_RE is, plus `test_lock`, which that one deliberately
# excludes there (it is a lock-acquisition attempt, not a completion poll)
# but which is still a predicate return here.
_BOOL_RE = re.compile(r"(_accessible|_test(_all|_any|_some)?(_vector)?|test_lock)$")


def classify_return_kind(function_name, c_return_type):
    """(function name, normalized C return type) -> a return.kind enum value.

    `c_return_type` must already have qualifiers/preprocessor tokens stripped
    (each adapter does this before calling); "void" and "" both mean void.
    """
    t = (c_return_type or "").strip()

    if t in ("", "void"):
        return "void"

    # A returned pointer is the object itself (an allocation or an address),
    # never a status -- RESULT is the schema's kind for exactly this.
    if "*" in t:
        return "RESULT"

    if t == "int":
        if _PE_VALUE_RE.search(function_name):
            return "value"
        if _BOOL_RE.search(function_name):
            return "bool"
        # Both standards' own convention for every remaining int-returning
        # routine: zero on success, nonzero on failure.
        return "ERROR_CODE"

    # Every other scalar return type in both corpora (TYPE, size_t, uint64_t,
    # ptrdiff_t, ...) is a datum the call computed or fetched.
    return "value"
