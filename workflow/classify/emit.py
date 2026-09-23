"""
Heuristic Classification's assembly layer -- the analog of workflow/
extract/emit.py's assemble_entry, but for a different field-ownership set
and a different starting point (a full entry Extract already produced, not
a null skeleton).

Contract (workflow/README.md):
  1. every output entry is the corresponding syntactic-api.json entry,
     structurally unchanged;
  2. only the 13 Heuristic-Classification-owned field paths are ever
     overwritten, and only when a heuristic actually produced a value --
     everything else (the 23 AI-Assisted Classification fields,
     semantics.formal, all syntactic fields) passes through byte-for-byte
     from the source entry;
  3. semantics.atomic (the parent object) is only ever constructed when the
     function was recognized as atomic-shaped at all -- for every other
     entry it's left exactly as Extract wrote it (null), never speculatively
     set to an all-null 3-key object.

Flagging policy (deliberately simpler than it might first look): a
low_confidence flag is raised automatically, once, for every value a
heuristic actually guessed (mirrors Extract's own _apply_confident). No
per-entry "note" flag is raised when a heuristic simply finds nothing to
match -- that's the expected, common case for a heuristic covering a
necessarily small slice of naming conventions, not an exceptional one (the
same distinction Extract itself draws: it doesn't flag its ~41 out-of-scope
fields on every entry either). The one systemic gap worth a human's
attention -- AI-Assisted Classification's 23 fields not being built at all
-- is recorded once, as a single whole-run note, by workflow/classify/cli.py,
not repeated per entry.
"""

import copy
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common.status import Flag  # noqa: F401,E402
from common.ir import unwrap  # noqa: E402


def _apply_confident(entry_key, field_path, value, flags):
    if value is None:
        return None
    plain, confidence, note = unwrap(value)
    if confidence == "needs_approval":
        # Heuristic Classification only ever produces "static"/"pattern"
        # values, never AI-drafted ones. Seeing this here would mean AI-
        # Assisted Classification code started reusing this function directly
        # instead of routing its proposals
        # into a separate review-queue file, silently shipping an unapproved
        # guess -- exactly what "needs_approval" exists to prevent. See
        # workflow/common/ir.py's docstring and docs/workflow/
        # workflow/README.md.
        raise ValueError(f"{entry_key}.{field_path}: confidence='needs_approval' must never reach _apply_confident")
    if confidence == "pattern":
        flags.append(Flag(entry_key=entry_key, field=field_path, severity="low_confidence", reason=note or "heuristic guess"))
    return plain


def _qualify(model, function_key):
    """Bare function_key -> "model:function_key". None passes through.

    Idempotent: an already-qualified reference is returned unchanged, so
    this is safe to apply at any point a value might have been qualified
    upstream. Cross-PPM references are therefore expressible -- nothing here
    forces the target into `model`, it only supplies the default when the
    reference doesn't name one.
    """
    if function_key is None or ":" in function_key:
        return function_key
    return f"{model}:{function_key}"


