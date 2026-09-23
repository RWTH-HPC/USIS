"""
OpenSHMEM adapter: external-inputs/shmem/tex/shmem-standard/content/*.tex -> IR dicts.

No prebuilt tool exists for OpenSHMEM the way MPI Forum's binding-tool
exists for MPI -- this is a new, narrow, macro-pattern parser (never a
general LaTeX parser), grounded directly in the 4+ content/*.tex files read
while designing this adapter (shmem_broadcast.tex, shmem_atomic_add.tex,
shmem_put.tex, shmem_barrier_all.tex).

Only \\begin{Csynopsis}/\\begin{CsynopsisCol} declaration blocks are treated
as real, individually-linkable C symbols. \\begin{C11synopsis} blocks are
deliberately skipped: they describe a single C11 _Generic-dispatched name
(e.g. "shmem_atomic_add", TYPE-generic via the C standard's own generic
selection, not N distinct exported symbols) -- extracting them as if they
were concrete functions would silently duplicate/conflict with the real
per-type symbols the Csynopsis blocks already name explicitly
(shmem_int_atomic_add, shmem_long_atomic_add, ...).

A \\FuncParam{TYPENAME}-generic declaration line is **collapsed into one IR
entry per family**: identity.name carries a literal "{T}" placeholder (e.g.
"shmem_{T}_put") and identity.type_family lists the concrete typenames from
the relevant type table (e.g. ["int","long","float",...]) -- matching the
schema's own documented {T}/type_family convention
(docs/schema/schema-overview.md). Resolved 2026-07-16: this used to be
treated as semantic-tier/out of Extract's scope (one IR entry per (c_type,
typename) pair, e.g. 25 separate shmem_*_put entries) -- the type axis
turned out to be a purely mechanical, source-derived signal (type_tables.py's
own parsed table), so Extract now populates it directly; see
curated/field-provenance.json's updated identity.type_family entry. The
operation axis never collapses -- structurally guaranteed here, since each
concrete *operation* already lives in its own separate .tex file
(shmem_atomic_add.tex vs shmem_atomic_fetch.tex, ...; confirmed by listing
external-inputs/shmem/tex/shmem-standard/content/) -- collapsing only ever multiplies
out the TYPENAME axis within one file's \\FuncDecl line, never merges two
files/operations. bindings.c.signature is templated the same way, using a
second placeholder "{CT}" for the C-type position (param base_type) --
resolved back to a concrete (typename, ctype) pair only once, by the new
Concretize workflow step (workflow/concretize/), immediately before
Validate.

A \\FuncParam{SIZE}-generic line (e.g. shmem_putmem's size-suffixed family)
is a **different axis, deliberately left untouched by this change** -- it
still expands into one entry per literal size found in the file's own
"\\SIZE{} is one of \\CONST{...}" line, exactly as before.
"""

import glob
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ir import Confident  # noqa: E402
from status import Flag  # noqa: E402
import type_tables  # noqa: E402
import changelog  # noqa: E402
from return_kind import classify_return_kind  # noqa: E402

_LAYOUT_COMMON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "common")
sys.path.insert(0, _LAYOUT_COMMON)
from layout import EXTERNAL_INPUTS_DIR  # noqa: E402

_CONTENT_DIR = os.path.join(EXTERNAL_INPUTS_DIR, "shmem", "tex", "shmem-standard", "content")

_APISUMMARY_START_RE = re.compile(r"\\apisummary\{")
# "shmem_{T}_and_reduce" -> "and"; also _to_all, _inscan and _exscan, the other
# three suffixes the two reduction tables serve.
_REDUCTION_OP_RE = re.compile(r"\{T\}_(\w+?)_(?:reduce|to_all|inscan|exscan)$")

