"""
The OpenMP ARB's Fortran interface module (`fortran/omp_lib.f90`) -> a per-routine
index of dummy arguments, their declared types, and their INTENT.

This file is the second half of the ARB's published interface definition, beside
`include/omp.h`, and it answers something the C header cannot: **argument
direction**. C says only const-or-not, which cannot tell an input handle from an
output one -- `omp_set_lock(omp_lock_t *lock)` and `omp_get_schedule(int *kind,
...)` look identical to a const/pointer heuristic. Fortran must state it, so the
ARB does:

    subroutine omp_set_lock (svar)
      integer(kind=omp_lock_kind), intent(inout) :: svar     -> inout
    subroutine omp_init_lock (svar)
      integer(kind=omp_lock_kind), intent(out) :: svar       -> out
    subroutine omp_free (ptr, allocator) bind(c)
      type(c_ptr), value :: ptr                              -> in

Only INTENT is read. The VALUE attribute looks like a second direction signal --
a by-value dummy cannot be written back -- but it describes the *pointer*, not
what the pointer addresses, and the ARB spells both `omp_free`'s `ptr` (which is
an input: the pointee is deallocated) and `omp_target_memcpy`'s `dst` (which is
an output: the pointee is written) as `type(c_ptr), value`. Reading VALUE as a
direction would therefore mark every destination buffer in the corpus `in`. The
6.0 specification's own argument-properties table is no better -- it gives `dst`
"iso_c, value" and `src` "intent(in), iso_c, value", mirroring the C const and
nothing more. Those cases stay with the const/pointer heuristic, and the handful
it gets wrong are corrected from each routine's own Effect text by
`c_header.RELEASED_PARAMETERS`.

Matching to the C declaration is **positional, not by name** -- the two bindings
name their arguments differently (`omp_set_lock`'s C `lock` is Fortran `svar`) --
and only when both declare the same number of arguments, so a direction cannot
slide onto the wrong parameter.

Deterministic and stdlib-only, like every other extraction input.
"""

import re

# A continuation line ("... &\n   ...") is joined before anything is matched:
# omp_get_submemspace's interface spans three lines that way.
_CONTINUATION_RE = re.compile(r"&\s*\n\s*")

# "    subroutine omp_set_lock (svar)", "    integer function omp_get_thread_num ()",
# "    type(c_ptr) function omp_target_alloc (size, device_num) bind(c)".
# The optional prefix is a Fortran result-type specification, which may carry a
# parenthesised kind or length selector: "integer function", "type(c_ptr)
# function", "integer(kind=omp_memspace_handle_kind) function", and
# "character(:) function" (omp_get_uid_from_device) -- so ':' and '=' belong in
# the prefix's character class as much as word characters do.
_INTERFACE_RE = re.compile(
    r"^\s*(?:[\w()=,:.* ]*?\s)?(subroutine|function)\s+(omp_\w+)\s*\(([^)]*)\)", re.IGNORECASE)
_END_RE = re.compile(r"^\s*end\s+(?:subroutine|function)\b", re.IGNORECASE)

# "integer(kind=omp_lock_kind), intent(inout) :: svar" -> attributes, names.
_DECL_RE = re.compile(r"^\s*(.+?)\s*::\s*(.+?)\s*$")
_INTENT_RE = re.compile(r"\bintent\s*\(\s*(in|out|inout)\s*\)", re.IGNORECASE)
_VALUE_RE = re.compile(r"(^|,)\s*value\s*($|,)", re.IGNORECASE)


def _dummy_names(text):
    """"kind, chunk_size" -> ["kind", "chunk_size"]; an array declarator
    ("resources(*)") keeps only the name."""
    out = []
    for fragment in text.split(","):
        name = fragment.strip().split("(")[0].strip()
        if name:
            out.append(name)
    return out


def build_fortran_index(path):
    """{routine: {"args": [name], "decls": {name: {"type", "intent", "value"}},
                  "kind": "subroutine"|"function"}}."""
    lines = _CONTINUATION_RE.sub(" ", open(path, encoding="utf-8").read()).split("\n")
    index = {}
    i = 0
    while i < len(lines):
        m = _INTERFACE_RE.match(lines[i])
        if not m:
            i += 1
            continue
        kind, name, arglist = m.group(1).lower(), m.group(2), m.group(3)
        args = _dummy_names(arglist)
        decls = {}
        j = i + 1
        while j < len(lines) and not _END_RE.match(lines[j]):
            d = _DECL_RE.match(lines[j])
            if d and not lines[j].lstrip().lower().startswith("use "):
                attributes, names = d.group(1), d.group(2)
                intent = _INTENT_RE.search(attributes)
                for dummy in _dummy_names(names):
                    # A function's result variable is declared the same way as a
                    # dummy argument; only the argument list decides.
                    if dummy in args:
                        decls[dummy] = {
                            "type": " ".join(f"{attributes} :: {dummy}".split()),
                            "intent": intent.group(1).lower() if intent else None,
                            "value": bool(_VALUE_RE.search(attributes)),
                        }
            j += 1
        index[name] = {"args": args, "decls": decls, "kind": kind}
        i = j + 1
    return index


def direction_for(entry, position):
    """The ARB Fortran interface's direction for the argument at `position`, or
    None if it does not state one. -> (direction, evidence)."""
    if not entry or position >= len(entry["args"]):
        return None, None
    decl = entry["decls"].get(entry["args"][position])
    if not decl:
        return None, None
    if decl["intent"]:
        return decl["intent"], f"INTENT({decl['intent'].upper()})"
    return None, None