def assemble_classified_entry(source_entry, ir):
    """(source_entry, ir) -> (entry, flags). Pure function, no I/O.

    ir is a flat dict: {"model", "function_key", "flags": [...],
    "identity.api_group", "execution.blocking", "execution.execute_once",
    "execution.collective", "execution.launch", "execution.gpu_scope", "execution.stages",
    "execution.procedure_class": Confident|None each;
    "semantics.atomic": {"operation","fetch","compare"} | None;
    "relationships.variants": {6 keys} | None;
    "return.value_kind": Confident|None;
    "parameters": [{"kind","not_null"}, ...] aligned positionally to
    source_entry["parameters"]} -- see workflow/classify/mpi/classify_mpi.py
    for a concrete producer.
    """
    model = ir["model"]
    function_key = ir["function_key"]
    entry_key = f"{model}:{function_key}"
    flags = list(ir.get("flags") or [])

    entry = copy.deepcopy(source_entry)

    entry["identity"]["api_group"] = _apply_confident(entry_key, "identity.api_group", ir.get("identity.api_group"), flags)

    # The owned fields written CONDITIONALLY rather than unconditionally.
    # api-schema.json makes execution.blocking, execution.execute_once and
    # execution.collective required, non-nullable booleans -- alone among this
    # stage's fields, they have no null to fall back on -- so "no answer" cannot be expressed as
    # null here the way it is for launch/gpu_scope/stages/procedure_class.
    # Leaving the key absent is the correct expression of that state:
    # Resolution v2 already gives absence the meaning "not decided",
    # workflow/concretize/materialize_nulls.py reports such a field as
    # genuinely unfillable rather than inventing `false`, and assemble.py
    # surfaces it through validation_errors. In practice every PPM's
    # classifier answers for every entry (each standard either defines the
    # axis by complement or states the restriction outright -- see each
    # _blocking and _execute_once docstring), so these arms are a contract,
    # not a live path.
    for _field in ("blocking", "execute_once", "collective"):
        _value = _apply_confident(entry_key, f"execution.{_field}", ir.get(f"execution.{_field}"), flags)
        if _value is not None:
            entry["execution"][_field] = _value

    entry["execution"]["launch"] = _apply_confident(entry_key, "execution.launch", ir.get("execution.launch"), flags)
    entry["execution"]["gpu_scope"] = _apply_confident(entry_key, "execution.gpu_scope", ir.get("execution.gpu_scope"), flags)
    entry["execution"]["stages"] = _apply_confident(entry_key, "execution.stages", ir.get("execution.stages"), flags)
    entry["execution"]["procedure_class"] = _apply_confident(entry_key, "execution.procedure_class", ir.get("execution.procedure_class"), flags)

    atomic_ir = ir.get("semantics.atomic")
    if atomic_ir is not None:
        entry["semantics"]["atomic"] = {
            "operation": _apply_confident(entry_key, "semantics.atomic.operation", atomic_ir.get("operation"), flags),
            "fetch": _apply_confident(entry_key, "semantics.atomic.fetch", atomic_ir.get("fetch"), flags),
            "compare": _apply_confident(entry_key, "semantics.atomic.compare", atomic_ir.get("compare"), flags),
        }
    # else: non-atomic-shaped function -- leave entry["semantics"]["atomic"]
    # exactly as Extract wrote it (null). Heuristic Classification has no
    # opinion here; forcing an all-null 3-key object would falsely imply
    # "examined, confirmed non-atomic" -- that classification is
    # the job of whichever stage populates semantics.collective/point_to_point/
    # one_sided (there is no separate operation-class field: which sub-object
    # is non-null is the classification).

    variants_ir = ir.get("relationships.variants")
    if variants_ir is not None:
        # Written wholesale, all 6 keys at once (matching semantics.atomic's
        # pattern below) rather than subscripted into a pre-existing dict --
        # relationships.variants is omitted entirely by Extract now (see
        # docs/overview/glossary.md (Staging schema)), so
        # there's no pre-existing dict to subscript into. Keys the heuristic
        # found no evidence for are explicitly null, not missing -- the
        # schema requires all 6 present together once this key exists at
        # all (each individually nullable).
        #
        # Qualified here, not in the four per-PPM classifiers (2026-07-22):
        # every cross-entry reference in a shipped entry is
        # "model:function_key", the form api-schema.json documents and
        # workflow/validate/consistency.py now enforces. The classifiers
        # match bare names against their own PPM's symbol set, which is the
        # right thing for them to do -- this is the one place a name stops
        # being a lookup key and becomes a reference, so it is the one place
        # that has to add the model. Doing it in all four classifiers
        # instead would be four chances to forget.
        entry["relationships"]["variants"] = {
            key: _qualify(model, _apply_confident(entry_key, f"relationships.variants.{key}", variants_ir.get(key), flags))
            for key in ("nonblocking", "blocking", "persistent", "neighborhood", "host", "gpu")
        }

    # Written unconditionally, like parameters[].kind below and for the same
    # reason: every entry's return is examined, so null is an answer (not a
    # value, or a value with no fitting kind), not a skipped field.
    entry["return"]["value_kind"] = _apply_confident(entry_key, "return.value_kind", ir.get("return.value_kind"), flags)

    # Written unconditionally (not "only when found"): Heuristic
    # Classification examines every parameter of every entry, so by the
    # time this runs, both fields are "considered" for every parameter --
    # null is a legitimate, examined answer (no heuristic matched), not a
    # sign this parameter was skipped. _apply_confident already treats a
    # None input as a safe no-op no-flag pass-through.
    for i, p_ir in enumerate(ir.get("parameters") or []):
        if i >= len(entry["parameters"]):
            break
        entry["parameters"][i]["kind"] = _apply_confident(entry_key, f"parameters[{i}].kind", p_ir.get("kind"), flags)
        entry["parameters"][i]["constraints"]["not_null"] = _apply_confident(
            entry_key, f"parameters[{i}].constraints.not_null", p_ir.get("not_null"), flags
        )

    return entry, flags
