"""
Merges the corpus through two ungated overlay steps, writing a numbered,
cumulative checkpoint file after each one so a human can just open the JSON
and look, rather than needing a lookup tool to reconstruct "what does this
entry look like at stage N":

  0_syntactic-api.json              (Extract, instances/)
  1_syntactic-semantics-api.json    (+ Heuristic Classification)
  2_syntactic-semantics-formal-api.json  (this script -- + formal-assignment proposals)
  3_syntactic-semantics-formal-supplement-api.json  (this script -- + supplement
                                     proposals; still collapsed/generic, one
                                     entry per "{T}" family -- the human-review
                                     level)
  4_final-api.json                  (this script -- 3_ mechanically Concretized,
                                     one concrete entry per type, then every
                                     still-absent field filled with an explicit
                                     null -- see the note below)

0_ through 3_ are all still generic (a type-generic family like
shmem_{T}_put is one entry); only the 3_->4_ step (Concretize) expands each
family to its concrete types. 3_ therefore exists precisely so a human can
review the fully-merged entry once per family, rather than re-reading the
same judgment across every concrete type in 4_ -- see workflow/concretize/
expand_types.py's docstring and the project's "review the generic, not every
concrete type" principle.

Reads and writes instances/ directly, over the full ~980-family corpus.

**Restructured 2026-07-21, project owner's explicit direction.** Two prior
mechanisms are gone, deliberately, "for now":

- **Review gating removed from this chain.** Every proposal used to be
  `confidence="needs_approval"`, gated through a review-decisions.json record
  (`_decision`/`_load_review_decisions`, a DEMO_PROMOTION_POLICY fallback,
  "promoted" vs "promoted_unreviewed" statuses) before it was allowed into
  final-api.json. That machinery is deleted here, not just unused --
  reviewing/approving proposals is still a real, expected step, but it's now
  a separate concern applied *after* this chain produces its best-effort
  merge, not interleaved with generating it. The old review-decisions.json/
  ai-classifications.json/audit-log.json files themselves were removed
  2026-07-21 (later the same day as the restructure) once nothing read them
  anymore -- see git history if the old review record is ever needed again.
- **AI-Assisted Classification as a separate stage** (workflow/classify/
  ai_classify.py) -- retired the same day, folded into supplement.json; see
  curated/field-provenance.json's "supplement" tier entry and
  curated/README.md.

**Final null-fill (2026-07-22, project owner's direction).** 0_ through 3_
preserve Resolution v2's null-vs-absent distinction; 4_ deliberately does
not. No stage writes a "default null" for a field it has no basis to decide
-- absence just persists, and one final step (workflow/concretize/
materialize_nulls.py, run right after Concretize) turns every remaining
absence into the explicit null R1 requires of a shipped entry. Required
NON-nullable fields are the one thing it refuses to invent: they stay absent
and are reported in `unfillable_required_fields`. See that module's
docstring, and docs/overview/glossary.md (Staging schema), for why this lives at the end rather than in the stages.

Both proposal sources (formal assignment, supplement) are applied at face
value -- no confidence gate, no rejection path. `4_final-api.json` reports
every concrete entry (Concretize's output), whether or not it validates
against the strict schema -- validation_errors is an informational
side-channel, not a filter, so a still-incomplete entry (e.g. missing a
not-yet-built field) is still there to look at rather than silently absent.

Run directly: python3 workflow/assemble/assemble.py
"""

import copy
import json
import os
import sys
import datetime
import importlib.util

_HERE = os.path.dirname(__file__)
_ROOT = os.path.join(_HERE, "..", "..")

_LAYOUT_COMMON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common")
sys.path.insert(0, _LAYOUT_COMMON)
from layout import CURATED_DIR, OUT_DIR, SCHEMAS_DIR  # noqa: E402

_SCHEMA_PATH = os.path.join(SCHEMAS_DIR, "api-schema.json")


_INSTANCES = OUT_DIR
_PATHS = {
    "semantics_api": os.path.join(_INSTANCES, "1_syntactic-semantics-api.json"),
    "formal_assignments": os.path.join(CURATED_DIR, "formal-assignments.json"),
    "formal_out": os.path.join(_INSTANCES, "2_syntactic-semantics-formal-api.json"),
    # 3_ is the fully-merged entry still in its collapsed, one-per-family
    # "{T}"-generic form -- the level a human actually reviews (once per
    # family, per the project's core "review the generic, not every concrete
    # type" principle). 4_ is 3_ mechanically concretized.
    "merged_out": os.path.join(_INSTANCES, "3_syntactic-semantics-formal-supplement-api.json"),
    "final_out": os.path.join(_INSTANCES, "4_final-api.json"),
}

