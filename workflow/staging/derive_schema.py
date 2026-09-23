"""
Derives staging-schema variants from api-schema.json + field-provenance.json,
implementing the omission rule of docs/overview/glossary.md (Staging schema)
(2026-07-20; supersedes the Option 3 mechanism this module originally
implemented -- see that doc for the full history).

The problem this solves: api-schema.json has no representation for "not yet
classified" -- every one of its required fields must be a concrete value,
never null, even though the workflow is explicitly staged (Extract populates
only syntactic+derived fields; later stages fill in the rest). Option 3
(the original version of this script) solved the *validity* half of that by
widening not-yet-legitimate fields to also accept null -- but left a real
ambiguity unresolved: a staging `null` ("not yet computed") and a final
`null` ("genuinely not applicable") were indistinguishable in the JSON
itself, once a field like `semantics.memory` or `semantics.formal` already
had a legitimate final-state null.

Option 4 removes the ambiguity instead of coexisting with it: a field not
yet legitimate at a stage is **omitted** from that stage's `required` list
(and therefore may be entirely absent from an emitted entry), not widened
to accept null. A key's *presence* now means "the owning stage has examined
this and decided" (value = its answer; `null` = genuinely N/A / no heuristic
match / no shape fits); a key's *absence* means "not reached yet". This
holds at the leaf level for plain fields and at the whole-object level for
fields whose entire structure belongs to one tier (`semantics.formal`) --
never for `required` itself. Every field's own `type`/`enum` is left exactly
as api-schema.json defines it: no widening, so a field that IS present at
any stage must still conform to the strict final type.

R1 ("all sections always present, nulls explicit") is unaffected for the
*final*, fully-promoted entry -- every field ends up present there, either a
real value or a legitimate null. R1's own documented invocations
(docs/schema/design-conventions.md) were specifically about that final
entry, never about staging completeness -- see docs/overview/glossary.md (Staging schema) for why this isn't a reopening of R1.

This is deliberately NOT a hand-maintained second schema file (rejected: it
drifts silently) and NOT a
relaxation of api-schema.json itself (rejected as Option 1 -- permanently
blurs "null means not-applicable" for the one artifact real consumers
actually read). It is generated from the two files that are already the
source of truth for "which field means what" and "who is allowed to
populate it", so it cannot go stale without the generator itself being
re-run and the checked-in output diffed in review.

Run directly to regenerate: python3 workflow/staging/derive_schema.py --stage post-extract
"""

import argparse
import json
import os
import re
import sys

_LAYOUT_COMMON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common")
sys.path.insert(0, _LAYOUT_COMMON)
from layout import FIELD_PROVENANCE_PATH, SCHEMAS_DIR  # noqa: E402

_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
_SCHEMA_PATH = os.path.join(SCHEMAS_DIR, "api-schema.json")
_PROVENANCE_PATH = FIELD_PROVENANCE_PATH

# Which provenance tiers are considered "legitimately populated" at a given
# workflow stage -- every OTHER tier's fields are dropped from `required`
# wherever they appear (leaf or whole-object). Adding a future stage is one
# more entry here, not new logic.
STAGE_TIERS = {
    "post-extract": frozenset({"syntactic", "derived"}),
    "post-heuristic-classification": frozenset({"syntactic", "derived", "semantic_heuristic"}),
    "post-generate-formal": frozenset({"syntactic", "derived", "formal"}),
}

# ...and which workflow stages (field-provenance.json's own "stage" letter)
# have actually RUN by then. Tier alone is not sufficient:
# `derived` covers both fields Extract computes in-entry at stage B
# (parameters[].parameter_bindings, tool_integration.profiling_name) and
# relationships.supersedes, which inverts superseded_by across the whole
# corpus and therefore cannot exist before stage E. Without this second
# gate, "derived" alone would mark supersedes required at post-extract --
# a field Extract has no way to compute. Both gates must pass.
STAGE_LETTERS = {
    "post-extract": frozenset({"B"}),
    "post-heuristic-classification": frozenset({"B", "C"}),
    "post-generate-formal": frozenset({"B", "D"}),
}


class ProvenanceGapError(Exception):
    """A schema leaf has no corresponding field-provenance.json entry (exact or wildcard)."""


def _exact_tier(path, provenance_fields, attr="tier"):
    for f in provenance_fields:
        if f["path"] == path:
            return f.get(attr)
    return None


def _tier_for(path, provenance_fields, attr="tier"):
    exact = _exact_tier(path, provenance_fields, attr)
    if exact is not None:
        return exact
    candidates = [f for f in provenance_fields if f["path"].endswith(".*") and path.startswith(f["path"][:-1])]
    if candidates:
        candidates.sort(key=lambda f: -len(f["path"]))
        return candidates[0].get(attr)
    return None


