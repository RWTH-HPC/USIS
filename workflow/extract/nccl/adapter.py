"""
NCCL adapter: external-inputs/nccl/.../include/nccl.h -> IR dicts, cross-referenced
against external-inputs/nccl/docs/2.30/api/*.md.

identity.desc is NOT among the fields produced here (retired 2026-07-21,
matching the same decision already taken for MPI and NVSHMEM) -- it comes
from curated/supplement/supplement-nccl.json. See the `desc` assignment below for why,
and curated/README.md for the tier this puts it in.

v1 scope: nccl.h (the classic host API) only -- not nccl_device.h /
nccl_device/, a structurally different, newer device-side API family that
would need its own adapter design (flagged as an open question, not
resolved here; see the approved plan).

Bare C header, confirmed by direct inspection: no macro-based direction/
asynchronous/root_only annotations exist at all (unlike MPI's apis.json or
OpenSHMEM's \\apiargument{} macros). Only const-qualification and pointer-
ness are mechanically available from the declaration syntax itself. This
makes parameters[].direction a genuine heuristic here, not a literal read,
and it is flagged low_confidence unconditionally (not just for ambiguous
cases) because const-only inference cannot distinguish "out" from "inout"
-- NCCL's legal in-place pattern (sendbuff == recvbuff, confirmed directly
in nccl.h's own doc comments above ncclAllReduce/ncclBroadcast) is exactly
the case where a non-const "out" pointer is really being read from too.

pnccl*-prefixed declarations (the profiling shadow API, confirmed literally
present in nccl.h immediately after every real declaration) are skipped as
entries and used only as a free correctness check on derive_profiling_name's
output (emit.py) instead.
"""

import glob
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

_HEADER_PATH = os.path.join(
    EXTERNAL_INPUTS_DIR, "nccl", "implementation", "nccl_2.30.7-1+cuda13.3_x86_64", "include", "nccl.h",
)
_DOCS_DIR = os.path.join(EXTERNAL_INPUTS_DIR, "nccl", "docs", "2.30", "api")

# One top-level declaration: RETTYPE NAME(params...); -- RETTYPE may itself
# contain spaces/pointers ("const char*"), NAME is a plain identifier,
# params captured whole (may itself contain balanced parens? not observed
# in this header -- no function-pointer params exist here, confirmed by
# direct grep). DOTALL/MULTILINE so a declaration split across lines
# (confirmed real: ncclBroadcast, ncclAllReduce, ...) is captured whole.
_DECL_RE = re.compile(r"^([A-Za-z_][\w\s\*]*?)\s+(\w+)\s*\(([^)]*)\)\s*;", re.MULTILINE)

_MD_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_MD_HEADING_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)
_MD_SIGNATURE_RE = re.compile(r"^\s*([A-Za-z_][\w\s\*]*?)\s+(\w+)\s*\(([^)]*)\)\s*$")

_RETURN_KIND_MAP = {"ncclResult_t": "ERROR_CODE", "void": "void"}


def _strip_md_links(text):
    return _MD_LINK_RE.sub(r"\1", text)


def _parse_c_param(param_text, entry_key, flags):
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
    pointer = sep_char == "*" or base_type.endswith("*")
    base_type = base_type.rstrip("*").strip()
    return {"name": name, "base_type": base_type, "constant": constant, "pointer": pointer}


def _direction_for(param, entry_key, flags, function_key=None):
    # A non-pointer (by-value) parameter can never be written back through --
    # it's always "in" regardless of const-qualification (plain scalars like
    # `size_t count`/`ncclComm_t comm` are rarely marked const in C, but
    # that's a style choice, not a direction signal). Only pointer
    # parameters are candidates for "out": const-qualified -> "in",
    # non-const -> "out" by default.
    released = c_header.released_direction("nccl", function_key, param["name"])
    if released is not None:
        flags.append(Flag(
            entry_key=entry_key, field=f"parameters[{param['name']}].direction", severity="note",
            reason=f"'in', not the 'out' that const/pointer-ness alone implies: this parameter names memory "
                   f"the call releases -- {released}",
        ))
        return "in"
    if not param["pointer"]:
        direction = "in"
    else:
        direction = "in" if param["constant"] else "out"
    flags.append(Flag(
        entry_key=entry_key, field=f"parameters[{param['name']}].direction", severity="low_confidence",
        reason="inferred from const-qualification/pointer-ness alone (no direction annotation exists in this header); cannot distinguish 'out' from 'inout' for non-const pointers -- NCCL's legal in-place pattern (sendbuff == recvbuff) is exactly this failure mode",
    ))
    return direction