_spec = importlib.util.spec_from_file_location(
    "_assemble_validate_entry", os.path.join(_ROOT, "workflow", "extract", "validate_entry.py")
)
_validate_entry_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_validate_entry_mod)
validate_entry = _validate_entry_mod.validate_entry
ValidationError = _validate_entry_mod.ValidationError

sys.path.insert(0, os.path.join(_ROOT, "workflow", "concretize"))
import expand_types  # noqa: E402
import materialize_nulls  # noqa: E402

sys.path.insert(0, os.path.join(_ROOT, "workflow", "common"))
from paths import ABSENT, get_path, set_path  # noqa: E402

sys.path.insert(0, os.path.join(_ROOT, "workflow", "supplement"))
from propose import build_proposals, source_files  # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import array_shape  # noqa: E402



def _apply_formal_assignment(entry, proposal, promotion_log):
    entry_key = proposal["entry_key"]
    outcome = proposal["outcome"]

    if outcome == "no_formal_applicable":
        # semantics.formal is OMITTED coming out of Extract/Classify (see
        # docs/overview/glossary.md (Staging schema)) -- this
        # outcome is Generate Formal actively confirming "genuinely no
        # formal layer applies", so it explicitly writes null here rather
        # than relying on any upstream default.
        entry["semantics"]["formal"] = None
        promotion_log.append({"entry_key": entry_key, "field": "semantics.formal", "status": "confirmed_null"})
        return

    if outcome == "escalate_new_shape":
        promotion_log.append({"entry_key": entry_key, "field": "semantics.formal",
                               "status": "no_candidate", "reason": "escalate_new_shape has no candidate to apply"})
        return

    # outcome == "shape_assigned"
    if proposal.get("expansion") is None:
        promotion_log.append({"entry_key": entry_key, "field": "semantics.formal",
                               "status": "no_candidate", "reason": proposal.get("expansion_error") or "no expansion"})
        return

    entry["semantics"]["formal"] = proposal["expansion"]
    promotion_log.append({"entry_key": entry_key, "field": "semantics.formal",
                           "status": "applied", "shape_ref": proposal["shape_ref"]})


def _apply_field_proposals(entry, entry_key, fields, promotion_log):
    """Applies the supplement projection (workflow/supplement/propose.py's
    build_proposals, run in memory) -- "field_path -> {value, note}" -- onto
    an entry that already has 2_syntactic-semantics-formal-api.json's formal
    overlay applied.

    Re-checks the field's CURRENT value on `entry` right here, immediately
    before writing -- not just trusting propose.py's own eligibility check,
    which computes eligibility against 1_syntactic-semantics-api.json, a
    snapshot taken before this merge pass runs. Without this re-check, a
    formal-assignment value applied a few lines above this loop could in
    principle be silently clobbered by a supplement proposal generated
    against that older snapshot -- exactly the override docs/workflow/
    curated/README.md's precedence rule exists to prevent. No overlap has
    actually happened (formal assignment only ever touches semantics.formal,
    which supplement.json doesn't target), but nothing enforced that
    structurally; this makes the guarantee hold regardless. This check is
    about data correctness (supplement never overrides a real value), not
    about review gating -- it stays even though gating itself is gone."""
    for field_path, proposal in fields.items():
        current = get_path(entry, field_path)
        if current is not ABSENT and current is not None:
            promotion_log.append({
                "entry_key": entry_key, "field": field_path, "status": "skipped_conflict",
                "reason": f"already populated by an earlier proposal in this same merge pass "
                          f"(current value {current!r}) -- supplement never overrides",
            })
            continue
        set_path(entry, field_path, proposal["value"])
        promotion_log.append({"entry_key": entry_key, "field": field_path, "status": "applied",
                               "note": proposal.get("note")})


