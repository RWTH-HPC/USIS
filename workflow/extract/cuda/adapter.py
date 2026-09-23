"""
CUDA adapter: external-inputs/cuda/implementation/cuda-13.1.0/include/cuda_runtime_api.h
-> IR dicts.

Scope: the CUDA Runtime API -- every `extern ... CUDARTAPI cuda*(...)` routine
declared in cuda_runtime_api.h. Out of scope: the device-side runtime
(cuda_device_runtime_api.h, not vendored), the driver API (cuda.h, `cu*`),
and kernels/intrinsics, none of which this header declares.

The header is read as it is seen by an ordinary host-side C compile of CUDA
13.1 with default settings (_macros_for): `__CUDART_API_VERSION` equals the
header's own CUDART_VERSION, and `__cplusplus`, `__CUDA_API_VERSION_INTERNAL`,
`CUDA_API_PER_THREAD_DEFAULT_STREAM`, `__CUDACC_RTC__` and `__CUDA_ARCH__` are
undefined. That drops the `__CUDA_API_VERSION_INTERNAL` block at the end of the
file, which re-declares most stream-ordered routines a second time for the
runtime's own build.

What the header gives:

  - Names, return types, parameter names and types: literal. `extern`,
    `CUDARTAPI` and `__CUDA_DEPRECATED` are stripped; C++ default arguments
    (`__dv(0)`) are dropped from the C signature and noted per parameter.
  - `__host__`/`__device__`/`__cudart_builtin__` are KEPT as a prefix on
    bindings.c.signature, exactly as the NVSHMEM adapter keeps its qualifiers,
    so Heuristic Classification can read execution.launch off the signature.
  - A doxygen block above every routine. `\\brief` is a purpose-built
    one-line summary -- the same kind of source as OpenSHMEM's
    `\\apisummary{}`, not the multi-paragraph prose that got identity.desc
    extraction retired for MPI, NCCL and NVSHMEM (curated/README.md)
    -- so it feeds identity.desc at `static` confidence. The body paragraphs
    are not read. `\\param name - text` gives parameters[].desc, and
    `\\param[in]`/`[out]` gives a literal direction where NVIDIA wrote one
    (a few dozen of ~1000 parameters); every other direction is the
    const/pointer heuristic, flagged low_confidence.
  - identity.deprecated_in: only "deprecated as of CUDA X.Y" is a version.
    A bare `\\deprecated` or `__CUDA_DEPRECATED` marks a routine deprecated
    without saying since when -- left null and noted.
  - identity.since: nothing in the header. From the supplement.

Two spellings are noted rather than modelled. Under
CUDA_API_PER_THREAD_DEFAULT_STREAM (`nvcc --default-stream per-thread`) the
header #defines ~70 routine names to `<name>_ptds`/`_ptsz`, distinct exported
symbols with per-thread default-stream semantics; an entry describes the
legacy-default-stream spelling it is declared under. A `_v<N>` suffix marks a
versioned re-issue of an older routine.
"""

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ir import Confident  # noqa: E402
from status import Flag  # noqa: E402
import c_header  # noqa: E402

_LAYOUT_COMMON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "common")
sys.path.insert(0, _LAYOUT_COMMON)
from layout import EXTERNAL_INPUTS_DIR  # noqa: E402

_HEADER_NAME = "cuda_runtime_api.h"
_HEADER_PATH = os.path.join(EXTERNAL_INPUTS_DIR, "cuda", "implementation", "cuda-13.1.0", "include", _HEADER_NAME)

_DECL_RE = re.compile(r"\bextern\s+([^;(){}\"]*?)\bCUDARTAPI\s+(\w+)\s*\(([^()]*)\)\s*;")
_QUALIFIERS = ("__host__", "__device__", "__cudart_builtin__")
_DEPRECATED_MARKER = "__CUDA_DEPRECATED"
_VERSION_RE = re.compile(r"^\s*#\s*define\s+CUDART_VERSION\s+(\d+)", re.MULTILINE)
_PER_THREAD_RE = re.compile(r"#\s*define\s+(\w+)\s+__CUDART_API_(PTDS|PTSZ)\(\1\)")
_VERSIONED_RE = re.compile(r"_v\d+$")
_DEFAULT_ARG_RE = re.compile(r"__dv\s*\((.*)\)", re.DOTALL)

