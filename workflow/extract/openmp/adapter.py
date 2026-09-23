"""
OpenMP adapter: the OpenMP ARB's own published interface definition
(external-inputs/openmp/standard/openmp-arb-6.0/) -> IR dicts.

Scope: the OpenMP *runtime library* routines (`omp_*`). The directive surface
(`#pragma omp ...`) is out of scope by construction -- see
docs/cross-ppm-analysis/known-gaps-and-open-questions.md's OpenMP row. The OMPT
and OMPD tool interfaces are separate headers (omp-tools.h, ompd-types.h),
vendored beside omp.h for reference but not read here.

Three inputs, each answering what the others cannot:

  - `standard/openmp-arb-6.0/include/omp.h` -- the C surface, and the authority
    on which routines exist: 122 of them. Unlike LLVM's generated omp.h (kept at
    implementation/llvm-20.1.7/ as the record of a shipping runtime, no longer
    read here), the ARB header **names every parameter**, so names are a literal
    read rather than a cross-reference into the specification's prose.
  - `standard/openmp-arb-6.0/fortran/omp_lib.f90` -- the Fortran half of the same
    interface definition. It supplies bindings.fortran08 and, more importantly,
    parameters[].direction: C states only const-or-not, Fortran must state INTENT.
    See workflow/extract/openmp/fortran_lib.py.
  - `docs/6.0/md/` and `docs/5.2/md/` -- the specification, sliced per routine by
    workflow/ingestion/openmp_spec_text.py. 6.0 gives identity.standard_refs
    (chapter and section) and the parameter names for the two routines the ARB
    header leaves unnamed; **5.2 gives identity.desc**, because 6.0 deleted the
    per-routine `Summary` block that 5.2 published. 6.0 replaced it with a
    multi-sentence `Effect` paragraph, and condensing prose into a one-line desc
    is the mechanism this project retired for MPI and NVSHMEM -- so the 30
    routines 6.0 adds carry `desc: null` rather than a condensation.

What no input states, and so stays null: identity.since and identity.deprecated_in
(no per-routine version marker in header or specification; the supplement carries
what is known), and bindings.fortran90 -- OpenMP's second Fortran form is the
`omp_lib.h` include file, but the schema's binding_fortran90 requires
`use_colons`, `index_overload` and `not_with_mpif`, three MPI-specific fields
with no OpenMP meaning. Logged as a gap rather than filled with invented values.

The header is read as a C translation unit: `__cplusplus` undefined (_MACROS),
which selects the C branch of the `omp_alloc` family whose C++ branch re-declares
the same six routines with default arguments.
"""

import glob
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ir import Confident  # noqa: E402
from status import Flag  # noqa: E402
import c_header  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fortran_lib  # noqa: E402

_LAYOUT_COMMON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "common")
sys.path.insert(0, _LAYOUT_COMMON)
from layout import EXTERNAL_INPUTS_DIR  # noqa: E402

_STANDARD_DIR = os.path.join(EXTERNAL_INPUTS_DIR, "openmp", "standard", "openmp-arb-6.0")
_HEADER_NAME = "omp.h"
_HEADER_PATH = os.path.join(_STANDARD_DIR, "include", _HEADER_NAME)
_FORTRAN_NAME = "omp_lib.f90"
_FORTRAN_PATH = os.path.join(_STANDARD_DIR, "fortran", _FORTRAN_NAME)
_FORTRAN_MODULE = "omp_lib"

# A C translation unit: every macro the header tests is undefined.
_MACROS = {}

# The header is scanned one ';'-terminated statement at a time rather than with a
# single declaration regex. Two shapes defeat the regex form: a declaration split
# over four lines (omp_init_mempartitioner), and one that omits `extern` outright
# (omp_get_uid_from_device, line 337) -- making `extern` optional in a regex lets
# the match start at the blank line above and swallow the keyword into the return
# type. Statements cannot straddle a ';', so neither is possible here.
_STATEMENT_RE = re.compile(r"[^;{}]*;")
_DECLARATION_RE = re.compile(r"^(.*?)\b(omp_\w+)\s*\((.*)\)$", re.S)
_EXTERN_RE = re.compile(r"\bextern\b")

_SPEC_DESC_DIR = os.path.join(EXTERNAL_INPUTS_DIR, "openmp", "docs", "5.2", "md")
_SPEC_DESC_VERSION = "OpenMP 5.2"
_SPEC_REF_DIR = os.path.join(EXTERNAL_INPUTS_DIR, "openmp", "docs", "6.0", "md")
_SPEC_REF_VERSION_LABEL = "OpenMP 6.0"
# identity.standard_refs mirrors MPI's shape: "<chapter> - <section> (<PPM>-<version>)".
_SPEC_REF_VERSION = "OpenMP-6.0"

