"""
The single place that owns R1 structural compliance and field-ownership for
Extract's output (workflow/README.md):

  1. every entry is structured identically to $defs/entry -- same section
     names, same nesting;
  2. every field Extract itself owns (curated/field-provenance.json's
     "syntactic"/"derived" tiers) that an adapter doesn't populate is
     explicitly null/[]/an all-null sub-object, never omitted;
  3. every field owned by a LATER stage (semantic/semantic_heuristic/formal
     tier -- including semantics.formal unconditionally) is OMITTED
     entirely, not null-padded. See docs/overview/glossary.md (Staging schema): a key's presence means "the owning stage
     has examined this and decided" (null = genuinely N/A); its absence
     means "not reached yet". This is what a staging null vs. a final null
     used to be unable to tell apart.

build_null_entry() produces the skeleton (8 sections; only syntactic/derived
leaves present, each null/[]/empty-container; `execution` and `semantics`
come out empty -- every one of their own leaves belongs to a later stage --
see the field-by-field shapes read directly from $defs/{identity,bindings,
binding_c,binding_fortran90,binding_fortran08,binding_lis,binding_cpp,
parameter,binding_type,return,tool_integration,relationships} while writing
this module). assemble_entry() overlays only the syntactic+derived fields
from one adapter's IR dict (workflow/extract/ir.py) onto that skeleton --
this is what guarantees every adapter produces contract-compliant output
without reimplementing section-shape boilerplate itself.

The resulting entry validates against instances/api-schema.staging.post-extract.json
(mechanically derived from api-schema.json + field-provenance.json -- see
workflow/staging/derive_schema.py), not the strict api-schema.json, which
still requires every field once the full workflow has run.
"""

from ir import Confident, LANG_INCLUSION_KEYS, REQUIRED_IR_KEYS, unwrap
from status import Flag

_EMPTY_BINDING_TYPE = {"c": None, "fortran90": None, "fortran08": None, "lis": None, "cpp": None}

_PARAMETER_BINDINGS_ENUM = frozenset({
    "c", "c_large",
    "fortran90", "fortran90_optional",
    "fortran08", "fortran08_optional",
    "lis", "lis_large",
    "cpp",
})


def build_null_entry():
    """The syntactic+derived skeleton: all 8 top-level sections always
    present (R1 holds for structure), but only the leaves Extract itself
    owns are populated (null/[]/empty-container); every leaf owned by a
    later stage is simply not a key here at all. `execution` and
    `semantics` come out as empty objects -- neither section has a single
    syntactic/derived leaf of its own.

    Structure and key sets below are transcribed directly from
    curated/field-provenance.json's tier assignments cross-referenced
    against api-schema.json's $defs -- not reconstructed from memory, to
    guarantee exact ownership match with what
    instances/api-schema.staging.post-extract.json actually requires.
    """
    return {
        "identity": {
            "model": None,
            "name": None,
            "since": None,
            "deprecated_in": None,
            "standard_refs": [],
            "desc": None,
            "type_family": None,
        },
        "bindings": {
            "c": None,
            "fortran90": None,
            "fortran08": None,
            "lis": None,
            "cpp": None,
        },
        "execution": {},
        "semantics": {},
        "parameters": [],
        "return": {
            "kind": None,
            "binding_type": dict(_EMPTY_BINDING_TYPE),
        },
        "tool_integration": {
            "profiling_name": None,
        },
        # Every relationships field belongs to a later stage, so the section
        # comes out empty like execution and semantics (Resolution v2 omission,
        # not null).
        "relationships": {},
    }


def _null_parameter():
    return {
        "name": None,
        "direction": None,
        "desc": None,
        "binding_type": dict(_EMPTY_BINDING_TYPE),
        "asynchronous": None,
        "constant": None,
        "pointer": None,
        "array_type": None,
        "func_type": None,
        "length": None,
        "parameter_bindings": [],
        "root_only": None,
        "constraints": {},
    }


def derive_profiling_name(model, name):
    """tool_integration.profiling_name: PMPI_/pnccl-style prefix transform.

    MPI: PMPI_Send from MPI_Send -- literally "P" prepended (name already
    carries the "MPI_" prefix). NCCL: pncclBroadcast from ncclBroadcast --
    "p" prepended, confirmed against nccl.h's own literal pnccl* shadow
    declarations.

    SHMEM: pshmem_put from shmem_put (corrected 2026-07-21, full-corpus
    audit). The previous "no profiling-interface prefix convention found in
    the sources inspected" was simply wrong for OpenSHMEM -- the standard
    devotes a whole chapter to it, and the vendored copy states the rule
    outright: "...entry point name, with the prefix `pshmem_` for each"
    (external-inputs/shmem/tex/shmem-standard/content/profiling_interface.tex), with
    the pshmem_ declarations living in pshmem.h. All 279 SHMEM entries were
    carrying a null here.

    NVSHMEM: genuinely null. Re-checked during the same audit -- no
    pnvshmem_ symbols exist in the vendored headers and the documentation
    mirror describes no profiling interface. This is the honest gap the old
    docstring claimed for both PGAS PPMs but was only ever true of one.

    OpenMP and CUDA: genuinely null, for different reasons. OpenMP's tool
    support (OMPT) is callback-based -- a tool registers callbacks with the
    runtime rather than interposing a shadow entry point per routine -- so no
    routine has a profiling name. CUDA has no p-prefixed shadow API either;
    its tools interface (CUPTI) is likewise callback-based.
    """
    if model == "mpi":
        return "P" + name
    if model == "nccl":
        return "p" + name
    if model == "shmem":
        return "p" + name
    return None