_SYNOPSIS_BLOCK_RE = re.compile(r"\\begin\{(Csynopsis|CsynopsisCol)\}(.*?)\\end\{\1\}", re.DOTALL)
_C11_BLOCK_RE = re.compile(r"\\begin\{C11synopsis\}(.*?)\\end\{C11synopsis\}", re.DOTALL)
# The FuncDecl name often contains a nested \FuncParam{TYPENAME|SIZE} group
# (itself containing a '}'), so a plain [^}]* capture truncates at that
# inner brace. Allow either non-brace characters or one balanced
# \FuncParam{...} group instead of a flat negated-class capture.
_FUNCDECL_LINE_RE = re.compile(
    r"^(.*?)@\\FuncDecl\{((?:[^{}]|\\FuncParam\{[^}]*\})*)\}@\s*\(([^;]*)\)\s*;",
    re.MULTILINE,
)
_FUNCPARAM_RE = re.compile(r"\\FuncParam\{(\w+)\}")
_TABLE_REF_RE = re.compile(r"Table[~ ]\\ref\{(\w+)\}")
_CONST_LIST_RE = re.compile(r"\\CONST\{([^}]*)\}")
_APIARGUMENT_START_RE = re.compile(r"\\apiargument\{(IN|OUT|INOUT|None\.?)\}")
_DEPRECATE_BEGIN = "\\begin{DeprecateBlock}"
_DEPRECATE_END = "\\end{DeprecateBlock}"

_DIRECTION_MAP = {"IN": "in", "OUT": "out", "INOUT": "inout"}

_MACRO_STRIP_PATTERNS = [
    (re.compile(r"\\ac\{([^}]*)\}"), r"\1"),
    (re.compile(r"\\acp\{([^}]*)\}"), r"\1"),
    (re.compile(r"\\openshmem"), "OpenSHMEM"),
    (re.compile(r"\\FUNC\{([^}]*)\}"), lambda m: m.group(1).replace("\\_", "_").replace("\\", "")),
    (re.compile(r"\\VAR\{([^}]*)\}"), lambda m: m.group(1).replace("\\_", "_").replace("\\", "")),
    (re.compile(r"\\dest\{?\}?"), "dest"),
    (re.compile(r"\\source\{?\}?"), "source"),
    (re.compile(r"\\_"), "_"),
    (re.compile(r"\\[a-zA-Z]+\{([^}]*)\}"), r"\1"),
    (re.compile(r"\\[a-zA-Z]+"), ""),
    # LaTeX's non-breaking space. Last, so it also catches the one left
    # behind by the \ref{} unwrap two rules up: "Table~\ref{p2p-consts}"
    # became "Table~p2p-consts" in 13 descs (audited 2026-07-21).
    (re.compile(r"~"), " "),
]


