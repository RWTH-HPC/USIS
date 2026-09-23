"""
MPI adapter: external-inputs/mpi/tex/mpi-standard/apis.json -> list of IR dicts.

apis.json (571 entries, keyed by lowercase function name) is the real MPI
Forum binding-tool's own output -- generated from \\begin{mpi-binding}
DSL blocks embedded directly in the .tex chapter files (confirmed by direct
inspection: external-inputs/mpi/tex/mpi-standard/chap-coll/coll.tex around the
Broadcast section has the literal function_name(...)/parameter(...) DSL
that compiles into apis.json["mpi_bcast"]). Treated here as already-
mechanical -- this adapter does not re-parse the tex DSL blocks, only
prose.py's narrow prose scan for the two fields apis.json doesn't carry.

Confirmed gaps in apis.json itself (not present anywhere in its 571
entries, checked directly): no identity.desc one-liner, no identity.since/
deprecated_in version string (attributes.deprecated is a bool, not a
version), no bindings.c signature string, no cpp_expressible attribute at
all (bindings.cpp is a fixed null for every MPI entry -- MPI-3.0+ removed
the C++ bindings).
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ir import Confident  # noqa: E402
from status import Flag  # noqa: E402
import signature  # noqa: E402
import prose  # noqa: E402
_LAYOUT_COMMON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "common")
sys.path.insert(0, _LAYOUT_COMMON)
from layout import EXTERNAL_INPUTS_DIR  # noqa: E402

_APIS_JSON_PATH = os.path.join(
    EXTERNAL_INPUTS_DIR, "mpi", "tex", "mpi-standard", "apis.json",
)

# apis.json's own array_type vocabulary observed directly (grep across all
# 571 entries): "" (no array) and "hidden" (length not represented as a
# separate parameter). Only "" maps cleanly onto the schema's closed
# fixed/variable/2d enum; "hidden" doesn't correspond to any of the three
# and is left null + flagged rather than force-fit -- an honest gap, not
# a resolved mapping.
_ARRAY_TYPE_MAP = {"": None}

# apis.json's parameters[].desc is prose lifted verbatim out of the .tex
# source, so it still carries that source's own typesetting macros. This
# strips them, exactly as the OpenSHMEM adapter's _strip_macros already does
# for its own \ac{}/\FUNC{} family -- MPI's descs were simply never given the
# same treatment (audited 2026-07-21: 533 macro occurrences across 210
# distinct desc strings, e.g. "communicator of \MPI/ processes to abort" and
# "new error code to be associated with \mpiarg{errorclass}").
#
# The table is closed and exhaustive against the real input, not a general
# LaTeX parser: these 9 macros are every macro that occurs in any desc in
# apis.json (enumerated directly). A macro outside the table is left intact
# rather than silently dropped, so a future apis.json that introduces one
# shows up as visible leakage instead of quietly losing its argument.
_DESC_MACRO_PATTERNS = [
    # Slash-terminated "abbreviation" macros: \MPI/ typesets as "MPI".
    (re.compile(r"\\MPI/"), "MPI"),
    (re.compile(r"\\mpi/"), "MPI"),
    (re.compile(r"\\RMA/"), "RMA"),
    # LaTeX's non-breaking space, used mid-sentence in two descs.
    (re.compile(r"~"), " "),
]

# Argument-taking font/reference macros: the argument IS the text. Applied to
# a fixpoint rather than once, because \mbox nests one of the others
# (mpi_dist_graph_create's "not~(\mbox{\mpicode{false}})") and the innermost
# match has to resolve before the outer one can see a brace-free argument.
_DESC_ARG_MACRO_RE = re.compile(r"\\(?:mpiarg|mpicode|mpiconst|mpifunc|code|mbox)\{([^{}]*)\}")


def _strip_desc_macros(text):
    if not text:
        return text
    for pattern, repl in _DESC_MACRO_PATTERNS:
        text = pattern.sub(repl, text)
    while True:
        stripped = _DESC_ARG_MACRO_RE.sub(r"\1", text)
        if stripped == text:
            break
        text = stripped
    return re.sub(r"\s+", " ", text).strip()

# apis.json's own `return_kind` is NOT the schema's 5-value return.kind enum
# -- it's the same MPI-Forum type-kind vocabulary used for parameters[].kind
# (confirmed: every value observed, e.g. "F90_COMM", "DISPLACEMENT",
# "WALL_TIME", "NOTHING", resolves through BASE_C_KIND_MAP to a real C type
# like MPI_Fint/MPI_Aint/double/void). Two closed, small translation tables
# below: one for the schema's structural kind, one for the actual C return
# type (reusing BASE_C_KIND_MAP via signature.c_base_type, not hardcoding
# "int" for every entry -- MPI_Wtime genuinely returns double).
_ERROR_CODE_LIKE = {"ERROR_CODE"}
_VOID_LIKE = {"NOTHING"}


def _schema_return_kind(apis_return_kind):
    if apis_return_kind in _ERROR_CODE_LIKE:
        return "ERROR_CODE"
    if apis_return_kind in _VOID_LIKE:
        return "void"
    return "value"


def _lang_included(parameter, attributes=None):
    """Which language bindings this parameter actually appears in.

    `attributes` is the function-level attributes dict. Passing it matters:
    apis.json records expressibility at BOTH levels, and the per-parameter
    `suppress` list alone answers a different question ("is this parameter
    dropped from an otherwise-existing binding?") than the function-level
    *_expressible flags do ("does that binding exist at all?"). Reading only
    the first produced 1147 parameters claiming a Fortran-2008 binding on 112
    entries whose own bindings.fortran08.expressible said false -- the
    deprecated MPI-1 attribute routines (mpi_attr_delete/get/put,
    mpi_keyval_*), which MPI-3 deliberately left out of the F08 bindings, plus
    the two C-inexpressible Fortran-only routines (mpi_f_sync_reg,
    mpi_sizeof). The entry contradicted itself: the section said the binding
    does not exist, every parameter in it said otherwise. Found 2026-07-21 by
    cross-checking parameter_bindings against the section flags.

    Optional (defaulting to the old behaviour) only so the function stays
    callable without an attributes dict; every caller in this adapter passes
    one.
    """
    suppress = set((parameter.get("suppress") or "").split())
    attributes = attributes or {}
    kind = parameter["kind"]
    optional = bool(parameter.get("optional"))
    large_only = bool(parameter.get("large_only"))
    is_poly = kind.startswith("POLY")

    c_excluded = "c_parameter" in suppress
    f90_excluded = "f90_parameter" in suppress
    f08_excluded = "f08_parameter" in suppress
    lis_excluded = "lis_parameter" in suppress

    # A binding the function itself has no expression in cannot include any
    # of its parameters, whatever `suppress` says about them individually.
    c_ok = attributes.get("c_expressible", True)
    f90_ok = attributes.get("f90_expressible", True)
    f08_ok = attributes.get("f08_expressible", True)
    lis_ok = attributes.get("lis_expressible", True)

    c = c_ok and (not c_excluded) and not (is_poly and large_only)
    c_large = c_ok and is_poly and not c_excluded
    f90 = f90_ok and not f90_excluded
    f08 = f08_ok and not f08_excluded
    lis = lis_ok and (not lis_excluded) and not (is_poly and large_only)
    lis_large = lis_ok and is_poly and not lis_excluded

    return {
        "c": c,
        "c_large": c_large,
        "fortran90": f90,
        "fortran90_optional": f90 and optional,
        "fortran08": f08,
        "fortran08_optional": f08 and optional,
        "lis": lis,
        "lis_large": lis_large,
        "cpp": False,
    }


def _build_parameter(parameter, entry_key, flags, attributes=None):
    array_type_raw = parameter.get("array_type") or ""
    if array_type_raw not in _ARRAY_TYPE_MAP:
        flags.append(Flag(
            entry_key=entry_key, field=f"parameters[{parameter['name']}].array_type",
            severity="note",
            reason=f"apis.json array_type {array_type_raw!r} has no clean mapping onto the schema's fixed/variable/2d enum",
        ))
    array_type = _ARRAY_TYPE_MAP.get(array_type_raw)

    lang_included = _lang_included(parameter, attributes)

    c_type = signature.c_param_string(parameter)
    if c_type is None:
        flags.append(Flag(
            entry_key=entry_key, field=f"parameters[{parameter['name']}].binding_type.c",
            severity="note",
            reason="function-pointer kind with no func_type given -- C type not resolvable",
        ))

    def _lang_type(included, builder, field_suffix):
        if not included:
            return None
        value = builder(parameter)
        if value is None:
            flags.append(Flag(
                entry_key=entry_key, field=f"parameters[{parameter['name']}].binding_type.{field_suffix}",
                severity="note",
                reason="parameter kind has no fixed type in this language (e.g. a C-only interop handle or VARARGS)",
            ))
        return value

    f90_type = _lang_type(lang_included["fortran90"], signature.fortran90_param_string, "fortran90")
    f08_type = _lang_type(lang_included["fortran08"], signature.fortran08_param_string, "fortran08")
    lis_type = _lang_type(lang_included["lis"], signature.lis_param_string, "lis")

    # apis.json has `constant` as a literal Python bool for every parameter
    # observed except 2 (mpi_pready_list/array_of_partitions,
    # mpi_psend_init/buf -- MPI-4.0 partitioned communication, already
    # logged as this project's most significant schema gap, see
    # docs/cross-ppm-analysis/known-gaps-and-open-questions.md), where it's
    # the string "true" instead. Coerced rather than left to fail schema
    # validation on 2 real, named entries.
    constant_raw = parameter.get("constant")
    constant = constant_raw if isinstance(constant_raw, bool) else (
        constant_raw.lower() == "true" if isinstance(constant_raw, str) else constant_raw
    )
    if isinstance(constant_raw, str):
        flags.append(Flag(
            entry_key=entry_key, field=f"parameters[{parameter['name']}].constant", severity="note",
            reason=f"apis.json gave string {constant_raw!r} instead of a boolean; coerced",
        ))

    # length is int|str|null in the schema, but apis.json uses a 2-element
    # list (e.g. ['n', '3']) for the 2D-array case (bindingc.py's own
    # _emit_array_attribute treats this the same way: "[][{len}]"). The
    # element is the inner row (MPI_Group_range_incl's ranges: "a
    # one-dimensional array of integer triplets"), so length is the outer
    # dimension -- a sibling parameter, as the length convention expects --
    # and the inner one stays in binding_type.c ("int ranges[][3]").
    length_raw = parameter.get("length")
    if isinstance(length_raw, list):
        length = length_raw[0]
        flags.append(Flag(
            entry_key=entry_key, field=f"parameters[{parameter['name']}].length", severity="note",
            reason=f"apis.json gave a 2D length {length_raw!r}; length is the outer dimension {length!r}, "
                   f"the inner one is in binding_type.c",
        ))
    elif length_raw == "":
        # apis.json's two empty lengths (MPI_Comm_spawn[_multiple]'s
        # array_of_errcodes) mean what its "*" means -- the binding tool emits
        # [] for both -- so they take the one spelling the schema defines.
        length = "*"
        flags.append(Flag(
            entry_key=entry_key, field=f"parameters[{parameter['name']}].length", severity="note",
            reason="apis.json gave an empty length for an array; written as '*', the binding tool's own "
                   "marker for an array no single parameter counts",
        ))
    else:
        length = length_raw

    return {
        "name": parameter["name"],
        "direction": parameter.get("param_direction"),
        "desc": _strip_desc_macros(parameter.get("desc")) or None,
        "binding_type": {"c": c_type, "fortran90": f90_type, "fortran08": f08_type, "lis": lis_type, "cpp": None},
        "asynchronous": parameter.get("asynchronous"),
        "constant": constant,
        "pointer": parameter.get("pointer"),
        "array_type": array_type,
        "func_type": parameter.get("func_type") or None,
        "length": length,
        "root_only": parameter.get("root_only"),
        "_lang_included": lang_included,
    }


def _build_bindings(attrs, name, name_f90, c_sig, flags, entry_key):
    c = {
        "expressible": bool(attrs.get("c_expressible")),
        "header": "mpi.h",
        "signature": c_sig,
    }
    # The "name(...)" placeholder is for the case it was written for -- a C
    # binding that DOES exist but whose parameter types couldn't all be
    # resolved. A function with no C binding at all is a different case, and
    # giving it a placeholder signature would restate the contradiction this
    # section's own `expressible: false` is there to record. Null instead.
    if c_sig is None and not c["expressible"]:
        c["signature"] = None
    elif c_sig is None:
        c["signature"] = f"{name}(...)"
        flags.append(Flag(
            entry_key=entry_key, field="bindings.c.signature", severity="low_confidence",
            reason="one or more parameter types unresolved; signature is a placeholder, not a real reconstruction",
        ))

    fortran90 = None
    if attrs.get("f90_expressible") is not None:
        raw_index_overload = attrs.get("f90_index_overload")
        index_overload = raw_index_overload
        if isinstance(raw_index_overload, str):
            # 4 real entries (mpi_alloc_mem, mpi_win_allocate, ...) carry a
            # full Fortran INTERFACE block here instead of a boolean -- the
            # schema's binding_fortran90.index_overload is boolean|null, so
            # the raw text can't be stored; presence is coerced to True
            # (there IS an overload) and the actual text is dropped, flagged
            # rather than silently discarded.
            index_overload = True
            flags.append(Flag(
                entry_key=entry_key, field="bindings.fortran90.index_overload", severity="note",
                reason="apis.json carries a full Fortran INTERFACE block here, not a boolean; coerced to true (overload exists), original text dropped",
            ))
        fortran90 = {
            # Upper-cased when apis.json has no explicit name_f90 (2026-07-22).
            # It used to fall back to `name` unchanged, which put the C
            # spelling "MPI_Send" into a field whose own schema description
            # gives "MPI_COMM_RANK" as its example -- 553 of 571 entries
            # disagreed with the field's documented convention.
            #
            # Fortran is case-insensitive, so this is not a distinct symbol
            # and the old value was never *wrong* to a compiler; it was wrong
            # to a reader and to the schema. Every source that expresses an
            # opinion uses all-caps: the standard's own Fortran examples
            # ("CALL MPI_SEND(a(1), 10, MPI_REAL, ...)"), and apis.json's own
            # name_f90 wherever it supplies one (COMM_COPY_ATTR_FUNCTION,
            # GREQUEST_FREE_FUNCTION -- the 18 callback typedefs, which also
            # drop the MPI_ prefix and so cannot be derived from `name` at
            # all; those keep coming from apis.json verbatim).
            "name": name_f90 or name.upper(),
            "expressible": bool(attrs.get("f90_expressible")),
            "use_colons": bool(attrs.get("f90_use_colons")),
            "index_overload": index_overload,
            "not_with_mpif": bool(attrs.get("not_with_mpif")),
        }

    fortran08 = None
    if attrs.get("f08_expressible") is not None:
        fortran08 = {
            "name": name,
            "expressible": bool(attrs.get("f08_expressible")),
            "abstract_interface": bool(attrs.get("f08_abstract_interface")),
            "module": "mpi_f08",
        }

    lis = None
    if attrs.get("lis_expressible") is not None:
        lis = {"expressible": bool(attrs.get("lis_expressible"))}

    return {
        "c": c,
        "fortran90": fortran90,
        "fortran08": fortran08,
        "lis": lis,
        "cpp": None,  # confirmed: no cpp_expressible attribute anywhere in apis.json's 571 entries
    }


def extract_mpi(apis_json_path=None, prose_index=None):
    """-> list[(ir_dict, list[Flag])]. One tuple per apis.json entry."""
    path = apis_json_path or _APIS_JSON_PATH
    with open(path) as f:
        apis = json.load(f)

    if prose_index is None:
        prose_index = prose.build_prose_index()

    results = []
    for function_key, e in apis.items():
        flags = []
        entry_key = f"mpi:{function_key}"
        name = e["name"]
        attrs = e.get("attributes", {})

        parameters = [_build_parameter(p, entry_key, flags, e.get("attributes")) for p in e.get("parameters", [])]

        apis_return_kind = e.get("return_kind")
        return_kind = _schema_return_kind(apis_return_kind)
        c_ret_type = signature.c_base_type(apis_return_kind)
        if c_ret_type is None:
            c_ret_type = "int"
            flags.append(Flag(
                entry_key=entry_key, field="return.binding_type.c", severity="note",
                reason=f"apis.json return_kind {apis_return_kind!r} has no entry in BASE_C_KIND_MAP",
            ))
        c_params = [p for p in e.get("parameters", []) if _lang_included(p, e.get("attributes"))["c"]]
        # A function with no C binding has no C signature to state. Without
        # this, the two Fortran-only routines (mpi_sizeof, mpi_f_sync_reg)
        # rendered as "int MPI_Sizeof()" -- a syntactically valid, completely
        # fictional C declaration with an empty parameter list, because every
        # one of their parameters had just been correctly excluded from the C
        # binding. Null is the honest answer and matches how bindings.cpp is
        # already handled for every MPI entry.
        c_sig = (signature.c_signature(name, c_params, c_ret_type)
                 if attrs.get("c_expressible", True) else None)

        bindings = _build_bindings(attrs, name, e.get("name_f90"), c_sig, flags, entry_key)

        prose_entry = prose_index.get(function_key, {})
        standard_refs = prose_entry.get("standard_refs") or []
        if standard_refs:
            flags.append(Flag(
                entry_key=entry_key, field="identity.standard_refs", severity="low_confidence",
                reason="chapter + top-level section title, mechanically read from the tex (not officially numbered, and the vendored standard is a working draft, not a ratified version)",
            ))
        # identity.desc is never attempted here (retired 2026-07-20, see
        # prose.py's module docstring): MPI's own semantics routinely span
        # multiple sentences, so a "first sentence following the binding
        # block" heuristic is a structural mismatch, not just an occasional
        # miss. Always null from Extract; filled only via a human-reviewed
        # curated/supplement/supplement-mpi.json entry -- see
        # curated/README.md.
        desc = None
        flags.append(Flag(
            entry_key=entry_key, field="identity.desc", severity="note",
            reason="not attempted mechanically -- MPI's tex has no dedicated one-line description field, and its prose descriptions routinely span multiple sentences; see curated/supplement/supplement-mpi.json",
        ))

        if attrs.get("deprecated"):
            flags.append(Flag(
                entry_key=entry_key, field="identity.deprecated_in", severity="note",
                reason="apis.json marks this deprecated (attributes.deprecated=true) but gives no version string; no machine-readable changelog source found",
            ))

        # A callback prototype (attributes.callback) or a predefined callback
        # constant (attributes.predefined_function names the prototype it
        # instantiates, e.g. MPI_DUP_FN -> MPI_Copy_function) is part of the
        # MPI API surface but is not a routine anyone CALLS -- so no PMPI_
        # shadow symbol exists for it. derive_profiling_name's blanket
        # "P" + name was inventing 34 symbols that are not in any MPI library
        # (PMPI_User_function, PMPI_DUP_FN, ...) -- found 2026-07-21 in the
        # full-corpus audit. Both attributes are literal, machine-readable
        # source facts, so this needs no naming heuristic.
        is_callback = bool(attrs.get("callback"))
        is_predefined = attrs.get("predefined_function") is not None
        if is_callback:
            flags.append(Flag(
                entry_key=entry_key, field=None, severity="note",
                reason="attributes.callback=true -- this is a function-pointer typedef family, not a directly-callable MPI routine; emitted as a regular entry, flagged for human confirmation it belongs in the same corpus",
            ))
        if is_predefined:
            flags.append(Flag(
                entry_key=entry_key, field=None, severity="note",
                reason=(f"attributes.predefined_function={attrs['predefined_function']!r} -- this is a "
                        "predefined callback CONSTANT (an instance of that prototype), not a callable "
                        "routine; same corpus-membership question as the callback prototypes above"),
            ))
        if is_callback or is_predefined:
            flags.append(Flag(
                entry_key=entry_key, field="tool_integration.profiling_name", severity="note",
                reason="no PMPI_ shadow symbol exists for a callback prototype/constant -- profiling_name suppressed rather than derived",
            ))

        ir = {
            "model": "mpi",
            "function_key": function_key,
            "name": name,
            "desc": desc,
            "since": None,       # confirmed gap: no mechanical source found, see prose.py docstring
            "deprecated_in": None,
            "standard_refs": standard_refs,
            "bindings": bindings,
            "parameters": parameters,
            "return_kind": return_kind,
            "return_binding_type": {"c": c_ret_type},
            "no_profiling_symbol": is_callback or is_predefined,
            "flags": flags,
        }
        results.append((ir, flags))

    return results