_DOC_PARAM_RE = re.compile(r"^\\param(?:\[\s*([a-z,\s]+?)\s*\])?\s+(\w+)\s*-\s*(.*)$")
_DOC_DIRECTIONS = {"in": "in", "out": "out", "in,out": "inout", "inout": "inout"}
_DEPRECATED_SINCE_RE = re.compile(r"deprecated as of CUDA (\d+(?:\.\d+)*)", re.IGNORECASE)


def _macros_for(raw):
    return {"__CUDART_API_VERSION": int(_VERSION_RE.search(raw).group(1))}


def _clean(text):
    text = re.sub(r"\\(?:p|e|b|c|a|ref)\s+", "", text)  # inline markup: "\p count" -> "count"
    text = re.sub(r"::(\w)", r"\1", text)              # "::cudaMemcpy" -> "cudaMemcpy"
    return " ".join(text.split())


def _parse_doc(block):
    """A doxygen block -> {"brief": str|None, "params": {name: (direction|None, text)},
    "deprecated": str|None}. Only the tagged parts are read, never the body."""
    lines = [re.sub(r"^\s*\*? ?", "", line).rstrip() for line in block[3:-2].split("\n")]

    def collect(i, first):
        parts, j = [first], i + 1
        while j < len(lines) and lines[j].strip() and not lines[j].strip().startswith("\\"):
            parts.append(lines[j].strip())
            j += 1
        return _clean(" ".join(parts))

    doc = {"brief": None, "params": {}, "deprecated": None}
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("\\brief") and doc["brief"] is None:
            doc["brief"] = collect(i, s[len("\\brief"):].strip()) or None
        elif s.startswith("\\param"):
            m = _DOC_PARAM_RE.match(s)
            if m:
                direction_raw, pname, text = m.groups()
                direction = _DOC_DIRECTIONS.get(re.sub(r"\s", "", direction_raw)) if direction_raw else None
                doc["params"][pname] = (direction, collect(i, text))
        elif s.startswith("\\deprecated"):
            doc["deprecated"] = collect(i, s[len("\\deprecated"):].strip())
    return doc


def _return_kind(return_type):
    if return_type == "cudaError_t":
        return "ERROR_CODE"
    if return_type == "void":
        return "void"
    if "*" in return_type:
        return "RESULT"
    return "value"