def _extract_braced(text, open_brace_index):
    """text[open_brace_index] must be '{'. Returns the content between it
    and its matching '}', respecting nested braces (\\apisummary{...\\ac{PE}...}
    has a real nested brace pair that a non-greedy regex can't see past)."""
    assert text[open_brace_index] == "{"
    depth = 0
    for i in range(open_brace_index, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[open_brace_index + 1:i]
    return text[open_brace_index + 1:]


# A \apisummary{} can contain a nested \begin{DeprecateBlock}...\end{DeprecateBlock}
# holding the summary of the *deprecated* variant the same content file also
# documents -- shmem_sync.tex carries the team-based sentence at the top level
# and the active-set sentence inside the block. Both were ending up
# concatenated into one identity.desc, with the environment name itself
# surviving as the literal word "DeprecateBlock" (the generic \macro{arg}
# unwrap in _MACRO_STRIP_PATTERNS turns \begin{DeprecateBlock} into its own
# argument). That produced a two-paragraph desc for a field documented as one
# sentence, describing two different routines at once.
#
# This is the same content-file-granularity problem field-semantics.md's
# identity.since warning describes, but with the opposite outcome: there the
# source genuinely cannot tell the two routines apart, so Extract emits null;
# here it can -- the deprecated text is exactly what is inside the block, the
# current text is exactly what is outside it -- so the block is dropped rather
# than guessed at. Found 2026-07-21 (shmem_sync, shmem_team_sync).
_DEPRECATE_BLOCK_RE = re.compile(r"\\begin\{DeprecateBlock\}.*?\\end\{DeprecateBlock\}", re.DOTALL)


def _find_apisummary(text):
    m = _APISUMMARY_START_RE.search(text)
    if not m:
        return None
    return _DEPRECATE_BLOCK_RE.sub("", _extract_braced(text, m.end() - 1))


def _strip_macros(text):
    for pattern, repl in _MACRO_STRIP_PATTERNS:
        text = pattern.sub(repl, text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_c_param(param_text, entry_key, flags):
    """'const TYPE *source' / 'shmem_team_t team' / 'int PE_root' -> dict."""
    text = param_text.strip()
    if text in ("", "void"):
        return None
    constant = text.startswith("const ")
    if constant:
        text = text[len("const "):].strip()
    m = re.match(r"^(.*?)([*\s])(\w+)$", text)
    if not m:
        flags.append(Flag(entry_key=entry_key, field=None, severity="note", reason=f"unparseable C parameter fragment: {param_text!r}"))
        return None
    base_type, sep_char, name = m.groups()
    base_type = base_type.strip()
    pointer = "*" in (base_type + sep_char) or sep_char == "*"
    # collapse any stray '*' left on base_type into the pointer flag
    base_type = base_type.rstrip("*").strip()
    return {"name": name, "base_type": base_type, "constant": constant, "pointer": pointer}


def _parse_param_list(paramlist_text, entry_key, flags):
    parts = [p.strip() for p in paramlist_text.split(",")]
    out = []
    for p in parts:
        parsed = _parse_c_param(p, entry_key, flags)
        if parsed:
            out.append(parsed)
    return out


def _next_brace_content(text, from_index):
    """Find the next '{' at/after from_index (skipping whitespace only) and
    return (content, index_just_past_matching_close_brace)."""
    i = from_index
    while i < len(text) and text[i].isspace():
        i += 1
    if i >= len(text) or text[i] != "{":
        return None, from_index
    content = _extract_braced(text, i)
    depth = 1
    j = i + 1
    while j < len(text) and depth > 0:
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
        j += 1
    return content, j


def _collect_argument_docs(apidefinition_text):
    """{param_name: (direction, desc)} from \\apiargument{DIR}{name}{desc}
    blocks. Brace-counted rather than regex-lookahead-terminated: this
    standard's source uses a trailing '%' LaTeX end-of-line comment marker
    directly after some arguments' closing brace (e.g. shmem_broadcast.tex's
    \\apiargument{IN}{team}{...}%), which breaks a whitespace-only lookahead
    boundary between one argument and the next -- found by direct inspection
    after a first regex-based attempt silently merged two arguments' text.
    """
    docs = {}
    for m in _APIARGUMENT_START_RE.finditer(apidefinition_text):
        direction_raw = m.group(1)
        name_raw, after_name = _next_brace_content(apidefinition_text, m.end())
        if name_raw is None:
            continue
        desc_raw, _ = _next_brace_content(apidefinition_text, after_name)
        if direction_raw.startswith("None"):
            continue
        name = name_raw.replace("\\_", "_").replace("\\", "").strip()
        docs[name] = (_DIRECTION_MAP.get(direction_raw, "in"), _strip_macros(desc_raw or ""))
    return docs


def _resolve_axis(where_text):
    """-> ("typename", [(c_type, typename), ...]) or ("size", [8,16,...]) or (None, [])."""
    table_match = _TABLE_REF_RE.search(where_text)
    if table_match:
        return "typename", table_match.group(1)
    const_match = _CONST_LIST_RE.search(where_text)
    if const_match:
        sizes = [s.strip() for s in const_match.group(1).split(",")]
        return "size", sizes
    return None, None


def _text_after(source_text, start_index, limit=400):
    return source_text[start_index:start_index + limit]


def _build_parameters(parsed_params, arg_docs, entry_key, flags):
    out = []
    for p in parsed_params:
        direction, desc = arg_docs.get(p["name"], (None, None))
        if direction is None:
            # schema's parameters[].direction has no null option (required
            # string enum) -- unlike identity.desc/since, there is no
            # legal "we don't know" value to fall back to, so a default
            # must be chosen. "in" is the common case; every instance is
            # flagged low_confidence rather than asserted silently.
            direction = "in"
            flags.append(Flag(entry_key=entry_key, field=f"parameters[{p['name']}].direction", severity="low_confidence",
                               reason="no matching \\apiargument{} block found for this parameter name; defaulted to 'in'"))
        # The standard's own \apiargument{} annotation and its own C signature
        # can disagree, and when they do the C type wins: a `const T *` cannot
        # be written by the callee -- that is a language guarantee, not an
        # interpretation. shmem_atomic_fetch_nbi.tex annotates `source` as OUT
        # while declaring it `const TYPE *source` and describing it as "Symmetric
        # address of the SOURCE data object"; both the type and the prose say it
        # is read, so the annotation is a defect in the standard. Corrected here
        # rather than propagated, and flagged every time so the correction stays
        # visible instead of looking like clean extraction. 28 concrete entries
        # (the typed shmem_ctx_*_atomic_fetch_nbi family), found 2026-07-21 by
        # the const-vs-direction cross-check.
        if p.get("constant") and direction in ("out", "inout"):
            flags.append(Flag(entry_key=entry_key, field=f"parameters[{p['name']}].direction", severity="note",
                               reason=(f"standard annotates \\apiargument{{{direction.upper()}}} but declares the parameter "
                                       f"const, which C forbids for an output; corrected to 'in' on the C type's authority")))
            direction = "in"
        out.append({
            "name": p["name"],
            "direction": direction,
            "desc": desc,
            "binding_type": {"c": None, "fortran90": None, "fortran08": None, "lis": None, "cpp": None},
            # schema's parameters[].asynchronous is a required boolean, no
            # null option -- OpenSHMEM's raw source has no equivalent of
            # MPI's explicit asynchronous flag, so there is no legal null
            # fallback here either. Defaulted false (the common case) and
            # flagged, rather than guessed true for some subset without a
            # real signal to base that guess on.
            "asynchronous": False,
            "constant": p["constant"],
            "pointer": p["pointer"],
            "array_type": None,
            "func_type": None,
            "length": None,        # confirmed gap: no cross-reference macro ties e.g. nelems to a buffer param
            # schema's parameters[].root_only is a required boolean, no null
            # option. field-provenance.json's rationale ("already present
            # as an explicit literal flag... in every PPM's raw dump seen
            # so far") was written against the output of an earlier, retired
            # header parser -- it does not hold for this adapter's real tex parsing;
            # no equivalent annotation exists in \apiargument{}. Same
            # honest-default-plus-flag treatment as asynchronous above.
            "root_only": False,
            "_lang_included": {"c": True},
        })
    return out


def _c_type_string(base_type, pointer, constant):
    prefix = "const " if constant else ""
    return f"{prefix}{base_type}{' *' if pointer else ''}".rstrip()


def _emit_for_declaration(name_template, param_list_text, where_text, tables, entry_key_prefix, deprecated, flags_out):
    """-> list of (real_name, [param dict], type_family|None) for one \\FuncDecl line.

    type_family is the list of canonical typenames when this is a
    TYPENAME-generic family (collapsed to exactly one result tuple
    regardless of how many concrete types the table lists), and None for
    every other case (including the SIZE axis, which still expands into one
    result tuple per concrete size -- a different, untouched axis).
    """
    axis_kind, axis_data = _resolve_axis(where_text)
    has_typename_placeholder = "\\FuncParam{TYPENAME}" in name_template
    has_size_placeholder = "\\FuncParam{SIZE}" in name_template

    results = []

    def clean_name(n):
        return n.replace("\\_", "_").replace("\\", "")

    if has_typename_placeholder:
        if axis_kind != "typename" or axis_data not in tables:
            flags_out.append(Flag(entry_key=None, field=None, severity="skipped",
                                   reason=f"{entry_key_prefix}: TYPENAME-generic declaration but no resolvable type table ({where_text[:80]!r})"))
            return results
        real_name = clean_name(name_template.replace("\\FuncParam{TYPENAME}", "{T}"))
        # A reduction or scan routine names its operation in its own symbol
        # (shmem_{T}_and_reduce, shmem_{T}_sum_inscan), and its table says which
        # types support that operation -- the whole table would mint
        # shmem_char_and_reduce, which the standard does not define.
        type_pairs = None
        operation_match = _REDUCTION_OP_RE.search(real_name)
        if operation_match:
            type_pairs = type_tables.reduction_types_for_operation(axis_data, operation_match.group(1))
        if type_pairs is None:
            type_pairs = tables[axis_data]
        params = [_param_with_type_sub(p, "{CT}") for p in param_list_text]
        type_family = [typename for _c_type, typename in type_pairs]
        results.append((real_name, params, type_family))
    elif has_size_placeholder:
        if axis_kind != "size":
            flags_out.append(Flag(entry_key=None, field=None, severity="skipped",
                                   reason=f"{entry_key_prefix}: SIZE-generic declaration but no resolvable \\CONST{{}} list ({where_text[:80]!r})"))
            return results
        for size in axis_data:
            real_name = clean_name(name_template.replace("\\FuncParam{SIZE}", size))
            results.append((real_name, param_list_text, None))
    else:
        real_name = clean_name(name_template)
        results.append((real_name, param_list_text, None))

    return results


def _param_with_type_sub(param, c_type):
    if param["base_type"] == "TYPE":
        return {**param, "base_type": c_type}
    return param


def build_typename_ctype_map(tables=None):
    """{typename: ctype, ...} across every TYPENAME table this adapter
    collapses -- e.g. {"int": "int", "longlong": "long long", ...}. Used by
    workflow/concretize/ to resolve the "{T}"/"{CT}" placeholders back to
    concrete values, re-derived fresh from type_tables.py's own parse of the
    real tex tables rather than smuggled through every entry (see this
    session's approved plan) -- one source of truth, not a second copy that
    could drift.
    """
    tables = tables if tables is not None else type_tables.parse_type_tables()
    ctype_map = {}
    for pairs in tables.values():
        for c_type, typename in pairs:
            ctype_map[typename] = c_type
    return ctype_map


def _since_for(path, deprecated, since_map):
    """(version_string, provenance_note) for one routine.

    changelog.build_since_map() resolves to a *content file*, but a content
    file routinely documents several routines with different histories, so
    attributing its version to every routine in it is only safe when they
    share one history. The case that exposed this (2026-07-21):
    shmem_broadcast.tex is referenced by 1.5's "Added team-based collective
    functions: ... shmem_broadcast[mem] ..." item, and the same file also
    documents shmem_broadcast32/64 -- which that very release *deprecated*.
    File-level attribution therefore reported the deprecation release as the
    introduction release for both.

    Narrowing by the function names an item's prose lists was tried and
    rejected as unsound: the changelog writes display names, not real
    symbols, in a different case (`\\FUNC{SHMEM\\_FETCH}` for the routine
    actually called shmem_atomic_fetch), and "Added" is not reliably an
    introduction marker there either ("Added \\CTYPE{volatile} to ... in
    \\FUNC{SHMEM\\_WAIT}" is a signature change to a routine that already
    existed). Matching on that text would trade one silent misattribution
    for several.

    What IS reliable is the standard's own \\begin{DeprecateBlock} markup,
    which this adapter already parses for its own sake. It doesn't identify
    the right version, but it does identify precisely the files where the
    file-level answer cannot be trusted: a file containing both a
    DeprecateBlock routine and a changelog "Added" reference is, by
    construction, a file whose routines do not share one history.

    Deriving a version from that marker was tried too, and also rejected:
    "deprecated => predates the added content" holds for shmem_broadcast32
    (1.0, deprecated 1.5) and fails for shmem_alltoall32 (introduced 1.3 by
    that very item, deprecated 1.5). Both readings are consistent with
    everything this source says, so choosing either would be a coin flip
    dressed as an extraction.

    So this case resolves to `None` -- an explicit, flagged gap for
    curated/supplement/supplement-shmem.json to fill per function, per the project's
    "explicit gaps over confident guesses" convention. It is deliberately
    narrow: only mixed-generation files are affected (15 routines in the
    current corpus), and every single-generation file keeps its file-level
    attribution unchanged.
    """
    version = since_map.get(os.path.basename(path))

    if version and deprecated:
        return None, (
            "UNRESOLVED: this routine's content file is referenced by an 'Added'/'New' changelog item "
            f"for {version}, but the routine is inside a \\begin{{DeprecateBlock}} -- so the file mixes "
            "generations and the item's version cannot be attributed to this routine. Which of the two "
            "it is (introduced by that release and later deprecated, e.g. shmem_alltoall32; or predating "
            "it entirely, e.g. shmem_broadcast32) is not derivable from this source -- left null for "
            "curated/supplement/supplement-shmem.json to fill per function"
        )

    if version:
        return version, ("found in an 'Added'/'New' item of the standard's own changelog "
                         "(external-inputs/shmem/tex/shmem-standard/content/backmatter.tex), attributed at "
                         "content-file granularity")

    return "OpenSHMEM-1.0", ("not mentioned in any 'Added'/'New' changelog item from Version 1.1 "
                             "onward -- inferred to predate the changelog's own coverage")


def extract_shmem(content_dir=None, tables=None, since_map=None):
    """-> list[(ir_dict, list[Flag])]."""
    directory = content_dir or _CONTENT_DIR
    tables = tables if tables is not None else type_tables.parse_type_tables()
    since_map = since_map if since_map is not None else changelog.build_since_map()

    all_results = []

    for path in sorted(glob.glob(os.path.join(directory, "*.tex"))):
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()

        if "\\begin{apidefinition}" not in text:
            continue  # topic-intro file, not a per-function file

        file_flags = []
        declarations_in_file = sum(
            1 for block in _SYNOPSIS_BLOCK_RE.finditer(text)
            for _decl in _FUNCDECL_LINE_RE.finditer(block.group(2)))
        entries_before_file = len(all_results)
        apisummary_raw = _find_apisummary(text)
        desc = _strip_macros(apisummary_raw) if apisummary_raw else None

        arg_docs = _collect_argument_docs(text)

        for block_match in _SYNOPSIS_BLOCK_RE.finditer(text):
            block_text = block_match.group(2)
            block_start = block_match.start()
            deprecated = text.rfind(_DEPRECATE_BEGIN, 0, block_start) > text.rfind(_DEPRECATE_END, 0, block_start)

            after_block = _text_after(text, block_match.end())

            for decl_match in _FUNCDECL_LINE_RE.finditer(block_text):
                return_type_raw, name_template, paramlist_text = decl_match.groups()
                return_type = return_type_raw.strip()
                raw_params = _parse_param_list(paramlist_text, name_template, file_flags)

                function_names = _emit_for_declaration(
                    name_template, raw_params, after_block, tables,
                    entry_key_prefix=os.path.basename(path), deprecated=deprecated, flags_out=file_flags,
                )

                # A TYPENAME-generic declaration writes its return type as the
                # bare token "TYPE" (e.g. "TYPE shmem_TYPENAME_g(...)"), the
                # same way its parameters write "const TYPE *source". Those
                # parameters already become "{CT}" via _param_with_type_sub,
                # which is what lets workflow/concretize/ resolve them per
                # type -- the return type was the one place that mapping was
                # never applied, so the literal string "TYPE" survived all the
                # way into 282 shipped entries' return.binding_type.c
                # (Concretize only knows "{T}"/"{CT}", so it had nothing to
                # substitute). Mapped here, at the same point and for the same
                # reason as the parameter case.
                #
                # classify_return_kind is deliberately still called with the
                # ORIGINAL token: its rule is written against the real C type
                # names, and "TYPE" and "{CT}" both fall through to the same
                # "value" branch anyway, so this keeps the classification
                # keyed on what the standard actually wrote.
                return_kind_input = return_type
                if return_type == "TYPE":
                    return_type = "{CT}"

                for real_name, params, type_family in function_names:
                    # .lower() would otherwise turn the "{T}"/"{CT}" placeholder
                    # tokens into "{t}"/"{ct}", inconsistent with both
                    # identity.name (which keeps real_name's original casing)
                    # and NVSHMEM's adapter (whose function_key is never
                    # lowercased at all) -- restore canonical casing afterward.
                    function_key = real_name.lower().replace("{t}", "{T}").replace("{ct}", "{CT}")
                    entry_key = f"shmem:{function_key}"
                    entry_flags = list(file_flags)

                    parameters = _build_parameters(params, arg_docs, entry_key, entry_flags)

                    if deprecated:
                        entry_flags.append(Flag(entry_key=entry_key, field="identity.deprecated_in", severity="note",
                                                 reason="wrapped in \\begin{DeprecateBlock} but no version string available"))

                    # since: workflow/extract/shmem/changelog.py parses the
                    # standard's own "Changes to this Document" chapter at
                    # content-file granularity; _since_for withholds that
                    # version from routines the standard marks deprecated,
                    # which is the one case where a file's routines provably
                    # do NOT share one history (see _since_for for the
                    # shmem_broadcast32 case that forced it). A routine
                    # matched by neither rule is inferred to predate the
                    # changelog's own coverage (which starts at Version 1.1)
                    # -- i.e. part of the original OpenSHMEM 1.0 baseline.
                    # All three outcomes stay `pattern`-confidence: each is a
                    # mechanical read or an explicit inference, never a
                    # literal per-function version marker, the same
                    # distinction MPI's field-provenance entry already draws.
                    since_version, since_note = _since_for(path, deprecated, since_map)
                    since = Confident(value=since_version, confidence="pattern", note=since_note)
                    if since_version is None:
                        entry_flags.append(Flag(
                            entry_key=entry_key, field="identity.since", severity="note",
                            reason=since_note,
                        ))

                    ir = {
                        "model": "shmem",
                        "function_key": function_key,
                        "name": real_name,
                        "type_family": list(type_family) if type_family else None,
                        "desc": Confident(value=desc, confidence="static", note="literal \\apisummary{} text, shared across all overloads/instantiations described in this file") if desc else None,
                        "since": since,
                        "deprecated_in": None,
                        "standard_refs": [],
                        "bindings": {
                            # Return type taken from the declaration, not
                            # hardcoded. It used to read `f"void {real_name}..."`,
                            # which shipped a WRONG C prototype for every
                            # OpenSHMEM routine that doesn't return void --
                            # 564 of them, including shmem_calloc ("void *"),
                            # shmem_addr_accessible ("int") and every typed
                            # atomic. The correct value was already parsed and
                            # sitting in `return_type` two lines up, used for
                            # return_binding_type; only the signature string
                            # ignored it. Found by the 2026-07-22 corpus audit.
                            "c": {"expressible": True, "header": "shmem.h",
                                  "signature": f"{return_type or 'void'} {real_name}({', '.join(_c_type_string(p['base_type'], p['pointer'], p['constant']) + ' ' + p['name'] for p in params)})"},
                            "fortran90": None, "fortran08": None, "lis": None, "cpp": None,
                        },
                        "parameters": parameters,
                        # OpenSHMEM's own convention (confirmed across every
                        # file read): void-returning routines are pure
                        # side-effecting operations; int-returning routines
                        # return zero on local success / nonzero on failure
                        # ("\apireturnvalues" prose), which is exactly the
                        # schema's ERROR_CODE meaning -- not a generic
                        # "value" the way an MPI handle-returning function is.
                        #
                        # That reasoning holds for int and void and for
                        # nothing else, which the original "anything but void
                        # -> ERROR_CODE" spelling of it did not respect: it
                        # also swept up the 23 TYPE-returning typed atomics,
                        # the 7 void*-returning allocators, and the size_t/
                        # uint64_t queries. See workflow/extract/return_kind.py
                        # for the corrected rule and its 2026-07-21 audit.
                        "return_kind": classify_return_kind(real_name, return_kind_input),
                        "return_binding_type": {"c": return_type or None},
                        "flags": entry_flags,
                    }
                    all_results.append((ir, entry_flags))

        # A file that declares functions and yields none is how the reduction
        # and scan families went missing for as long as they did:
        # _emit_for_declaration flags the skip on file_flags, but file_flags is
        # only ever attached to an entry, so a file that produces no entry
        # discards its own explanation. 238 routines were absent from the corpus
        # with nothing in any report saying so. Loud beats silent -- the
        # adapters that read C headers already raise rather than guess, and this
        # is the same call. Guarded on declarations_in_file because
        # shmem_ctx_session_config_t.tex is an \begin{apidefinition} file that
        # legitimately declares a type and no function.
        if declarations_in_file and len(all_results) == entries_before_file:
            skipped = [f.reason for f in file_flags if f.severity == "skipped"]
            raise ValueError(
                f"{os.path.basename(path)}: \\begin{{apidefinition}} file produced no entries"
                + ("; skipped: " + "; ".join(skipped) if skipped else ""))

    return all_results
