"""
Reconstructs bindings.c.signature and parameters[].binding_type.c from
apis.json's per-parameter kind/constant/pointer/length fields.

Reuses SMALL_C_KIND_MAP directly from the real MPI Forum binding-tool
(external-inputs/mpi/tex/mpi-standard/binding-tool/bindingtypes.py) by importing it
-- not by hand-transcribing its ~190 entries, which would be exactly the
kind of "plausible-sounding invented value" this project's philosophy
rejects. Every parameter kind value that appears anywhere in apis.json is
confirmed present in that map (checked directly: 149 distinct kinds used,
0 missing from SMALL_C_KIND_MAP).

Deliberately SMALL_C_KIND_MAP, not the tool's own BASE_C_KIND_MAP: BASE
leaves every POLY-prefixed kind (e.g. POLYXFER_NUM_ELEM_NNI, MPI-4.0's
large-count-polymorphic parameters) mapped to None on purpose -- the real
tool resolves those per-variant via SMALL_C_KIND_MAP (int) or
BIG_C_KIND_MAP (MPI_Count) depending on which binding is being emitted.
Since bindings.c.signature is a single field representing the default/small
variant (the large-count variant's existence is separately recorded via
parameters[].parameter_bindings including "c_large"), SMALL_C_KIND_MAP is
the correct table for it -- confirmed by reading binding_emitter.py's own
LANGUAGE_MODULES_POLY table, which pairs exactly this postfix-less/SMALL,
"_c"-postfixed/BIG split.

The const/pointer/array-suffix assembly logic below is a simplified,
independent reimplementation of bindingc.py's _emit_c_param family (not an
import of those private functions, which are written against a different,
richer LaTeX-parseset input shape than apis.json's already-serialized
dicts) -- covers exactly the cases actually observed in apis.json (pointer
explicitly True/False/null, length null/non-null/list, the fixed pointer-
kind set bindingc.py itself enumerates), ported by direct reading of that
module's source, not guessed.

The `bindings.fortran90`/`bindings.fortran08`/`bindings.lis` *sections*
(see curated/schemas/api-schema.json's own $defs) carry no whole-function `signature`
field -- those are populated directly from apis.json's `attributes` by the
adapter. `parameters[].binding_type.{fortran90,fortran08,lis}`, however, is a
genuinely separate, per-parameter field, and -- like `.c` -- is mechanically
derivable from apis.json: fortran90_param_string/fortran08_param_string/
lis_param_string below are simplified, independent reimplementations of
bindingf90.py's/bindingf08.py's/bindinglis.py's own per-parameter descriptor
logic (_construct_parameter / find_parameter_ordering / _emit_parameter_lis_type),
ported by direct reading of those modules' source, the same way c_param_string
was ported from bindingc.py -- not a literal import of those private
functions (which emit whole-signature LaTeX macros grouping every parameter
that shares a type onto one line, a document-rendering concern this project
has no use for) and not guessed. Each function returns one parameter's own
type-plus-decoration fragment in that language, independent of how any real
LaTeX rendering would group it with sibling parameters.

Reuses SMALL_F90_KIND_MAP/SMALL_F08_KIND_MAP/LIS_KIND_MAP directly from the
same binding-tool module as SMALL_C_KIND_MAP, for the same reason and with
the same SMALL-vs-BASE reasoning (POLY-prefixed large-count kinds resolve
through the small/default variant here, exactly as for C).
"""

import os
import sys

_LAYOUT_COMMON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "common")
sys.path.insert(0, _LAYOUT_COMMON)
from layout import EXTERNAL_INPUTS_DIR  # noqa: E402

_BINDING_TOOL_DIR = os.path.join(
    EXTERNAL_INPUTS_DIR, "mpi", "tex", "mpi-standard", "binding-tool",
)
sys.path.insert(0, _BINDING_TOOL_DIR)
from bindingtypes import (  # noqa: E402
    SMALL_C_KIND_MAP,
    SMALL_F90_KIND_MAP,
    SMALL_F08_KIND_MAP,
    LIS_KIND_MAP,
)

_POINTER_KINDS = frozenset({
    "BUFFER", "C_BUFFER", "C_BUFFER2", "C_BUFFER3", "C_BUFFER4",
    "STRING", "EXTRA_STATE", "EXTRA_STATE2", "ATTRIBUTE_VAL",
    "STATUS", "ATTRIBUTE_VAL_10", "STRING_ARRAY",
    "FUNCTION", "FUNCTION_SMALL", "POLYFUNCTION",
    "TOOL_MPI_OBJ", "F08_STATUS", "F90_STATUS",
})


def c_base_type(kind, func_type=None):
    """The bare C type name for a parameter kind (no const/pointer/array
    decoration). Returns None if this kind has no fixed base type
    (FUNCTION/FUNCTION_SMALL/POLYFUNCTION -- every function-pointer type is
    genuinely different, per BASE_C_KIND_MAP's own comment -- the caller's
    own func_type value is the real answer for those).
    """
    if kind in ("FUNCTION", "FUNCTION_SMALL", "POLYFUNCTION"):
        return func_type or None
    return SMALL_C_KIND_MAP.get(kind)