def derive_parameter_bindings(lang_included):
    """Mechanical repackaging of the per-language inclusion flags (already
    computed by the adapter, itself a mechanical transform of the raw
    source's own optional/large_only/suppress-style flags) into the
    schema's parameter_bindings enum-array form.
    """
    if not lang_included:
        return []
    return sorted(k for k in LANG_INCLUSION_KEYS if lang_included.get(k) and k in _PARAMETER_BINDINGS_ENUM)


def _apply_confident(entry_key, field_path, value, flags):
    plain, confidence, note = unwrap(value)
    if confidence == "needs_approval":
        # Extract never produces AI-drafted values -- everything it emits is
        # either a literal read or a "pattern" heuristic guess. Seeing this
        # here would mean a future adapter change started routing an
        # unapproved AI proposal straight into the shipped entry, which is
        # exactly what "needs_approval" exists to prevent -- see
        # workflow/common/ir.py's docstring.
        raise ValueError(f"{entry_key}.{field_path}: confidence='needs_approval' must never reach _apply_confident")
    if confidence == "pattern":
        flags.append(Flag(entry_key=entry_key, field=field_path, severity="low_confidence", reason=note or "heuristic extraction"))
    return plain


def assemble_entry(ir):
    """ir dict -> (entry dict, list[Flag]).

    Pure function, no I/O. Raises ValueError if a REQUIRED ir key is
    missing -- that's an adapter bug (it should have skipped the function
    and raised a "skipped" Flag itself, never called assemble_entry with an
    incomplete IR), not a source-data quirk to silently null-pad over.
    """
    missing = [k for k in REQUIRED_IR_KEYS if k not in ir or ir[k] is None]
    if missing:
        raise ValueError(f"IR for {ir.get('function_key', '<unknown>')!r} missing required key(s): {missing}")

    model = ir["model"]
    function_key = ir["function_key"]
    entry_key = f"{model}:{function_key}"
    flags = []

    entry = build_null_entry()

    entry["identity"]["model"] = model
    entry["identity"]["name"] = ir["name"]
    entry["identity"]["type_family"] = list(ir["type_family"]) if ir.get("type_family") else None
    if "desc" in ir and ir["desc"] is not None:
        entry["identity"]["desc"] = _apply_confident(entry_key, "identity.desc", ir["desc"], flags)
    if "since" in ir and ir["since"] is not None:
        entry["identity"]["since"] = _apply_confident(entry_key, "identity.since", ir["since"], flags)
    if "deprecated_in" in ir and ir["deprecated_in"] is not None:
        entry["identity"]["deprecated_in"] = _apply_confident(entry_key, "identity.deprecated_in", ir["deprecated_in"], flags)
    entry["identity"]["standard_refs"] = list(ir.get("standard_refs") or [])


    bindings = ir.get("bindings") or {}
    for lang in ("c", "fortran90", "fortran08", "lis", "cpp"):
        entry["bindings"][lang] = bindings.get(lang)

    params_out = []
    for p in ir.get("parameters", []):
        np = _null_parameter()
        np["name"] = p.get("name")
        np["direction"] = p.get("direction")
        np["desc"] = p.get("desc")
        np["binding_type"] = dict(_EMPTY_BINDING_TYPE, **(p.get("binding_type") or {}))
        np["asynchronous"] = p.get("asynchronous")
        np["constant"] = p.get("constant")
        np["pointer"] = p.get("pointer")
        np["array_type"] = p.get("array_type")
        np["func_type"] = p.get("func_type")
        np["length"] = p.get("length")
        np["root_only"] = p.get("root_only")
        np["parameter_bindings"] = derive_parameter_bindings(p.get("_lang_included"))
        params_out.append(np)
    entry["parameters"] = params_out

    entry["return"]["kind"] = ir["return_kind"]
    entry["return"]["binding_type"] = dict(_EMPTY_BINDING_TYPE, **(ir.get("return_binding_type") or {}))

    entry["tool_integration"]["profiling_name"] = (
        None if ir.get("no_profiling_symbol") else derive_profiling_name(model, ir["name"])
    )

    # Contract requirement #3: semantics.formal is unconditionally OMITTED
    # coming out of Extract -- never a guess, never partial, never a
    # premature null (that's Generate Formal's call to make, once it's
    # actually run -- see docs/overview/glossary.md (Staging schema)). build_null_entry() already leaves it out; restated
    # here so the invariant is visible at the call site, not just implied
    # by "we never touch it."
    assert "formal" not in entry["semantics"]

    flags.extend(ir.get("flags") or [])

    return entry, flags