def extract_cuda(header_path=None):
    """-> list[(ir_dict, list[Flag])]."""
    path = header_path or _HEADER_PATH
    with open(path, encoding="utf-8") as f:
        raw = f.read()

    active = c_header.select_active_lines(raw, _macros_for(raw))
    docs = c_header.DocIndex(active)
    no_comments = c_header.blank_comments(active)
    code = c_header.blank_calls(no_comments, "__dv")
    per_thread = {name: kind.lower() for name, kind in _PER_THREAD_RE.findall(raw)}

    results = []
    seen = {}
    for m in _DECL_RE.finditer(code):
        prefix, name, _ = m.groups()
        line = code.count("\n", 0, m.start(2)) + 1
        entry_key = f"cuda:{name}"
        if name in seen:
            raise ValueError(f"{entry_key}: declared twice in the host C view of {_HEADER_NAME} "
                             f"(lines {seen[name]} and {line}) -- the macro table selects the wrong branch")
        seen[name] = line
        flags = []

        prefix_tokens = prefix.split()
        qualifiers = [t for t in prefix_tokens if t in _QUALIFIERS]
        deprecated_marker = _DEPRECATED_MARKER in prefix_tokens
        return_type = c_header.normalize_type(
            " ".join(t for t in prefix_tokens if t not in _QUALIFIERS and t != _DEPRECATED_MARKER))

        block = docs.before(m.start())
        doc = _parse_doc(block) if block else {"brief": None, "params": {}, "deprecated": None}
        if block is None:
            flags.append(Flag(entry_key=entry_key, field="identity.desc", severity="note",
                               reason=f"no doxygen block immediately above {_HEADER_NAME}:{line}"))

        raw_params = []
        for start, end in c_header.split_top_level(code, *m.span(3)):
            try:
                p = c_header.parse_c_param(code[start:end])
            except ValueError as e:
                raise ValueError(f"{entry_key} ({_HEADER_NAME}:{line}): {e}") from None
            if p is None:
                continue
            default = _DEFAULT_ARG_RE.search(no_comments[start:end])
            p["default"] = " ".join(default.group(1).split()) if default else None
            raw_params.append(p)

        parameters = []
        for i, p in enumerate(raw_params):
            pname = p["name"] or f"arg{i}"
            if p["name"] is None:
                flags.append(Flag(entry_key=entry_key, field=f"parameters[{pname}].name", severity="note",
                                   reason=f"{_HEADER_NAME}:{line} declares this parameter without a name; "
                                          f"named after its position"))
            doc_direction, doc_desc = doc["params"].get(pname, (None, None))
            released = c_header.released_direction("cuda", name, pname)
            if doc_direction is not None:
                direction = doc_direction
            elif released is not None:
                direction = "in"
                flags.append(Flag(
                    entry_key=entry_key, field=f"parameters[{pname}].direction", severity="note",
                    reason=f"'in', not the 'out' that const/pointer-ness alone implies: this parameter names "
                           f"memory the call releases -- {released}",
                ))
            else:
                direction = "in" if not p["pointer"] else ("in" if p["constant"] else "out")
                flags.append(Flag(
                    entry_key=entry_key, field=f"parameters[{pname}].direction", severity="low_confidence",
                    reason="inferred from const-qualification/pointer-ness (no \\param[in]/[out] annotation for "
                           "this parameter); cannot distinguish 'out' from 'inout' for a non-const pointer",
                ))
            if p["default"] is not None:
                flags.append(Flag(entry_key=entry_key, field=f"parameters[{pname}]", severity="note",
                                   reason=f"C++ callers may omit this argument (default {p['default']}); "
                                          f"C callers must pass it"))
            parameters.append({
                "name": pname,
                "direction": direction,
                "desc": doc_desc or None,
                "binding_type": {"c": p["c_type"] + p["array_suffix"],
                                 "fortran90": None, "fortran08": None, "lis": None, "cpp": None},
                "asynchronous": False,
                "constant": p["constant"],
                "pointer": p["pointer"],
                "array_type": None,
                "func_type": None,
                "length": None,
                "root_only": False,
                "_lang_included": {"c": True},
            })

        desc = None
        if doc["brief"]:
            desc = Confident(doc["brief"], "static", "doxygen \\brief summary line, literal")
        elif block is not None:
            flags.append(Flag(entry_key=entry_key, field="identity.desc", severity="note",
                               reason=f"doxygen block above {_HEADER_NAME}:{line} has no \\brief line"))

        deprecated_in = None
        if doc["deprecated"] is not None or deprecated_marker:
            since = _DEPRECATED_SINCE_RE.search(doc["deprecated"] or "")
            if since:
                deprecated_in = Confident(f"CUDA-{since.group(1)}", "static", "literal '\\deprecated ... as of CUDA X.Y'")
            else:
                flags.append(Flag(entry_key=entry_key, field="identity.deprecated_in", severity="note",
                                   reason="marked deprecated in the header (\\deprecated and/or __CUDA_DEPRECATED) "
                                          "without a version -- deprecated_in left null"))

        if name in per_thread:
            flags.append(Flag(entry_key=entry_key, field="bindings.c", severity="note",
                               reason=f"under CUDA_API_PER_THREAD_DEFAULT_STREAM (nvcc --default-stream per-thread) "
                                      f"{_HEADER_NAME} #defines {name} to {name}_{per_thread[name]}, a distinct symbol "
                                      f"with per-thread default-stream semantics; this entry is the legacy spelling"))
        if _VERSIONED_RE.search(name):
            flags.append(Flag(entry_key=entry_key, field="identity.name", severity="note",
                               reason="_v<N> suffix: a versioned re-issue of an older routine of the same stem"))

        params_text = ", ".join(c_header.render_param(p) for p in raw_params) or "void"
        c_signature = f"{' '.join(qualifiers + [return_type])} {name}({params_text})"

        ir = {
            "model": "cuda",
            "function_key": name,
            "name": name,
            "desc": desc,
            "since": None,
            "deprecated_in": deprecated_in,
            "standard_refs": [],
            "bindings": {
                "c": {"expressible": True, "header": _HEADER_NAME, "signature": c_signature},
                "fortran90": None, "fortran08": None, "lis": None, "cpp": None,
            },
            "parameters": parameters,
            "return_kind": _return_kind(return_type),
            "return_binding_type": {"c": return_type},
            "flags": flags,
        }
        results.append((ir, flags))

    return results
