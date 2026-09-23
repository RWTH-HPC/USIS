"""
NVSHMEM adapter: external-inputs/nvshmem/.../include/host/{nvshmem_api,nvshmem_coll_api}.h
-> IR dicts, cross-referenced against external-inputs/nvshmem/docs/3.7.0/gen/api/*.md.

v1 scope (confirmed by direct inspection, not assumed): nvshmem_api.h (init,
PE-info query, heap mgmt, OpenSHMEM 1.3/1.4 atomics, put, get, point-to-point
sync, teams) + nvshmem_coll_api.h (alltoall(s), barrier, sync, broadcast,
fcollect, reduce(scatter)) only. nvshmemx_api.h/nvshmemx_coll_api.h (the "x"
stream-based and per-thread-group _warp/_block device variants) are
deliberately excluded -- combinatorial type x op x thread-scope explosion,
a structurally different device-side API family that would need its own
adapter design. Flagged as an open question, not decided unilaterally here.

Same bare-header weakness as NCCL (see workflow/extract/nccl/adapter.py's
docstring for the shared const-qualification direction heuristic and its
known blind spot for in-place operations) -- confirmed directly, no
direction/asynchronous annotations exist in these headers either.

Type-generic function families (nvshmem_TYPENAME_broadcast etc.) are
resolved via macro_expand.py against include/device_host/nvshmem_common.cuh's
NVSHMEMI_REPT_FOR_* macros -- **collapsed into one IR entry per family**,
using macro_expand.expand_invocations_grouped(): identity.name carries a
literal "{T}" placeholder (e.g. "nvshmem_{T}_put") and identity.type_family
lists the concrete typenames the family is generic over (e.g.
["int","long","bfloat16",...]) -- matching the schema's own documented
{T}/type_family convention (docs/schema/schema-overview.md). Resolved
2026-07-16: this used to be treated as semantic-tier/out of Extract's scope
(one IR entry per concrete instantiation, 25 separate nvshmem_*_put entries
etc.) -- the type axis turned out to be a purely mechanical, source-derived
signal (the REPT macro's own type-tuple list), so Extract now populates it
directly; see curated/field-provenance.json's updated identity.type_family
entry. The operation axis never collapses (docs/schema/schema-overview.md's
"type axis collapses, operation axis never does" rule) -- confirmed safe
mechanically, since each NVSHMEMI_REPT_FOR_*(...) invocation *line* is
already exactly one operation (see macro_expand.py's own docstring for the
concrete reduce-family example). bindings.c.signature is templated the same
way, using a second placeholder "{CT}" for C-type positions where the
concrete signature would appear (kept distinct from "{T}" because typename
and C type are sometimes different strings for the same logical type, e.g.
("longlong", "long long"), ("bfloat16", "__nv_bfloat16")) -- both get
resolved back to a concrete (typename, ctype) pair only once, by the new
Concretize workflow step (workflow/concretize/), immediately before
Validate. Same rule applied to OpenSHMEM's identical pattern, see
workflow/extract/shmem/adapter.py.
"""

import glob
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from status import Flag  # noqa: E402
import macro_expand  # noqa: E402
from return_kind import classify_return_kind  # noqa: E402

_LAYOUT_COMMON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "common")
sys.path.insert(0, _LAYOUT_COMMON)
from layout import EXTERNAL_INPUTS_DIR  # noqa: E402

_INCLUDE_DIR = os.path.join(
    EXTERNAL_INPUTS_DIR, "nvshmem", "implementation", "libnvshmem-linux-x86_64-3.7.1_cuda13-archive", "include",
)
_DOCS_DIR = os.path.join(EXTERNAL_INPUTS_DIR, "nvshmem", "docs", "3.7.0", "gen", "api")

_V1_HEADERS = ("nvshmem_api.h", "nvshmem_coll_api.h")
_COMMON_HEADER = os.path.join("device_host", "nvshmem_common.cuh")