_SPEC_SECTION_RE = re.compile(r"^# (\S+) (.*)$", re.MULTILINE)
_SPEC_SHARED_RE = re.compile(r"^<!-- section shared with: (.*) -->$", re.MULTILINE)
_SPEC_CHAPTER_RE = re.compile(r"^<!-- chapter: (.*) -->$", re.MULTILINE)
# 5.2's per-routine blocks; the Summary paragraph ends where the next one starts.
_SPEC_BLOCK_ENDS = ("Format", "Binding", "Constraints on Arguments", "Effect")

# return.kind. The C type settles void and pointers; `int` is overloaded the same
# way it is in OpenSHMEM (workflow/extract/return_kind.py), so the two families
# whose int is not a plain value are listed by name. Each was checked against its
# routine's own wording in the vendored specification.
#
#   status    -- omp_target_memcpy and its _rect/_async variants, and
#                omp_target_(dis)associate_ptr: "returns zero if successful";
#                omp_pause_resource: "zero in case of success, and non-zero
#                otherwise"; omp_pause_resource_all is defined as calling it per
#                device. omp_mempartition_set_part (6.0 section 27.6): "If the
#                specified size cannot be supported by the specified resource,
#                this routine returns negative one. Otherwise, it returns zero."
#   predicate -- "returns true if ...; otherwise, it returns false", or the value
#                of an enabled/disabled ICV. omp_ancestor_is_free_agent (6.0
#                section 21.12) is the literal first form; omp_is_free_agent
#                (21.11) "returns the value of the free-agent-var ICV, which
#                indicates whether ...", the same shape as omp_get_dynamic.
#
# omp_test_nest_lock is deliberately not a predicate: it returns the new nesting
# count. Every other scalar return (a thread count, a level, a device number, a
# time, a size, a handle) is a datum the call computed -- including
# omp_get_device_from_uid, which returns a device number or omp_invalid_device.
_STATUS_ROUTINES = frozenset({
    "omp_target_memcpy", "omp_target_memcpy_rect",
    "omp_target_memcpy_async", "omp_target_memcpy_rect_async",
    "omp_target_associate_ptr", "omp_target_disassociate_ptr",
    "omp_pause_resource", "omp_pause_resource_all",
    "omp_mempartition_set_part",
})
_PREDICATE_ROUTINES = frozenset({
    "omp_in_parallel", "omp_in_final", "omp_in_explicit_task", "omp_is_initial_device",
    "omp_get_dynamic", "omp_get_nested", "omp_get_cancellation",
    "omp_test_lock", "omp_target_is_present", "omp_target_is_accessible",
    "omp_is_free_agent", "omp_ancestor_is_free_agent",
})


def _return_kind(name, return_type):
    if return_type == "void":
        return "void"
    if "*" in return_type:
        return "RESULT"
    if name in _STATUS_ROUTINES:
        return "ERROR_CODE"
    if name in _PREDICATE_ROUTINES:
        return "bool"
    return "value"


def _spec_prototype(lines, name):
    """The routine's own C prototype from its Format (5.2) or Prototypes (6.0)
    block -> the parameter-list text, or None. pdftotext breaks a long prototype
    across lines, so the declaration is joined until its closing ');'."""
    start = re.compile(rf"^\s*(?:const\s+)?[A-Za-z_][\w\s\*]*?\b{re.escape(name)}\s*\(")
    for i, line in enumerate(lines):
        if not start.match(line):
            continue
        decl, j = line, i
        while ");" not in decl and j + 1 < len(lines) and len(decl) < 600:
            j += 1
            decl += " " + lines[j].strip()
        m = re.search(rf"\b{re.escape(name)}\s*\((.*?)\)\s*;", decl, re.DOTALL)
        if m:
            return " ".join(m.group(1).split())
    return None


def _spec_summary(lines):
    """5.2's 'Summary' paragraph. 6.0 publishes no such block."""
    if "Summary" not in lines:
        return None
    out = []
    for line in lines[lines.index("Summary") + 1:]:
        if line.strip() in _SPEC_BLOCK_ENDS:
            break
        out.append(line.strip())
    return " ".join(" ".join(out).split()) or None


