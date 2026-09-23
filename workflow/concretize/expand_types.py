"""
Concretize -- the new workflow step (this session's approved plan, revising
the original "collapse type families in Extract" plan once it became clear
the collapse should propagate all the way through the workflow) that
resolves a collapsed, still-"{T}"/"{CT}"-generic entry back into N concrete
entries, one per listed identity.type_family type -- the very last step
before Validate.

Why here, why last: every upstream stage (Heuristic Classification, Generate
Formal's assignment+expansion, AI-Assisted Classification) does its
classification/assignment work exactly ONCE per collapsed family, not once
per concrete type -- that is the entire efficiency point of collapsing type-
generic families in Extract (see workflow/extract/nvshmem/adapter.py,
workflow/extract/shmem/adapter.py, docs/schema/schema-overview.md's
Type-genericity note). But a shipped, validated entry must always be fully
concrete -- api-schema.json's own $defs never expect a literal "{T}"/"{CT}"
string in identity.name, or a "type:{T}" in a data_flow_entry.extent.
datatype_ref. Concretize is what draws that line: substitute every
placeholder back to a real, chosen (typename, ctype) pair, exactly once,
immediately before Validate.

Substitution rule: replace the literal substrings "{T}" (-> typename, e.g.
"int") and "{CT}" (-> ctype, e.g. "long long") wherever they appear in any
string value anywhere in the entry, recursively -- deliberately generic
rather than a hardcoded list of "the fields that might contain a
placeholder" (identity.name, bindings.c.signature, semantics.formal's
datatype_ref), so a new formal-layer field that happens to reuse the same
convention doesn't silently get skipped.

The typename->ctype mapping is NOT smuggled through every entry (see this
session's approved plan) -- it is re-derived fresh, once per run, from the
same real sources Extract itself parsed, via
workflow/extract/nvshmem/adapter.py's and workflow/extract/shmem/adapter.py's
own build_typename_ctype_map() (added alongside this module) -- one source
of truth, never a second, independently-maintained copy that could drift.
"""

import copy
import importlib.util
import os
import sys

_HERE = os.path.dirname(__file__)
_ROOT = os.path.join(_HERE, "..", "..")


def _load_module(unique_name, file_path, extra_sys_path=()):
    for p in extra_sys_path:
        if p not in sys.path:
            sys.path.insert(0, p)
    spec = importlib.util.spec_from_file_location(unique_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[unique_name] = module
    spec.loader.exec_module(module)
    return module


def load_typename_ctype_maps():
    """-> {"nvshmem": {typename: ctype, ...}, "shmem": {typename: ctype, ...}}.

    Both adapters are literally named adapter.py -- loaded under distinct
    sys.modules keys via explicit file path, the same collision workaround
    already used by workflow/extract/test_emit.py and workflow/classify/cli.py.
    """
    _extract_dir = os.path.join(_ROOT, "workflow", "extract")
    nvshmem_adapter = _load_module(
        "_concretize_nvshmem_adapter", os.path.join(_extract_dir, "nvshmem", "adapter.py"),
        extra_sys_path=[_extract_dir, os.path.join(_extract_dir, "nvshmem")],
    )
    shmem_adapter = _load_module(
        "_concretize_shmem_adapter", os.path.join(_extract_dir, "shmem", "adapter.py"),
        extra_sys_path=[_extract_dir, os.path.join(_extract_dir, "shmem")],
    )
    return {
        "nvshmem": nvshmem_adapter.build_typename_ctype_map(),
        "shmem": shmem_adapter.build_typename_ctype_map(),
    }


def _substitute_placeholders(obj, typename, ctype):
    if isinstance(obj, dict):
        return {k: _substitute_placeholders(v, typename, ctype) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_substitute_placeholders(v, typename, ctype) for v in obj]
    if isinstance(obj, str) and ("{T}" in obj or "{CT}" in obj):
        return obj.replace("{CT}", ctype).replace("{T}", typename)
    return obj


def concretize_entry(entry, typename_ctype_maps):
    """One entry -> list of concrete entries (one per identity.type_family
    type), or [entry] unchanged if type_family is null -- nothing to
    concretize. The concrete output's own identity.type_family is null: once
    resolved to one specific type, the entry is no longer "generic over"
    anything, matching the field's own meaning (docs/schema/schema-overview.md)."""
    type_family = entry["identity"].get("type_family")
    if not type_family:
        return [entry]

    model = entry["identity"]["model"]
    ctype_map = typename_ctype_maps.get(model, {})

    concretized = []
    for typename in type_family:
        ctype = ctype_map.get(typename)
        if ctype is None:
            raise ValueError(
                f"no ctype known for {model} typename {typename!r} in {entry['identity']['name']!r} -- "
                f"typename_ctype_maps out of date relative to identity.type_family?"
            )
        concrete = _substitute_placeholders(copy.deepcopy(entry), typename, ctype)
        concrete["identity"]["type_family"] = None
        concretized.append(concrete)
    return concretized


def concretize_corpus(entries, typename_ctype_maps):
    """{entry_key: entry} -> {entry_key: entry}: every type-generic family
    entry expands into one concrete entry per type (new key = the family
    key with "{T}"/"{CT}" substituted the same way); every other entry
    passes through completely unchanged, same key."""
    out = {}
    for entry_key, entry in entries.items():
        type_family = entry["identity"].get("type_family")
        if not type_family:
            out[entry_key] = entry
            continue
        model = entry_key.split(":", 1)[0]
        ctype_map = typename_ctype_maps.get(model, {})
        # concretize_entry() iterates type_family in this same order, so
        # zipping the two lists correctly pairs each concrete entry with the
        # typename that produced it.
        for typename, concrete in zip(type_family, concretize_entry(entry, typename_ctype_maps)):
            concrete_key = entry_key.replace("{CT}", ctype_map[typename]).replace("{T}", typename)
            out[concrete_key] = concrete
    return out