# Widened twice, for three independent declaration shapes this pattern used to
# skip outright with no flag. Each widening was found separately; the pattern
# below is the union, and dropping any one clause loses real functions.
#
# 2026-09-11 -- the original form required whitespace between the return type
# and the name, and a ';' terminator. Two shapes in these same headers meet
# neither condition (seven functions, among them nvshmem_malloc, whose absence
# curated/README.md had recorded as an Extract coverage gap):
#
#   void *nvshmem_malloc(size_t size);      -- the '*' binds to the NAME, so
#       there is no whitespace before it (also nvshmem_calloc/_align/_ptr).
#   static inline void nvshmem_init() { ... }  -- a definition, not a
#       declaration: it ends in a body, not a ';' (also nvshmem_init_thread,
#       nvshmem_finalize, which forward to the nvshmemi_* internals).
#
# So the return-type group may end in '*', and a declaration may be closed by
# either ';' or the '{' of a definition body. `static`/`inline` are stripped
# alongside the other qualifiers before the return-kind lookup.
#
# 2026-09-12 -- the return-type group must also accept '{'. A type-generic
# family whose RETURN type is the generic type expands to the literal
# placeholder "{CT}", and an [A-Za-z_]-anchored group cannot match it. That
# silently dropped every value-returning generic family here --
# nvshmem_TYPENAME_g and all 8 fetching atomics (_atomic_fetch, _fetch_inc,
# _fetch_add, _fetch_and, _fetch_or, _fetch_xor, _swap, _compare_swap) --
# while their void-returning siblings (_p, _put, _atomic_inc, _atomic_set,
# ...) came through fine, which is why that gap looked like a macro-expansion
# problem rather than a parsing one.
#
# Note the group must be allowed to END in '}' as well as [\w*]: "{CT}" is a
# complete return type. An [A-Za-z_]-only start or a [\w\*]-only end silently
# re-drops one of the two families above.
_DECL_RE = re.compile(
    r"(NVSHMEMI_HOSTDEVICE_PREFIX\s+)?([A-Za-z_{][\w\s\*{}]*?[\w\*}])\s*\b([A-Za-z_{][\w{}]*)\s*\(([^)]*)\)\s*(?:;|\{)",
)

# Widened 2026-07-17 (was "^##" only): the docs mirror is inconsistent about
# heading depth for what's conceptually the same kind of unit -- confirmed
# directly, e.g. sync.md's NVSHMEM_WAIT_UNTIL is "##" but rma.md's
# NVSHMEM_PUT/NVSHMEM_GET are "###" (nested under a "## Blocking RMA" grouping
# heading that itself doesn't match the NVSHMEM_ name pattern, so widening to
# "##" or "###" doesn't risk picking up section-grouping headings by
# accident). Also widened to capture a comma-separated multi-name heading
# (memory.md's "## NVSHMEM_MALLOC, NVSHMEM_FREE, NVSHMEM_ALIGN" covers three
# functions under one shared Description section) -- the old regex's lazy
# single-word capture silently failed to match that heading at all.
_FAMILY_HEADING_RE = re.compile(
    r"^#{2,3}\s+\**\s*(NVSHMEM_\w+(?:\s*,\s*NVSHMEM_\w+)*)\**\s*$", re.MULTILINE | re.IGNORECASE,
)
_PARAM_DOC_BOUNDARY = r"(?:^\*\w+\s*\[(?:IN|OUT|INOUT)\]\*\s*$|^\*\*[\w\s]+\*\*\s*$|^##\s|\Z)"
_PARAM_DOC_RE = re.compile(
    r"^\*(\w+)\s*\[(IN|OUT|INOUT)\]\*\s*$\n+(.+?)(?=" + _PARAM_DOC_BOUNDARY + r")",
    re.MULTILINE | re.DOTALL,
)
# Added 2026-07-17, auditing the pilot corpus: every family section in the docs mirror
# has a "**Description**" ... "**Returns**" block with a real, usable function-level
# summary (confirmed directly against external-inputs/nvshmem/docs/3.7.0/gen/api/{rma,sync,...}.md
# -- e.g. rma.md's NVSHMEM_PUT section). The adapter previously hardcoded identity.desc to
# null with a comment claiming no such text existed -- that claim was checked and was
# wrong; this was a real, fixable Extract gap, not a genuine "nothing to extract" case.
#
# Retired as identity.desc's source 2026-07-20: the block this regex finds is
# correct in CONTENT (it's genuinely the right description) but wrong in
# SHAPE -- whole multi-paragraph sections (up to ~2000 chars / 16 sentences
# in the real corpus), never the one-sentence summary api-schema.json's own
# field description calls for, and at least one contained a raw scrape
# artifact (nvshmem_fence's block included a dangling
# "Table [[mem-order]](https:" markdown-link fragment). Mechanically
# trimming to "first sentence" was considered and rejected for the same
# reason MPI's equivalent heuristic was retired the same day (see
# workflow/extract/mpi/prose.py's module docstring): a real NVSHMEM
# function's semantics routinely need the whole block, so truncating loses
# meaning rather than summarizing it. _build_docs_param_index still computes
# this (kept, not deleted -- correct and cheap, and a reasonable starting
# point for a human/LLM drafting a real curated/supplement/supplement-nvshmem.json
# entry), but its output is no longer wired into identity.desc; see the
# `desc` assignment below and curated/README.md.
_DESC_RE = re.compile(r"\*\*Description\*\*\s*\n+(.+?)\n+\*\*Returns\*\*", re.DOTALL)