def build_spec_index(spec_dir):
    """{routine: {"summary", "params", "section", "section_title", "chapter",
                  "shared_with"}} from one vendored specification's slices.

    An absent slice is not an error: a routine the vendored version does not
    define simply has no entry, which is how the two deprecated `*_nested`
    routines (dropped by 6.0, still declared) and the 30 routines 6.0 adds are
    each handled in the version that lacks them.
    """
    index = {}
    for path in sorted(glob.glob(os.path.join(spec_dir, "*.md"))):
        name = os.path.basename(path)[: -len(".md")]
        with open(path, encoding="utf-8") as f:
            text = f.read()
        lines = [line.rstrip() for line in text.split("\n")]
        params_text = _spec_prototype(lines, name)
        params = None
        if params_text is not None:
            params = []
            for fragment in params_text.split(","):
                try:
                    parsed = c_header.parse_c_param(fragment)
                except ValueError:
                    parsed = None
                if parsed is not None or fragment.strip() in ("", "void"):
                    if parsed is not None:
                        params.append(parsed["name"])
                else:
                    params.append(None)
        section = _SPEC_SECTION_RE.search(text)
        shared = _SPEC_SHARED_RE.search(text)
        chapter = _SPEC_CHAPTER_RE.search(text)
        index[name] = {
            "summary": _spec_summary(lines),
            "params": params,
            "section": section.group(1) if section else None,
            "section_title": section.group(2) if section else None,
            "chapter": chapter.group(1) if chapter else None,
            "shared_with": [s.strip() for s in shared.group(1).split(",")] if shared else [],
        }
    return index


def _direction_for(param, position, name, entry_key, fortran, flags):
    """The ARB's Fortran INTENT where it states one, the documented reason where
    a released handle needs one, and the const/pointer heuristic otherwise."""
    stated, evidence = fortran_lib.direction_for(fortran, position)
    if stated is not None:
        return stated
    released = c_header.released_direction("openmp", name, param["name"])
    if released is not None:
        flags.append(Flag(
            entry_key=entry_key, field=f"parameters[{param['name']}].direction", severity="note",
            reason=f"'in', not the 'out' that const/pointer-ness alone implies: this parameter names "
                   f"memory the call releases -- {released}",
        ))
        return "in"
    direction = "in" if not param["pointer"] else ("in" if param["constant"] else "out")
    reason = ("inferred from const-qualification/pointer-ness alone; cannot distinguish 'out' from "
              "'inout' for a non-const pointer")
    if fortran is None:
        reason += f" -- {_FORTRAN_NAME} declares no interface for this routine"
    else:
        reason += f" -- {_FORTRAN_NAME}'s interface states no INTENT for this argument"
    flags.append(Flag(
        entry_key=entry_key, field=f"parameters[{param['name']}].direction",
        severity="low_confidence", reason=reason,
    ))
    return direction


def _declarations(code):
    """-> [(return_type_text, name, parameter_list_text, offset)] over the active
    C view of the header."""
    out = []
    for match in _STATEMENT_RE.finditer(code):
        statement = match.group(0)[:-1]
        if "typedef" in statement or "(*" in statement:
            continue
        declaration = _DECLARATION_RE.match(" ".join(statement.split()))
        if not declaration:
            continue
        prefix, name, paramlist = declaration.groups()
        out.append((_EXTERN_RE.sub(" ", prefix), name, paramlist, match.start()))
    return out