def _derive_supersedes(entries):
    """Populate relationships.supersedes on every entry, in place.

    The mechanical inverse of relationships.superseded_by, and the reason
    that field is single-valued while this one is an array: supersession is
    many-to-one, so inverting A->B for the whole corpus gives B a list.

    Deliberately derived rather than authored. Hand-maintaining both
    directions of one edge is how a graph desyncs, and there is no judgment
    left to make here once superseded_by is final -- which is why this runs
    at 3_ (after supplement, the only source of a real superseded_by value)
    rather than anywhere earlier. Every entry gets the key, so [] means
    "inverted the corpus, nothing points here", never "not computed".

    Reference form: superseded_by targets are read as bare function_keys
    resolved within the same model (what the corpus actually contains, for
    both this field and relationships.variants) OR as already-qualified
    "model:function_key". Emitted targets are always fully qualified, the
    form the schema documents. Note the corpus's own bare-vs-qualified
    inconsistency for the FORWARD edge is pre-existing and unrelated to
    this field -- logged, not silently normalized here.

    A superseded_by naming an entry that doesn't exist is left out of the
    inverse index rather than fabricating a target entry for it;
    workflow/validate/consistency.py is what reports those as findings.
    """
    for entry in entries.values():
        entry.setdefault("relationships", {})["supersedes"] = []

    for entry_key, entry in entries.items():
        target = (entry.get("relationships") or {}).get("superseded_by")
        if not target:
            continue
        model = entry_key.split(":", 1)[0]
        target_key = target if ":" in target else f"{model}:{target}"
        target_entry = entries.get(target_key)
        if target_entry is None:
            continue  # dangling -- consistency.py's finding to report, not ours to invent
        target_entry["relationships"]["supersedes"].append(entry_key)

    for entry in entries.values():
        entry["relationships"]["supersedes"].sort()