# (the old _RETURN_KIND_MAP lived here; superseded 2026-07-21 by the shared,
#  corpus-audited rule in workflow/extract/return_kind.py)


_LINE_COMMENT_RE = re.compile(r"//[^\n]*")
_BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)


def _strip_comments(text):
    """Strip C-style comments before declaration scanning -- without this,
    a bare '// barrier collectives' line immediately preceding a real
    declaration (confirmed present in nvshmem_coll_api.h) gets glued onto
    the next declaration's captured return-type group, since the
    declaration regex isn't anchored to a statement boundary. No string
    literals containing '//' or '/*' exist in these headers, so this
    simple strip is safe here -- not a general C comment stripper."""
    text = _BLOCK_COMMENT_RE.sub(" ", text)
    text = _LINE_COMMENT_RE.sub("", text)
    return text


def _read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return _strip_comments(f.read())


def _parse_c_param(param_text, entry_key, flags):
    text = param_text.strip()
    if text in ("", "void"):
        return None
    constant = text.startswith("const ")
    if constant:
        text = text[len("const "):].strip()
    m = re.match(r"^(.*?)([*\s])(\w+)$", text)
    if m:
        base_type, sep_char, name = m.groups()
    elif "(" in text:
        flags.append(Flag(entry_key=entry_key, field=None, severity="note", reason=f"unparseable C parameter fragment: {param_text!r}"))
        return None
    else:
        # A type with no parameter name -- legal C, and real in these headers:
        # nvshmem_calloc(size_t, size_t) and nvshmem_align(size_t, size_t).
        # Until 2026-09-11 this parser dropped such a parameter entirely, which
        # would make the entry claim the function takes no arguments at all;
        # the caller names it after its position instead.
        base_type, sep_char, name = text, "", None
    base_type = base_type.strip()
    pointer = sep_char == "*" or base_type.endswith("*")
    base_type = base_type.rstrip("*").strip()
    return {"name": name, "base_type": base_type, "constant": constant, "pointer": pointer}