def _governing_tier(path, provenance_fields, attr="tier"):
    """The single tier that governs `path` as one wholesale unit, if any --
    independent of whether the base schema also happens to already allow
    `null` there (that's a final-schema nullability concern, orthogonal to
    staging requiredness). Three cases collapse into one check:

      - An exact provenance entry at this path (e.g. "semantics.formal").
      - A wildcard entry matching this path directly, one level up
        (e.g. "bindings.*" matching "bindings.c" itself).
      - No entry at this path, but every provenance entry found NESTED
        beneath it shares exactly one tier (e.g. "semantics.atomic", whose
        only coverage is the single-tier "semantics.atomic.*" wildcard, or
        "relationships.variants", covered only by
        "relationships.variants.*") -- these are decided as one unit even
        though field-provenance.json never names the container path itself.

    Returns None for a genuine mixed-tier container (must be recursed into,
    its own key always stays required) or a path with no coverage at all
    (the caller treats that as a potential gap).

    `attr` selects which provenance attribute is being resolved -- "tier"
    (the default, and what the name says) or "stage", a
    second, independent gate resolved over exactly the same path/wildcard/
    single-valued-descendant rules. See STAGE_LETTERS for why one gate
    stopped being enough.
    """
    direct = _tier_for(path, provenance_fields, attr)
    if direct is not None:
        return direct
    if not path:
        return None
    descendant_tiers = {f.get(attr) for f in provenance_fields if f["path"].startswith(path + ".")}
    if len(descendant_tiers) == 1:
        return next(iter(descendant_tiers))
    return None


def _resolve(node, defs):
    while "$ref" in node:
        node = defs[node["$ref"].split("/")[-1]]
    return node


def _has_null_option(node, defs):
    node = _resolve(node, defs)
    t = node.get("type")
    if t == "null" or (isinstance(t, list) and "null" in t):
        return True
    enum = node.get("enum")
    if isinstance(enum, list) and None in enum:
        return True
    for key in ("anyOf", "oneOf"):
        if key in node:
            for sub in node[key]:
                if _resolve(sub, defs).get("type") == "null":
                    return True
    return False


