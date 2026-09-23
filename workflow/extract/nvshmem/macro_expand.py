"""
A minimal, general-enough C preprocessor macro expander for exactly the
patterns NVSHMEM's headers use to declare type-generic function families --
NOT a general preprocessor (no #if/#ifdef evaluation, no function-like macro
expansion outside the REPT/FN_TEMPLATE idiom below).

Confirmed directly by reading include/device_host/nvshmem_common.cuh and
include/host/{nvshmem_api,nvshmem_coll_api}.h: every type-generic
declaration follows one of three shapes:

  1. One-argument REPT macro:
     #define DECL_X(TYPENAME, TYPE) <one or more declarations using TYPENAME/TYPE>
     NVSHMEMI_REPT_FOR_STANDARD_RMA_TYPES(DECL_X)

  2. Two-argument REPT macro (reductions -- the op name is threaded through
     from the invocation site, not baked into the type table itself):
     #define NVSHMEMI_DECL_TEAM_REDUCE(NAME, TYPE, OP) <declaration using NAME/TYPE/OP>
     NVSHMEMI_REPT_FOR_BITWISE_REDUCE_TYPES(NVSHMEMI_DECL_TEAM_REDUCE, and)

  3. "OPGROUP" REPT macro (every atomic-memory-operation family). The
     invocation names the declaration template by an *abbreviation* that the
     REPT body token-pastes onto a fixed prefix, rather than passing the
     macro's own name:
     #define NVSHMEMI_REPT_OPGROUP_FOR_STANDARD_AMO(OPGRPNAME, opname) \
         NVSHMEMI_DECL_TYPE_##OPGRPNAME(int, int, opname) ...
     #define NVSHMEMI_DECL_TYPE_FINC(type, TYPE, opname) \
         NVSHMEMI_HOSTDEVICE_PREFIX TYPE nvshmem_##type##_atomic_##opname(TYPE *dest, int pe);
     NVSHMEMI_REPT_OPGROUP_FOR_STANDARD_AMO(FINC, fetch_inc)

All three resolve the same way: the REPT macro's own body is a fixed
sequence of calls to its first formal parameter -- either bare
(FN_TEMPLATE(typename, ctype[, ...]), shapes 1-2) or token-pasted onto a
prefix (PREFIX##OPGRPNAME(typename, ctype[, ...]), shape 3) -- so extract
those tuples and the prefix once, resolve the template macro's real name as
prefix + the invocation's first argument, then expand that macro's body once
per tuple, substituting its formal parameters (first two from the type
tuple, any remainder from the invocation's own extra arguments) and
resolving '##' token-pasting.

Two things this module learned the hard way (2026-09-12), both of which had
been silently dropping whole families:

  * **REPT macros nest.** A REPT body is not always a flat list of
    FN_TEMPLATE calls -- NVSHMEMI_REPT_FOR_STANDARD_REDUCE_TYPES opens with
    NVSHMEMI_REPT_FOR_BITWISE_REDUCE_TYPES(NVSHMEMI_FN_TEMPLATE, opname) and
    then lists ten more types itself, and NVSHMEMI_REPT_FOR_ARITH_REDUCE_TYPES
    consists of *nothing but* a nested call. Bodies are therefore flattened
    (nested REPT invocations inlined, with the nested macro's formals renamed
    to the enclosing invocation's arguments) before the tuples are read.
  * **A macro table is a point-in-time thing, not a whole-file thing.** These
    headers #define a declaration template, invoke it, #undef it, and reuse
    the same name for a different declaration a few lines later
    (NVSHMEMI_DECL_TYPE_PUT, NVSHMEMI_DECL_TEAM_REDUCE, ...). A single
    last-definition-wins table expands earlier invocations with a later
    body. The expansion pass therefore walks the file in order, applying
    each #define/#undef as it reaches it, on top of a seed table built from
    the other headers.

Preprocessor conditionals are still not evaluated. Only two #ifdef guards in
these headers wrap a macro *definition*, and both are handled by the
last-definition-wins seed behaviour landing on the #else branch, which is the
correct reading for both:
NVSHMEM_COMPLEX_SUPPORT (an opt-in build flag, off by default: no complex
reduction types) and __cplusplus around
NVSHMEMI_REPT_OPGROUP_FOR_EXTENDED_AMO_HALF (so `half` is absent from the
extended-AMO type families -- the C-visible declaration set). The second is a
real, deliberate narrowing; see
docs/cross-ppm-analysis/known-gaps-and-open-questions.md.
"""

import re

_DEFINE_LINE_RE = re.compile(r"^#define\s+(\w+)\s*\(([^)]*)\)\s*(.*)$")
_UNDEF_LINE_RE = re.compile(r"^#undef\s+(\w+)\b")
# Closed vocabulary on purpose (this project's "enumerable over general
# matching" convention): the two REPT families that actually exist in these
# headers, not any NVSHMEMI_* name that happens to look repetitive.
_INVOCATION_RE = re.compile(r"\b(NVSHMEMI_REPT_(?:OPGROUP_)?FOR_\w+)\s*\(([^)]*)\)")