# NVSHMEM's atomic families, grouped by what they actually do to `dest`. The
# const-qualification heuristic below cannot see this and gets the whole
# read-modify-write group wrong in the direction that matters: it reports
# `out`, i.e. "the call writes this and does not read it", for an operation
# whose entire point is to read the old value and write a new one. This is the
# same class of defect as the consumed-handle directions fixed in the CUDA/NCCL
# /OpenMP audit -- a wrong value that looks right, on the one field a race
# detector reads.
#
# Deliberately a closed list of the operations that exist in
# include/host/nvshmem_api.h, not a "contains 'atomic'" rule: `atomic_fetch`
# takes a `const TYPE *dest` and only reads (the heuristic already says `in`),
# and `atomic_set` only writes (`out`). Both stay heuristic-derived.
_AMO_READ_MODIFY_WRITE_OPS = (
    "atomic_inc", "atomic_fetch_inc",
    "atomic_add", "atomic_fetch_add",
    "atomic_and", "atomic_fetch_and",
    "atomic_or", "atomic_fetch_or",
    "atomic_xor", "atomic_fetch_xor",
    "atomic_swap", "atomic_compare_swap",
)


def _direction_override(function_key, param_name):
    """-> a direction the C header's const-qualification cannot express, or
    None to fall through to the docs mirror and then the heuristic."""
    if param_name == "dest" and function_key.endswith(_AMO_READ_MODIFY_WRITE_OPS):
        return "inout"
    return None


def _direction_for(param, entry_key, flags):
    if not param["pointer"]:
        direction = "in"
    else:
        direction = "in" if param["constant"] else "out"
    flags.append(Flag(
        entry_key=entry_key, field=f"parameters[{param['name']}].direction", severity="low_confidence",
        reason="inferred from const-qualification/pointer-ness alone (no direction annotation exists in this header)",
    ))
    return direction


# Small, closed, hand-built table mapping a concrete function's operation
# root to the doc file's family heading name -- built by reading the ~10
# doc files directly, not derived by fuzzy string matching (per this
# project's closed-vocabulary-over-general-matching philosophy). Extend
# by adding an entry when a new real function is found that needs one.
_FAMILY_MAP = {
    "broadcast": "BROADCAST", "broadcastmem": "BROADCAST",
    "alltoall": "ALLTOALL", "alltoallmem": "ALLTOALL",
    "fcollect": "FCOLLECT", "fcollectmem": "FCOLLECT",
    "barrier": "BARRIER", "barrier_all": "BARRIER",
    "sync": "SYNC", "sync_all": "SYNC_ALL", "team_sync": "SYNC",
    "reduce": "REDUCTIONS", "reducescatter": "REDUCTIONS",
    "put": "PUT", "get": "GET",
    "put_nbi": "PUT", "get_nbi": "GET",
    # Added 2026-07-17, auditing the pilot corpus (previously missing --
    # identity.desc was silently null for every one of these): confirmed
    # against external-inputs/nvshmem/docs/3.7.0/gen/api/{setup,memory,sync}.md.
    # "team_my_pe"/"team_n_pes"/"signal_wait_until" are listed *before* the
    # shorter "my_pe"/"n_pes"/"wait_until" they'd otherwise collide with --
    # _family_for already sorts by longest-suffix-first, so this ordering is
    # cosmetic, but keeping the more-specific entries adjacent to what they
    # override makes the collision visible to a future reader.
    "team_my_pe": "TEAM_MY_PE", "team_n_pes": "TEAM_N_PES",
    "my_pe": "MY_PE", "n_pes": "N_PES",
    "free": "FREE", "fence": "FENCE",
    "signal_wait_until": "SIGNAL_WAIT_UNTIL",
    "wait_until": "WAIT_UNTIL",
    # Deliberately NOT extended to the atomics or NVSHMEM_G when those families
    # were added (2026-09-12): amo.md has no *name [IN]* parameter labels at
    # all, and rma.md has them only for the out-of-scope TILE_PUT/TILE_GET, so
    # a mapping for them would resolve to an empty params dict and buy nothing.
    # Logged in docs/cross-ppm-analysis/known-gaps-and-open-questions.md as a
    # docs-mirror conversion gap, not worked around here.
}