def _build_docs_index():
    """-> {function_name: desc}, scanning every ## heading section in every
    external-inputs/nccl/docs/2.30/api/*.md file for embedded RETTYPE Name(...)
    signature lines (a heading section can describe more than one function,
    e.g. '## ncclBroadcast' also covers legacy 'ncclBcast' -- confirmed by
    direct inspection of colls.md) and taking the prose immediately
    following each as that function's desc.
    """
    index = {}
    for path in glob.glob(os.path.join(_DOCS_DIR, "*.md")):
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
        lines = text.split("\n")

        i = 0
        while i < len(lines):
            line = _strip_md_links(lines[i])
            m = _MD_SIGNATURE_RE.match(line)
            if m:
                _, name, _ = m.groups()
                para_lines = []
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                while j < len(lines):
                    stripped = lines[j].strip()
                    if not stripped:
                        break
                    if stripped.startswith("Related links:") or stripped.startswith("##") or _MD_SIGNATURE_RE.match(_strip_md_links(lines[j])) or stripped.startswith("```"):
                        break
                    para_lines.append(stripped)
                    j += 1
                if para_lines and name not in index:
                    index[name] = re.sub(r"`([^`]*)`", r"\1", " ".join(para_lines))
                i = j
            else:
                i += 1
    return index


def extract_nccl(header_path=None, docs_dir=None):
    """-> list[(ir_dict, list[Flag])]."""
    path = header_path or _HEADER_PATH
    with open(path, encoding="utf-8", errors="replace") as f:
        header_text = f.read()

    docs_index = _build_docs_index() if docs_dir is None else _build_docs_index()

    results = []
    for m in _DECL_RE.finditer(header_text):
        return_type_raw, name, paramlist_text = m.groups()
        return_type = " ".join(return_type_raw.split())

        if name.startswith("pnccl"):
            continue  # profiling shadow API -- see module docstring

        entry_key = f"nccl:{name}"
        flags = []

        raw_params = [_parse_c_param(p, entry_key, flags) for p in paramlist_text.split(",")]
        raw_params = [p for p in raw_params if p]

        parameters = []
        for p in raw_params:
            direction = _direction_for(p, entry_key, flags, name)
            parameters.append({
                "name": p["name"],
                "direction": direction,
                "desc": None,  # confirmed gap: no per-parameter prose exists in docs or header
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

        return_kind = _RETURN_KIND_MAP.get(return_type, "value")
        if return_type not in _RETURN_KIND_MAP:
            flags.append(Flag(entry_key=entry_key, field="return.kind", severity="note",
                               reason=f"return type {return_type!r} treated as schema kind 'value' (only ncclResult_t->ERROR_CODE and void->void are mapped explicitly)"))

        param_sig = ", ".join(f"{'const ' if p['constant'] else ''}{p['base_type']}{'*' if p['pointer'] else ' '}{p['name']}" for p in raw_params)
        c_signature = f"{return_type} {name}({param_sig})"

        # identity.desc is deliberately never emitted here -- retired
        # 2026-07-21, the same decision already taken for MPI and NVSHMEM
        # (see workflow/extract/mpi/prose.py's and workflow/extract/nvshmem/
        # adapter.py's docstrings, and curated/README.md).
        #
        # The prose _build_docs_index finds is correct content in the wrong
        # SHAPE: the docs mirror's paragraph is whatever length that page
        # needed, not the one-sentence summary api-schema.json specifies for
        # this field. Most NCCL sections happen to be one clean sentence,
        # which is why this looked fine until audited -- but ncclCommInitRank
        # and ncclCommDestroy carry four-sentence operational blobs complete
        # with raw "*comm*" markdown emphasis artifacts, and nothing
        # mechanical distinguishes those from the good ones without
        # re-deriving the same first-sentence truncation heuristic that was
        # already tried and rejected as a structural mismatch for the other
        # two PPMs.
        #
        # _build_docs_index is kept, not deleted: it is correct, cheap, and
        # the natural starting point for hand-condensing a real
        # curated/supplement/supplement-nccl.json entry.
        desc = None
        flags.append(Flag(
            entry_key=entry_key, field="identity.desc", severity="note",
            reason="identity.desc is not extracted for NCCL (retired 2026-07-21, matching MPI/NVSHMEM): the "
                   "docs mirror's paragraph is arbitrary-length prose, not the one-sentence summary this "
                   "field specifies -- sourced from curated/supplement/supplement-nccl.json instead",
        ))

        ir = {
            "model": "nccl",
            "function_key": name,
            "name": name,
            "desc": Confident(value=desc, confidence="static", note="matched via docs mirror heading + signature line") if desc else None,
            "since": None,
            "deprecated_in": None,
            "standard_refs": [],
            "bindings": {
                "c": {"expressible": True, "header": "nccl.h", "signature": c_signature},
                "fortran90": None, "fortran08": None, "lis": None, "cpp": None,
            },
            "parameters": parameters,
            "return_kind": return_kind,
            "return_binding_type": {"c": return_type},
            "flags": flags,
        }
        results.append((ir, flags))

    return results