def _join_continuations(text):
    """Collapse backslash-newline line continuations into single logical
    lines, so every #define and every invocation becomes regex-matchable
    on one line regardless of how it's wrapped in the source."""
    return re.sub(r"\\\r?\n\s*", " ", text)


def _split_args(args_raw):
    return [a.strip() for a in args_raw.split(",")] if args_raw.strip() else []


def _parse_defines(text):
    """-> {macro_name: (params_list, body_text)} for every #define in text."""
    defines = {}
    for line in text.split("\n"):
        m = _DEFINE_LINE_RE.match(line.strip())
        if m:
            name, params_raw, body = m.groups()
            defines[name] = ([p.strip() for p in params_raw.split(",") if p.strip()], body.strip())
    return defines


def _rename_formals(body, renames):
    """Substitute a nested macro's formal parameter names for the arguments
    the enclosing body passes it, in one simultaneous pass so a rename can't
    feed into a later one. Word-boundary only -- unlike _substitute this
    leaves '##' in place, because the result is another macro body that has
    not been instantiated yet."""
    if not renames:
        return body
    pattern = re.compile(
        r"\b(" + "|".join(re.escape(k) for k in sorted(renames, key=len, reverse=True)) + r")\b"
    )
    return pattern.sub(lambda m: renames[m.group(1)], body)


def _flatten_rept_body(rept_name, macro_table, _seen=frozenset()):
    """A REPT macro's body with every nested REPT invocation replaced by that
    macro's own (recursively flattened) body, its formals renamed to the
    arguments the nesting site passes. -> body text, or None if unknown."""
    entry = macro_table.get(rept_name)
    if entry is None:
        return None
    seen = _seen | {rept_name}

    def _inline(m):
        nested_name = m.group(1)
        nested = macro_table.get(nested_name)
        if nested is None or nested_name in seen:
            return m.group(0)
        nested_body = _flatten_rept_body(nested_name, macro_table, seen)
        if nested_body is None:
            return m.group(0)
        return _rename_formals(nested_body, dict(zip(nested[0], _split_args(m.group(2)))))

    return _INVOCATION_RE.sub(_inline, entry[1])


def _template_tuples(fn_formal, flat_rept_body):
    """A flattened REPT body is a sequence of calls to its own first formal
    parameter, either bare or token-pasted onto a fixed prefix. -> (prefix or
    "", [(typename, ctype), ...]).

    Only the first two arguments of each call are kept: any further
    positional args in the body are themselves formal-parameter names (e.g.
    'opname'), not real values, and real values for those come from the
    invocation site instead."""
    call_re = re.compile(r"(?:(\w+?)\s*##\s*)?\b" + re.escape(fn_formal) + r"\b\s*\(([^)]*)\)")
    prefix = ""
    tuples = []
    for m in call_re.finditer(flat_rept_body):
        if m.group(1):
            prefix = m.group(1)
        args = _split_args(m.group(2))
        if len(args) >= 2:
            tuples.append((args[0], args[1]))
    return prefix, tuples


def _substitute(body, subs):
    """Apply {formal_param: value} substitutions to a macro body, resolving
    '##' token-pasting (X##Y##Z with any operand substituted becomes the
    concatenation) as well as bare word-boundary occurrences."""
    result = body
    for param, value in subs.items():
        result = re.sub(r"##\s*" + re.escape(param) + r"\s*##", value, result)
        result = re.sub(r"##\s*" + re.escape(param) + r"\b", value, result)
        result = re.sub(r"\b" + re.escape(param) + r"\s*##", value, result)
    for param, value in subs.items():
        result = re.sub(r"\b" + re.escape(param) + r"\b", value, result)
    result = result.replace("##", "")
    return result


def build_macro_table(*header_texts):
    """Combine #define statements from one or more header texts (already
    read, not file paths) into one seed lookup table, after joining line
    continuations in each. Definition order within a single file is *not*
    honoured here -- expand_invocations[_grouped] re-applies the scanned
    file's own #define/#undef lines in order on top of this seed, which is
    what makes a redefined template name resolve correctly."""
    defines = {}
    for text in header_texts:
        defines.update(_parse_defines(_join_continuations(text)))
    return defines