def _family_for(function_key):
    for suffix, family in sorted(_FAMILY_MAP.items(), key=lambda kv: -len(kv[0])):
        if function_key.endswith(suffix):
            return family
    return None


def _clean_doc_text(raw):
    text = re.sub(r"`([^`]*)`", r"\1", raw).strip()
    return re.sub(r"\s+", " ", text)


def _build_docs_param_index():
    """-> {family_name: {"params": {param_name: (direction, desc)}, "desc": str_or_None}}."""
    index = {}
    for path in glob.glob(os.path.join(_DOCS_DIR, "*.md")):
        text = _read(path)
        headings = list(_FAMILY_HEADING_RE.finditer(text))
        for i, h in enumerate(headings):
            # h.group(1) is one or more comma-separated "NVSHMEM_X" names sharing one
            # section (e.g. memory.md's "NVSHMEM_MALLOC, NVSHMEM_FREE, NVSHMEM_ALIGN") --
            # every name in the list maps to the same params/desc.
            families = [n.strip().upper().removeprefix("NVSHMEM_") for n in h.group(1).split(",")]
            start = h.end()
            end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
            section = text[start:end]
            params = {}
            for pm in _PARAM_DOC_RE.finditer(section):
                pname, direction_raw, desc_raw = pm.groups()
                params[pname] = ({"IN": "in", "OUT": "out", "INOUT": "inout"}[direction_raw], _clean_doc_text(desc_raw))
            desc_m = _DESC_RE.search(section)
            family_desc = _clean_doc_text(desc_m.group(1)) if desc_m else None
            for family in families:
                if family not in index:
                    index[family] = {"params": params, "desc": family_desc}
    return index


def _split_declarations(text):
    """Every top-level ';'-terminated declaration in text (already
    line-continuation-joined by the caller), skipping #define/#undef lines
    and lines that are themselves inside a still-open macro body (handled
    by the caller only ever passing already-macro-expanded strings or raw
    non-macro header text separately)."""
    return _DECL_RE.finditer(text)


def build_typename_ctype_map(include_dir=None):
    """{typename: ctype, ...} across every type-generic family this adapter
    collapses -- e.g. {"int": "int", "longlong": "long long",
    "bfloat16": "__nv_bfloat16", ...}. Used by workflow/concretize/ to
    resolve the "{T}"/"{CT}" placeholders back to concrete values, re-derived
    fresh from the same real headers this adapter itself parses rather than
    smuggled through every entry (see this session's approved plan) -- one
    source of truth, not a second copy that could drift.
    """
    base = include_dir or _INCLUDE_DIR
    common_text = _read(os.path.join(base, _COMMON_HEADER))
    header_texts = {name: _read(os.path.join(base, "host", name)) for name in _V1_HEADERS}
    macro_table = macro_expand.build_macro_table(common_text, *header_texts.values())

    ctype_map = {}
    for text in header_texts.values():
        for record in macro_expand.expand_invocations_grouped(text, macro_table):
            for typename, ctype in record["ctype_map"].items():
                # One flat map serves the whole model, so a typename that means
                # two different C types across two families would make this
                # ambiguous and silently resolve {CT} wrongly for one of them.
                # NVSHMEM has exactly one candidate -- "half" is `half` in the
                # RMA and reduction tables but `__half` in the extended-AMO
                # table -- and it does not fire today only because that table's
                # half row sits behind an #ifdef __cplusplus whose #else branch
                # is the one this adapter reads (see macro_expand.py). Raise
                # rather than let a future input drift past it, per the same
                # rule the OpenSHMEM reduction fix adopted: a skip that can
                # explain itself must not be silent.
                if ctype_map.get(typename, ctype) != ctype:
                    raise ValueError(
                        f"typename {typename!r} maps to two different C types across NVSHMEM "
                        f"type tables: {ctype_map[typename]!r} vs {ctype!r} -- "
                        f"workflow/concretize/ cannot resolve {{CT}} from a flat per-model map"
                    )
                ctype_map[typename] = ctype
    return ctype_map