def extract_openmp(header_path=None):
    """-> list[(ir_dict, list[Flag])]."""
    path = header_path or _HEADER_PATH
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    code = c_header.blank_comments(c_header.select_active_lines(raw, _MACROS))
    desc_index = build_spec_index(_SPEC_DESC_DIR)
    ref_index = build_spec_index(_SPEC_REF_DIR)
    fortran_index = fortran_lib.build_fortran_index(_FORTRAN_PATH)

    results = []
    seen = {}
    for prefix, name, paramlist, offset in _declarations(code):
        line = code.count("\n", 0, offset) + 1
        entry_key = f"openmp:{name}"
        if name in seen:
            raise ValueError(f"{entry_key}: declared twice in the C view of {_HEADER_NAME} "
                             f"(lines {seen[name]} and {line}) -- the macro table selects the wrong branch")
        seen[name] = line
        flags = []

        return_type = c_header.normalize_type(prefix)
        try:
            raw_params = [p for p in (c_header.parse_c_param(t) for t in paramlist.split(",")) if p]
        except ValueError as e:
            raise ValueError(f"{entry_key} ({_HEADER_NAME}:{line}): {e}") from None

        ref = ref_index.get(name) or {}
        # The ARB header names all but two parameters; the specification's own
        # prototype supplies those, and only when the arity matches so a name
        # cannot land on the wrong position.
        ref_params = ref.get("params")
        use_ref_names = bool(ref_params) and len(ref_params) == len(raw_params) and all(ref_params)

        fortran = fortran_index.get(name)
        if fortran is not None and len(fortran["args"]) != len(raw_params):
            # Positional matching is only sound at equal arity.
            flags.append(Flag(
                entry_key=entry_key, field="parameters[].direction", severity="note",
                reason=f"{_FORTRAN_NAME} declares {len(fortran['args'])} argument(s) for this routine against "
                       f"{_HEADER_NAME}'s {len(raw_params)}, so its INTENT was not applied",
            ))
            fortran = None

        parameters = []
        unnamed = []
        from_spec = []
        for i, p in enumerate(raw_params):
            if p["name"]:
                pname = p["name"]
            elif use_ref_names:
                pname = ref_params[i]
                from_spec.append(pname)
            else:
                pname = f"arg{i}"
                unnamed.append(pname)
            p = dict(p, name=pname)
            fortran_type = None
            if fortran is not None and i < len(fortran["args"]):
                declaration = fortran["decls"].get(fortran["args"][i])
                fortran_type = declaration["type"] if declaration else None
            parameters.append({
                "name": pname,
                "direction": _direction_for(p, i, name, entry_key, fortran, flags),
                "desc": None,
                "binding_type": {"c": p["c_type"] + p["array_suffix"],
                                 "fortran90": None, "fortran08": fortran_type, "lis": None, "cpp": None},
                "asynchronous": False,
                "constant": p["constant"],
                "pointer": p["pointer"],
                "array_type": None,
                "func_type": None,
                "length": None,
                "root_only": False,
                "_lang_included": {"c": True, "fortran08": fortran_type is not None},
            })
        if from_spec:
            flags.append(Flag(
                entry_key=entry_key, field="parameters[].name", severity="note",
                reason=f"{_HEADER_NAME}:{line} declares these parameters without names; {', '.join(from_spec)} "
                       f"taken by position from the {_SPEC_REF_VERSION_LABEL} specification, "
                       f"section {ref.get('section')}",
            ))
        if unnamed:
            flags.append(Flag(
                entry_key=entry_key, field="parameters[].name", severity="note",
                reason=f"{_HEADER_NAME}:{line} declares {', '.join(unnamed)} without a name, and the "
                       f"{_SPEC_REF_VERSION_LABEL} prototype does not supply one at matching arity; named "
                       f"after their position",
            ))

        params_text = ", ".join(c_header.render_param(p) for p in raw_params) or "void"
        c_signature = f"{return_type} {name}({params_text})"

        standard_refs = []
        if ref.get("section_title"):
            chapter = ref.get("chapter")
            # "18 Runtime Library Routines" -> "Runtime Library Routines".
            chapter_title = chapter.split(" ", 1)[1] if chapter and " " in chapter else None
            label = f"{chapter_title} - {ref['section_title']}" if chapter_title else ref["section_title"]
            standard_refs.append(f"{label} ({_SPEC_REF_VERSION})")

        fortran08 = None
        if fortran is not None:
            fortran08 = {"name": name, "expressible": True, "abstract_interface": False,
                         "module": _FORTRAN_MODULE}
        elif name in fortran_index:
            # An arity mismatch, already flagged above with both counts. Fortran
            # genuinely takes fewer arguments for the string routines, whose
            # character(len=*) dummies carry their own length.
            flags.append(Flag(
                entry_key=entry_key, field="bindings.fortran08", severity="note",
                reason=f"{_FORTRAN_NAME} declares this routine, but not at {_HEADER_NAME}'s arity, so the "
                       f"binding is left null rather than paired with a different argument list",
            ))
        else:
            flags.append(Flag(
                entry_key=entry_key, field="bindings.fortran08", severity="note",
                reason=f"{_FORTRAN_NAME} declares no interface for this routine: the ARB publishes no Fortran "
                       f"binding for it",
            ))

        desc = None
        spec_desc = desc_index.get(name) or {}
        if spec_desc.get("summary"):
            note = f"literal Summary sentence, {_SPEC_DESC_VERSION} section {spec_desc.get('section')}"
            if spec_desc.get("shared_with"):
                note += f" -- a section the standard shares with {', '.join(spec_desc['shared_with'])}"
            desc = Confident(value=spec_desc["summary"], confidence="static", note=note)
        else:
            flags.append(Flag(
                entry_key=entry_key, field="identity.desc", severity="note",
                reason=f"neither {_HEADER_NAME} nor {_SPEC_REF_VERSION_LABEL} carries a one-line description "
                       f"({_SPEC_REF_VERSION_LABEL} replaced 5.2's per-routine Summary block with a "
                       f"multi-sentence Effect paragraph), and {_SPEC_DESC_VERSION} does not define this "
                       f"routine -- identity.desc stays null rather than condensing prose",
            ))

        ir = {
            "model": "openmp",
            "function_key": name,
            "name": name,
            "desc": desc,
            "since": None,
            "deprecated_in": None,
            "standard_refs": standard_refs,
            "bindings": {
                "c": {"expressible": True, "header": _HEADER_NAME, "signature": c_signature},
                "fortran90": None, "fortran08": fortran08, "lis": None, "cpp": None,
            },
            "parameters": parameters,
            "return_kind": _return_kind(name, return_type),
            "return_binding_type": {"c": return_type},
            "flags": flags,
        }
        results.append((ir, flags))

    return results