def _pointer_suffix(parameter):
    """Ported from bindingc.py's _emit_pointer_attribute. Rule order matters
    and is kept identical to upstream's -- four rules were missing from the
    original port (audited 2026-07-21, 14 parameters across 8 functions came
    out with the wrong C declaration):

      - ARGUMENT_LIST's own two cases. MPI_Init's `argv` is `char ***argv`
        and MPI_Info_create_env's is `char *argv[]`; without them both
        rendered as a bare `char argv`.
      - `or parameter['pointer']` in the final rule. `pointer` was only ever
        read as a *negative* signal here ("pointer is False -> no star"),
        never as the positive one it also is, so every `pointer: true`
        parameter declared IN with no length lost its star -- MPI_Cancel's
        `MPI_Request *request`, the four `*_errhandler_function` callbacks'
        `MPI_Comm *comm`/`int *error_code`, MPI_User_function's `int *len`/
        `MPI_Datatype *datatype`, MPI_Abi_set_fortran_booleans' two
        `void *logical_*`.
      - MPI_Unpack_external's STRING-with-length-'*' case, which takes array
        notation rather than a star.
    """
    kind = parameter["kind"]
    pointer = parameter.get("pointer")
    length = parameter.get("length")
    direction = parameter.get("param_direction")

    if pointer is not None and not pointer and kind == "ARGUMENT_LIST":
        return "*"
    if pointer is not None and not pointer:
        return ""
    if kind == "STRING_2DARRAY":
        return "**"
    if kind == "ARGUMENT_LIST":
        return "***"
    if kind == "STRING" and length == "*" and not pointer:
        return ""
    if kind in _POINTER_KINDS:
        return "*"
    if (direction in ("inout", "out") or pointer) and length is None:
        return "*"
    return ""


def _array_suffix(parameter):
    """Ported from bindingc.py's _emit_array_attribute. Two rules were
    missing from the original port (audited 2026-07-21): C_BUFFER4's
    unconditional "" (MPI_User_function's `invec`/`inoutvec` carry a
    `length` of "len" that is a real element count, not an array bound, and
    were rendering as `void invec[]`), and MPI_Unpack_external's
    STRING-with-length-'*' case, which _pointer_suffix defers to here."""
    kind = parameter["kind"]
    length = parameter.get("length")
    pointer = parameter.get("pointer")

    if kind == "C_BUFFER4":
        return ""
    if kind != "STRING" and length is not None and not isinstance(length, list) and not pointer:
        return "[]"
    if kind == "STRING" and length == "*" and not pointer:
        return "[]"
    if kind in ("STRING_ARRAY", "STRING_2DARRAY"):
        return "[]"
    if isinstance(length, list) and len(length) > 1:
        return f"[][{length[1]}]"
    return ""


def c_param_string(parameter):
    """One parameter's full C declaration fragment, e.g. 'const void *buf'
    or 'int count'. Returns None (rather than a guessed placeholder) when
    the base type itself can't be determined (unresolved function-pointer
    kind with no func_type given)."""
    base = c_base_type(parameter["kind"], parameter.get("func_type"))
    if base is None:
        return None
    # SMALL_C_KIND_MAP is the *LaTeX* binding tool's table, so VARARGS comes
    # back as the typesetting macro "\ldots" -- which renders as "..." in the
    # standard's PDF but is not C. This field holds a real C declaration, and
    # C spells a variadic parameter "..." with no name at all, so the macro is
    # translated and the (document-only) placeholder name dropped. Affects
    # MPI_Pcontrol and the four *_errhandler_function callbacks (audited
    # 2026-07-21, previously emitted as a literal "\ldots varargs").
    if base == "\\ldots":
        return "..."
    const = "const " if parameter.get("constant") else ""
    pointer = _pointer_suffix(parameter)
    array = _array_suffix(parameter)
    name = parameter["name"]
    return f"{const}{base} {pointer}{name}{array}"


def c_signature(name, parameters, return_kind_c="int"):
    """Full 'RETTYPE Name(params...)' signature string, or None (with the
    caller expected to flag it) if any parameter's type couldn't be
    resolved."""
    parts = []
    for p in parameters:
        s = c_param_string(p)
        if s is None:
            return None
        parts.append(s)
    return f"{return_kind_c} {name}({', '.join(parts)})"


def _f90_name_suffix(parameter):
    """Ported from bindingf90.py's _construct_parameter: the array-dimension
    parenthetical attached to the *name* side of an F90 declaration (F90
    types themselves never carry dimension info the way C's `*`/`[]` does)."""
    suppress = parameter.get("suppress") or ""
    if "f90_parenthesis" in suppress or "f90_buf_paren" in suppress:
        return ""

    kind = parameter["kind"]
    length = parameter.get("length")
    dimensions = []

    if kind in ("BUFFER", "C_BUFFER2", "C_BUFFER3", "STRING_ARRAY"):
        dimensions.append("*")
    elif kind == "F90_STATUS":
        dimensions.append("MPI_STATUS_SIZE")
    elif kind == "STATUS":
        dimensions.append("MPI_STATUS_SIZE")
        if length is not None:
            dimensions.append(length)
    elif kind == "C_BUFFER4":
        dimensions.append(length.upper())
    elif kind == "STRING_2DARRAY":
        dimensions.append(length.upper())
        dimensions.append("*")
    elif kind != "STRING" and length is not None:
        if isinstance(length, list):
            dimensions.append(length[1])
        dimensions.append("*")

    return f"({', '.join(dimensions)})" if dimensions else ""