def run():
    with open(_PATHS["semantics_api"]) as f:
        semantics_api = json.load(f)
    with open(_PATHS["formal_assignments"]) as f:
        formal_assignments = {p["entry_key"]: p for p in json.load(f)["proposals"]}
    # The supplement projection runs here, in memory (2026-07-22): which
    # curated supplement values are eligible depends entirely on which fields
    # are still null in this very corpus, so materializing it as a file could
    # only ever produce a stale duplicate of two things this function already
    # holds. Ineligible entries are not dropped silently -- they land in
    # promotion_log below, which is where every other per-field outcome of
    # this merge is already recorded.
    #
    # Only the supplements of models this corpus contains: a build restricted
    # with --ppm would otherwise log every entry of every other model's
    # supplement as "not in the full corpus", records about models it never
    # built, which split/by_model.py then has no file to put in.
    built_models = {entry_key.split(":", 1)[0] for entry_key in semantics_api}
    supplement_proposals, supplement_skipped = build_proposals(
        semantics_api=semantics_api, corpus_label="full corpus", models=built_models)
    with open(_SCHEMA_PATH) as f:
        schema = json.load(f)

    promotion_log = [
        {"entry_key": s_["entry_key"], "field": s_["field"],
         "status": "supplement_ineligible", "reason": s_["reason"]}
        for s_ in supplement_skipped
    ]

    # 2_syntactic-semantics-formal-api.json: 1_ + every formal-assignment
    # proposal applied at face value. Still "{T}"/"{CT}"-generic for any
    # type-generic family -- Concretize only ever runs once, after every
    # proposal source has been applied, not per checkpoint (Heuristic
    # Classification, Generate Formal, and supplement.json all operate on
    # the collapsed entry directly, exactly once per family, not once per
    # concrete type -- see workflow/concretize/expand_types.py's docstring).
    formal_entries = {}
    for entry_key, source_entry in semantics_api.items():
        entry = copy.deepcopy(source_entry)
        formal_proposal = formal_assignments.get(entry_key)
        if formal_proposal is not None:
            _apply_formal_assignment(entry, formal_proposal, promotion_log)
        formal_entries[entry_key] = entry

    os.makedirs(os.path.dirname(_PATHS["formal_out"]), exist_ok=True)
    with open(_PATHS["formal_out"], "w") as f:
        json.dump(formal_entries, f, indent=2, sort_keys=True)
        f.write("\n")

    # 3_syntactic-semantics-formal-supplement-api.json: 2_ + every supplement
    # proposal applied at face value, still collapsed/generic (one entry per
    # "{T}" family, not yet concretized). This is the human-review level --
    # written as a plain {entry_key: entry} dict like 0_/1_/2_ so a reviewer
    # reads each family once, rather than re-reading the same judgment across
    # every concrete type in 4_.
    merged_entries = {}
    for entry_key, source_entry in formal_entries.items():
        entry = copy.deepcopy(source_entry)
        supplement_fields = supplement_proposals.get(entry_key)
        if supplement_fields is not None:
            _apply_field_proposals(entry, entry_key, supplement_fields, promotion_log)
        merged_entries[entry_key] = entry

    # parameters[].length/array_type for every array Extract could not size:
    # needs kind (Classify) and the formal extents (above), so it runs here, on
    # the generic entries, before Concretize copies them per type.
    array_shape.complete_array_shape(merged_entries, promotion_log)

    _derive_supersedes(merged_entries)

    with open(_PATHS["merged_out"], "w") as f:
        json.dump(merged_entries, f, indent=2, sort_keys=True)
        f.write("\n")

    # 4_final-api.json: 3_ mechanically Concretized (each "{T}" family expanded
    # to one concrete entry per type). entries includes every concrete entry
    # regardless of strict-schema validity -- validation_errors records which
    # failed and why, as information, not as a filter.
    typename_ctype_maps = expand_types.load_typename_ctype_maps()
    concrete_entries = expand_types.concretize_corpus(merged_entries, typename_ctype_maps)

    # The very last step, and deliberately only here: every field still
    # absent after every stage has run becomes an explicit null (or [], or a
    # recursed object), satisfying R1 without any earlier stage having had
    # to invent a default null it couldn't justify. 0_ through 3_ keep the
    # null-vs-absent distinction Resolution v2 is built on -- see
    # workflow/concretize/materialize_nulls.py's docstring for why the
    # filling lives at the end rather than field-by-field in the stages.
    # Required non-nullable fields with no value are NOT invented; they stay
    # absent and fall through to validation_errors below, exactly as before.
    unfillable = materialize_nulls.materialize_corpus(concrete_entries, schema)

    validation_errors = {}
    for entry_key, entry in concrete_entries.items():
        try:
            validate_entry(entry, schema)
        except ValidationError as e:
            validation_errors[entry_key] = str(e)

    applied = sum(1 for p in promotion_log if p["status"] == "applied")
    no_candidate = sum(1 for p in promotion_log if p["status"] == "no_candidate")
    skipped_conflict = sum(1 for p in promotion_log if p["status"] == "skipped_conflict")
    confirmed_null = sum(1 for p in promotion_log if p["status"] == "confirmed_null")

    out = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "review_status": (
            "UNGATED -- every formal-assignment and supplement.json proposal is applied at face value, "
            "no review-decisions.json check. Review/approval is a separate step, applied later, not part "
            "of generating this file. See this module's own docstring."
        ),
        "summary": {
            "total_function_families": len(semantics_api),
            "total_concrete_entries_after_concretize": len(concrete_entries),
            "entries_valid_against_strict_schema": len(concrete_entries) - len(validation_errors),
            "entries_failed_validation": len(validation_errors),
            "fields_applied": applied,
            "fields_no_candidate": no_candidate,
            "fields_skipped_conflict": skipped_conflict,
            "formal_confirmed_null": confirmed_null,
            "entries_with_unfillable_required_fields": len(unfillable),
        },
        # Required NON-NULLABLE fields no stage produced a value for -- the
        # one case the final null-fill deliberately refuses to paper over,
        # since there is no null to fall back on and inventing a default
        # would be a guess. Overlaps validation_errors by construction;
        # listed separately because "genuinely incomplete" is a different
        # signal from "malformed".
        "unfillable_required_fields": unfillable,
        "validation_errors": validation_errors,
        "promotion_log": promotion_log,
        "entries": concrete_entries,
    }

    os.makedirs(os.path.dirname(_PATHS["final_out"]), exist_ok=True)
    with open(_PATHS["final_out"], "w") as f:
        json.dump(out, f, indent=2, sort_keys=True)
        f.write("\n")

    print(f"wrote {len(formal_entries)} entries to {_PATHS['formal_out']}")
    print(f"wrote {len(merged_entries)} generic (pre-concretize) entries to {_PATHS['merged_out']}")
    print(f"wrote {len(concrete_entries)} concrete entries "
          f"({len(concrete_entries) - len(validation_errors)} valid against the strict schema) to {_PATHS['final_out']}")
    print(f"fields applied: {applied}, no candidate: {no_candidate}, "
          f"skipped (conflict): {skipped_conflict}, formal confirmed null: {confirmed_null}")
    print(f"strict-schema validation failures: {len(validation_errors)} (still present in 'entries', see validation_errors)")
    return 0


if __name__ == "__main__":
    sys.exit(run())