def _iter_invocations(text, macro_table):
    """Walk text in source order, maintaining the macro table as each
    #define/#undef is reached, and yield one
    (template_params, template_body, tuples, extra_args) per resolvable
    NVSHMEMI_REPT_*(...) invocation site."""
    table = dict(macro_table)

    for line in _join_continuations(text).split("\n"):
        stripped = line.strip()

        define_m = _DEFINE_LINE_RE.match(stripped)
        if define_m:
            name, params_raw, body = define_m.groups()
            table[name] = ([p.strip() for p in params_raw.split(",") if p.strip()], body.strip())
            continue
        undef_m = _UNDEF_LINE_RE.match(stripped)
        if undef_m:
            table.pop(undef_m.group(1), None)
            continue
        if stripped.startswith("#"):
            continue

        for m in _INVOCATION_RE.finditer(stripped):
            rept_name = m.group(1)
            args = _split_args(m.group(2))
            rept_entry = table.get(rept_name)
            if not args or rept_entry is None or not rept_entry[0]:
                continue

            flat_body = _flatten_rept_body(rept_name, table)
            if flat_body is None:
                continue
            prefix, tuples = _template_tuples(rept_entry[0][0], flat_body)
            if not tuples:
                continue

            template_entry = table.get(prefix + args[0])
            if template_entry is None:
                continue
            template_params, template_body = template_entry
            yield template_params, template_body, tuples, args[1:]


def _subs_for(template_params, extra_args, typename_value, ctype_value):
    subs = {}
    if len(template_params) > 0:
        subs[template_params[0]] = typename_value
    if len(template_params) > 1:
        subs[template_params[1]] = ctype_value
    for i, extra in enumerate(extra_args):
        if len(template_params) > 2 + i:
            subs[template_params[2 + i]] = extra
    return subs


def expand_invocations(text, macro_table):
    """-> one expanded declaration-body string per (invocation, type-tuple)
    pair, with the type axis flattened into concrete values."""
    results = []
    for template_params, template_body, tuples, extra_args in _iter_invocations(text, macro_table):
        for typename, ctype in tuples:
            results.append(_substitute(template_body, _subs_for(template_params, extra_args, typename, ctype)))
    return results


def expand_invocations_grouped(text, macro_table):
    """Like expand_invocations, but collapses the type axis instead of
    flattening it -- yields one GENERIC record per invocation (an invocation
    line is already exactly one operation; see this module's docstring and
    the reduce-family example there) instead of one concrete string per
    type tuple:

        {"template": <declaration text with the type axis replaced by the
                       literal placeholder tokens '{T}' (typename positions,
                       e.g. the NAME half of nvshmem_##NAME##_put) and '{CT}'
                       (ctype positions, e.g. a parameter declared as
                       'TYPE *dest') -- kept distinct because typename and
                       ctype are sometimes different strings for the same
                       logical type (NVSHMEM's ("longlong", "long long"),
                       ("bfloat16", "__nv_bfloat16")). The op axis (this
                       invocation's own extra_args, e.g. 'sum'/'max'/'and')
                       is NOT part of the type axis and is substituted with
                       its real, concrete value immediately, exactly as
                       expand_invocations already does -- this is what keeps
                       every distinct operation a separate record, per
                       docs/schema/schema-overview.md's "type axis collapses,
                       operation axis never does" rule>,
         "type_family": [typename, ...],       # canonical typenames, for identity.type_family
         "ctype_map": {typename: ctype, ...}}  # for Concretize's later {CT} substitution

    Records are keyed by the declaration text they produce, so two
    invocations that expand to byte-identical declarations are merged into
    one record whose type_family is the union (first-seen order, deduplicated).
    This completes the *type* axis; it never collapses the operation axis,
    because the operation name is already substituted concretely above, so two
    different operations can never produce identical text. It is load-bearing
    for the atomics: one AMO family is declared by two or three separate
    invocations, one per type table -- e.g. nvshmem_{T}_atomic_fetch comes from
    NVSHMEMI_REPT_OPGROUP_FOR_{BITWISE,STANDARD,EXTENDED}_AMO(FETCH, fetch),
    7 + 5 + 2 types -- and without the merge the first invocation's table would
    silently stand in for the whole family.

    Whoever consumes this is expected to later substitute '{T}'/'{CT}' back
    to a chosen concrete (typename, ctype) pair exactly once, at Concretize
    time (see workflow/concretize/) -- never here, and never per-type in
    Extract.
    """
    merged = {}
    for template_params, template_body, tuples, extra_args in _iter_invocations(text, macro_table):
        template = _substitute(template_body, _subs_for(template_params, extra_args, "{T}", "{CT}"))
        record = merged.setdefault(template, {"template": template, "type_family": [], "ctype_map": {}})
        for typename, ctype in tuples:
            if typename not in record["ctype_map"]:
                record["type_family"].append(typename)
            elif record["ctype_map"][typename] != ctype:
                raise ValueError(
                    f"conflicting C type for typename {typename!r} in {template!r}: "
                    f"{record['ctype_map'][typename]!r} vs {ctype!r}"
                )
            record["ctype_map"][typename] = ctype
    return list(merged.values())