def fortran90_param_string(parameter):
    """One parameter's own F90 declaration fragment, e.g. 'INTEGER count' or
    '<type> buf(*)' -- '<type>' is the real MPI standard's own literal
    placeholder for BUFFER's choice-type (BASE_F90_KIND_MAP's own value),
    not a gap in this adapter. Returns None when the kind has no fixed F90
    type (mirrors c_base_type's FUNCTION*/POLYFUNCTION handling)."""
    kind = parameter["kind"]
    if kind in ("FUNCTION", "FUNCTION_SMALL", "POLYFUNCTION"):
        return "EXTERNAL"
    base = SMALL_F90_KIND_MAP.get(kind)
    if base is None:
        return None
    name = parameter["name"]
    suffix = _f90_name_suffix(parameter)
    return f"{base} {name}{suffix}"


def _f08_intent(parameter):
    """Ported from bindingf08.py's _emit_intent_attribute: several kinds
    deliberately omit INTENT because the argument may also legally be a
    sentinel constant (MPI_STATUS_IGNORE, MPI_BOTTOM) of a different
    intent than the parameter's own declared direction."""
    kind = parameter["kind"]
    direction = parameter.get("param_direction")
    suppress = parameter.get("suppress") or ""

    if "f08_intent" in suppress:
        return ""
    if kind == "STATUS" and direction == "out":
        return ""
    if kind == "BUFFER" and direction in ("out", "inout"):
        return ""
    if kind in ("FUNCTION", "POLYFUNCTION") and direction == "in":
        return ""
    if direction is None:
        return ""
    return f", INTENT({direction.upper()})"


def _f08_name_suffix(parameter):
    """Ported from bindingf08.py's _emit_name_length: the array-dimension
    parenthetical attached to the name side of an F08 declaration."""
    kind = parameter["kind"]
    length = parameter.get("length")
    array_type = parameter.get("array_type")

    if kind == "F90_STATUS":
        return "(MPI_STATUS_SIZE)"
    if kind == "STRING_ARRAY":
        return "(*)"
    if kind == "STRING_2DARRAY":
        return f"({length}, *)"
    if length is not None and array_type == "hidden":
        return "(*)"
    if kind != "STRING" and length is not None:
        if isinstance(length, list):
            return f"({', '.join(reversed(length))})"
        return f"({length if length else '*'})"
    return ""


def fortran08_param_string(parameter):
    """One parameter's own F08 declaration fragment, e.g.
    'TYPE(MPI_Datatype), INTENT(IN) :: datatype'. Returns None when the kind
    has no fixed F08 type."""
    kind = parameter["kind"]
    func_type = parameter.get("func_type")

    if kind in ("FUNCTION", "FUNCTION_SMALL", "POLYFUNCTION"):
        base = f"PROCEDURE({func_type})" if func_type else None
    else:
        base = SMALL_F08_KIND_MAP.get(kind)
    if base is None:
        return None

    length = parameter.get("length")
    if kind in ("STRING", "STRING_ARRAY"):
        base += f"(LEN={length})" if length else "(LEN=*)"
    elif kind == "STRING_2DARRAY":
        base += "(LEN=*)"

    if parameter.get("optional"):
        base += ", OPTIONAL"
    base += _f08_intent(parameter)
    if parameter.get("asynchronous"):
        base += ", ASYNCHRONOUS"

    name = parameter["name"] + _f08_name_suffix(parameter)
    return f"{base} :: {name}"


def lis_param_string(parameter):
    """One parameter's own language-independent type parenthetical, e.g.
    '(choice)' or '(array of integers)' -- ported from bindinglis.py's
    _emit_parameter_lis_type (the type-descriptor half only; the sentence-
    level description itself is already covered by parameters[].desc).
    Returns None when the kind has no LIS type at all."""
    kind = parameter["kind"]
    lis_kind = LIS_KIND_MAP.get(kind)
    if lis_kind is None:
        return None

    suppress = parameter.get("suppress") or ""
    root_only = bool(parameter.get("root_only"))
    if ("lis_paren" in suppress or "lis_kind" in suppress) and root_only:
        return "(significant only at root)"

    significant = ", significant only at root" if root_only else ""
    count = ", only present for large count variants" if parameter.get("large_only") else ""

    if kind in ("STRING", "STRING_2DARRAY"):
        return f"({lis_kind}{significant})"

    length = parameter.get("length")
    array = "array of " if length is not None else ""
    plural = ("" if kind == "STATUS" else "s") if array else ""
    return f"({array}{lis_kind}{plural}{significant}{count})"