def extract_nvshmem(include_dir=None):
    """-> list[(ir_dict, list[Flag])]."""
    base = include_dir or _INCLUDE_DIR
    common_text = _read(os.path.join(base, _COMMON_HEADER))
    header_texts = {name: _read(os.path.join(base, "host", name)) for name in _V1_HEADERS}

    macro_table = macro_expand.build_macro_table(common_text, *header_texts.values())
    docs_index = _build_docs_param_index()

    results = []
    seen_names = set()

    def emit_from_declaration(decl_text, source_label, type_family=None):
        for m in _split_declarations(decl_text):
            hostdevice_prefix, return_type_raw, name, paramlist_text = m.groups()
            # Host/device qualifier detection -- added 2026-07-17 after auditing the pilot
            # corpus found execution.launch was wrong for 9/10 NVSHMEM pilot functions.
            # NVSHMEMI_HOSTDEVICE_PREFIX (typically expands to "__host__ __device__" --
            # confirmed in external-inputs/nvshmem/.../include/host/nvshmem_macros.h) marks a
            # function callable from both host and device; a literal "__device__" prefix
            # with NO NVSHMEMI_HOSTDEVICE_PREFIX (nvshmem_api.h's *_wait_until family) marks
            # a device-ONLY function, not callable from host at all. Neither qualifier means
            # genuinely host-only (e.g. nvshmem_free). This directly grounds execution.launch
            # (see curated/field-provenance.json's own rationale for that field: "Syntactic
            # when the source has __host__/__device__ qualifiers... NVSHMEM headers") --
            # Heuristic Classification derives it from bindings.c.signature's qualifier
            # prefix rather than the previous blanket "always cpu" assumption.
            is_hostdevice = hostdevice_prefix is not None
            is_device_only = not is_hostdevice and return_type_raw.strip().startswith("__device__")
            qualifier_prefix = "__host__ __device__ " if is_hostdevice else ("__device__ " if is_device_only else "")
            # Strip every qualifier token before the return-kind lookup below -- an
            # unstripped "__device__ void" previously failed to match the return-kind
            # exact "void" key, silently corrupting return.kind to the "value" fallback
            # for the whole *_wait_until family (found during the same audit).
            # Preprocessor tokens leak into this capture the same way the
            # __device__/__host__ qualifiers do: a declaration immediately
            # following a "#ifdef __CUDACC__" or "#endif" line picks the
            # directive up as part of its return type once the '#' has been
            # consumed upstream. Left unstripped it corrupted three entries'
            # return.binding_type.c AND their bindings.c.signature outright
            # ("endif int nvshmem_team_my_pe(...)", found 2026-07-21) -- so
            # these are dropped alongside the qualifiers, before both uses.
            # `static`/`inline` join the list 2026-09-11, with the definition
            # form: leaving them in made the return type of nvshmem_init and
            # nvshmem_finalize read "static inline void", which then missed the
            # exact "void" key and fell through to the "value" return kind.
            return_type = " ".join(
                tok for tok in (
                    return_type_raw.replace("NVSHMEMI_HOSTDEVICE_PREFIX", "")
                    .replace("__device__", "").replace("__host__", "").split()
                )
                if tok not in ("ifdef", "ifndef", "endif", "else", "define", "__CUDACC__", "static", "inline")
            )
            if not name.startswith("nvshmem_") or name in seen_names:
                continue
            seen_names.add(name)

            entry_key = f"nvshmem:{name}"
            flags = []
            raw_params = [_parse_c_param(p, entry_key, flags) for p in paramlist_text.split(",")]
            raw_params = [p for p in raw_params if p]

            # Name any parameter the header declares without one after its
            # position, as workflow/extract/openmp/adapter.py does, and say so.
            unnamed = []
            for i, p in enumerate(raw_params):
                if p["name"] is None:
                    p["name"] = f"arg{i}"
                    unnamed.append(p["name"])
            if unnamed:
                flags.append(Flag(
                    entry_key=entry_key, field="parameters[].name", severity="note",
                    reason=f"{source_label} declares {', '.join(unnamed)} without a name; named after their position",
                ))

            family = _family_for(name)
            family_docs = docs_index.get(family) if family else None
            param_docs = family_docs["params"] if family_docs else {}

            parameters = []
            for p in raw_params:
                doc_direction, doc_desc = param_docs.get(p["name"], (None, None))
                override = _direction_override(name, p["name"])
                if override is not None:
                    direction = override
                    flags.append(Flag(
                        entry_key=entry_key, field=f"parameters[{p['name']}].direction", severity="note",
                        reason="read-modify-write atomic: dest is both read and written, which the header's "
                               "const-qualification cannot express and the docs mirror does not label",
                    ))
                elif doc_direction is not None:
                    direction = doc_direction
                else:
                    direction = _direction_for(p, entry_key, flags)
                parameters.append({
                    "name": p["name"],
                    "direction": direction,
                    "desc": doc_desc,
                    "binding_type": {"c": None, "fortran90": None, "fortran08": None, "lis": None, "cpp": None},
                    "asynchronous": False,
                    "constant": p["constant"],
                    "pointer": p["pointer"],
                    "array_type": None,
                    "func_type": None,
                    "length": None,
                    "root_only": False,
                    "_lang_included": {"c": True},
                })

            # See workflow/extract/return_kind.py: "int -> ERROR_CODE" is
            # right for the status-returning majority and wrong for the PE-
            # query (nvshmem_my_pe/_n_pes/_team_translate_pe) and predicate
            # (_test*) families, which return a value and a boolean.
            return_kind = classify_return_kind(name, return_type)
            param_sig = ", ".join(f"{'const ' if p['constant'] else ''}{p['base_type']}{'*' if p['pointer'] else ' '}{p['name']}" for p in raw_params)
            c_signature = f"{qualifier_prefix}{return_type} {name}({param_sig})"

            # identity.desc is never attempted here (retired 2026-07-20, see
            # _DESC_RE's own comment above): the real "**Description**" block
            # _build_docs_param_index finds is correct content but the wrong
            # shape (whole multi-sentence sections, not the one-sentence
            # field api-schema.json calls for). Always null from Extract;
            # filled only via a human-reviewed curated/supplement/supplement-nvshmem.json
            # entry -- see curated/README.md.
            flags.append(Flag(entry_key=entry_key, field="identity.desc", severity="note",
                               reason="not attempted mechanically -- the docs mirror's Description block is real but spans multiple sentences, not a one-line summary; see curated/supplement/supplement-nvshmem.json"))

            ir = {
                "model": "nvshmem",
                "function_key": name,
                "name": name,
                "type_family": list(type_family) if type_family else None,
                "desc": None,
                "since": None,
                "deprecated_in": None,
                "standard_refs": [],
                "bindings": {
                    "c": {"expressible": True, "header": source_label, "signature": c_signature},
                    "fortran90": None, "fortran08": None, "lis": None, "cpp": None,
                },
                "parameters": parameters,
                "return_kind": return_kind,
                "return_binding_type": {"c": return_type},
                "flags": flags,
            }
            results.append((ir, flags))

    for name, text in header_texts.items():
        joined = macro_expand._join_continuations(text)
        non_macro_lines = "\n".join(line for line in joined.split("\n") if not line.strip().startswith("#define") and not line.strip().startswith("#undef"))
        emit_from_declaration(non_macro_lines, name)

        for record in macro_expand.expand_invocations_grouped(text, macro_table):
            emit_from_declaration(record["template"], name, type_family=record["type_family"])

    return results