def derive_staging_schema(schema, provenance, stage):
    """Pure function: schema + provenance + stage name -> derived schema dict.

    Walks every leaf of $defs/entry (resolving $ref/anyOf/oneOf/items,
    following the same dotted-path + trailing-".*"-wildcard convention
    field-provenance.json's own $comment documents -- array items get a
    literal "[]" path segment). For every property, decides whether it
    should stay in its enclosing object's `required` array at this stage:

      - A property with an EXACT provenance entry at its own path (e.g.
        "semantics.formal") is a wholesale unit -- its tier alone decides
        whether the whole subtree stays required; never recursed into.
      - A property with no exact entry but provenance coverage nested
        beneath it (e.g. "semantics.atomic", covered by the
        "semantics.atomic.*" wildcard) is a mixed-tier container: the key
        itself always stays required (structure is always present -- R1),
        but its OWN nested `required` list is trimmed the same way,
        recursively.
      - A property with no exact entry and no nested coverage either uses
        its tier via the nearest wildcard match (e.g. "bindings.c" via
        "bindings.*") as a wholesale unit, same as the first case.
      - A plain object/array container with no tier of its own (identity,
        execution, semantics, parameters[] items, ...) always stays
        required; its own `required` list is trimmed by recursing into its
        properties/items.

    Never widens a field's own `type`/`enum` -- only `required` arrays are
    ever touched. `additionalProperties` is never touched either.

    Raises ProvenanceGapError if a schema leaf has no field-provenance.json
    entry at all (exact or wildcard) -- silently treating an unclassified
    field as "fine to leave required" would be exactly the kind of
    undocumented gap this project's philosophy rejects.
    """
    if stage not in STAGE_TIERS:
        raise ValueError(f"unknown stage {stage!r}; known stages: {sorted(STAGE_TIERS)}")

    valid_tiers = STAGE_TIERS[stage]
    valid_stages = STAGE_LETTERS[stage]
    defs = schema["$defs"]
    provenance_fields = provenance["fields"]

    out_defs = json.loads(json.dumps(defs))  # deep copy; we mutate out_defs, not defs

    def walk(node, out_node, path, required_here):
        """Returns True if `path` should remain in its parent's `required`
        list, False if it should be dropped (not-yet-legitimate tier at
        this stage). If `required_here` is False, there's nothing to
        decide -- the field is already optional upstream in the base
        schema, so its presence isn't this function's concern.

        Checks `_governing_tier` FIRST, before looking at the node's own
        shape at all -- whether a path is a wholesale, all-or-nothing unit
        is a fact about field-provenance.json's tiering, not about whether
        the base schema also happens to already allow `null` there. Only
        once no single tier governs the whole path does this fall through
        to structural recursion (object properties / array items).
        """
        if not required_here:
            return True

        governing = _governing_tier(path, provenance_fields)
        if governing is not None:
            # Both gates must pass: the field's tier must be one this stage
            # can legitimately populate, AND its owning workflow stage must
            # already have run. See STAGE_LETTERS.
            governing_stage = _governing_tier(path, provenance_fields, "stage")
            return governing in valid_tiers and (governing_stage is None or governing_stage in valid_stages)

        node = _resolve(node, defs)
        out_node_resolved = out_node
        while "$ref" in out_node_resolved:
            out_node_resolved = out_defs[out_node_resolved["$ref"].split("/")[-1]]

        # No single governing tier: either a mixed-tier container (its own
        # key always stays required; recurse to trim its inner `required`
        # list) or a genuine gap. Unwrap nullable-in-place anyOf/oneOf
        # wrapping first if present, purely to reach the real object shape.
        if _has_null_option(node, defs) and ("anyOf" in node or "oneOf" in node):
            key = "anyOf" if "anyOf" in node else "oneOf"
            for branch, out_branch in zip(node[key], out_node_resolved[key]):
                if _resolve(branch, defs).get("type") != "null":
                    walk(branch, out_branch, path, True)
            return True

        t = node.get("type")
        if t == "object" or "properties" in node:
            required_list = set(node.get("required", []))
            new_required = []
            for name, sub in node.get("properties", {}).items():
                p = f"{path}.{name}" if path else name
                child_required = name in required_list
                if walk(sub, out_node_resolved["properties"][name], p, child_required) and child_required:
                    new_required.append(name)
            out_node_resolved["required"] = new_required
            return True

        if t == "array":
            items = node.get("items")
            if items:
                resolved_items = _resolve(items, defs)
                items_are_structured = resolved_items.get("type") == "object" or "properties" in resolved_items
                if items_are_structured:
                    out_items = out_node_resolved.get("items")
                    walk(items, out_items, f"{path}[]", True)
                    return True
                # Array of scalars with no governing tier found above either --
                # fall through, which will raise a ProvenanceGapError since
                # there's nowhere left to look.

        # Genuine scalar leaf (or array-of-scalars falling through above)
        # with no governing tier anywhere -- a real, undocumented gap.
        raise ProvenanceGapError(
            f"schema leaf {path!r} has no field-provenance.json entry "
            f"(exact or wildcard, at this path or beneath it) -- cannot "
            f"determine staging requiredness"
        )

    walk(defs["entry"], out_defs["entry"], "", True)

    derived = json.loads(json.dumps(schema))
    derived["$defs"] = out_defs
    derived["$id"] = re.sub(r"\.json$", f".staging-{stage}.json", schema["$id"])
    derived["$comment"] = (
        f"MECHANICALLY GENERATED by workflow/staging/derive_schema.py --stage {stage}. "
        f"Do not hand-edit -- regenerate via the script and let the diff show what changed. "
        f"Source of truth: curated/schemas/api-schema.json + curated/field-provenance.json. "
        f"Valid tiers at this stage: {sorted(valid_tiers)}; valid workflow stages: "
        f"{sorted(valid_stages)} (both gates must pass). Fields outside these are "
        f"OMITTED (dropped from `required`), not null-widened -- see this module's own "
        f"docstring and docs/overview/glossary.md (Staging schema). "
        + schema.get("$comment", "")
    )
    return derived


def staging_schema_for(stage, schema_path=None, provenance_path=None):
    """Derive a stage's staging schema in memory. This is how the workflow
    actually gets one: the derivation is a pure function of two curated files
    and takes ~0.2s, so every stage derives its own at startup rather than
    reading a checked-in copy that could go stale. The CLI below exists to
    print one for a human to read, not to feed the pipeline."""
    with open(schema_path or _SCHEMA_PATH) as f:
        schema = json.load(f)
    with open(provenance_path or _PROVENANCE_PATH) as f:
        provenance = json.load(f)
    return derive_staging_schema(schema, provenance, stage)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True, choices=sorted(STAGE_TIERS),
                        help="which workflow stage's staging schema to derive")
    parser.add_argument("--schema", default=_SCHEMA_PATH,
                        help="the full schema to derive from (default: curated/schemas/api-schema.json)")
    parser.add_argument("--provenance", default=_PROVENANCE_PATH,
                        help="field-provenance.json, which decides who owns each field "
                             "(default: curated/field-provenance.json)")
    parser.add_argument("--out", default=None,
                        help="write the derived schema here instead of stdout. Nothing in the "
                             "workflow reads such a file: every stage derives its own schema in "
                             "memory via staging_schema_for(), so there is no checked-in copy to "
                             "go stale. Use this only to keep one around for inspection.")
    args = parser.parse_args()

    with open(args.schema) as f:
        schema = json.load(f)
    with open(args.provenance) as f:
        provenance = json.load(f)

    derived = derive_staging_schema(schema, provenance, args.stage)

    if not args.out:
        json.dump(derived, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    with open(args.out, "w") as f:
        json.dump(derived, f, indent=2)
        f.write("\n")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
