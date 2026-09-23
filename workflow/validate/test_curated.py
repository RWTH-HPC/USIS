"""
Validates every hand-edited curated file against its schema.

The corpus itself has been schema-checked from the beginning; the files that
*govern* the corpus were not. That asymmetry is the gap this closes. A typo in
curated/field-provenance.json silently changes what each stage is allowed to
emit (workflow/staging/derive_schema.py derives every staging schema from it);
a mistyped review status is invisible because nothing consumes review records
yet; a malformed shape only surfaces as a confusing expansion failure later.

What is checked, per file:
  curated/field-provenance.json        -> schemas/field-provenance.schema.json
  curated/shapes/shapes.json           -> schemas/shapes.schema.json
  curated/shapes/seed-assignments.json -> schemas/seed-assignments.schema.json
  curated/supplement/supplement-*.json -> schemas/supplement-input.schema.json
  curated/review/*.review.json         -> schemas/review-record.schema.json

Plus the cross-references a JSON Schema structurally cannot express:
  - every fields[].tier is a key of the `tiers` map it claims membership in
  - shape ids are unique across the catalog
  - every seed assignment's shape_ref names a shape that exists
  - a review record's group ids are unique, and its members are entry-shaped

Not checked here: that provenance paths exist in api-schema.json, or that every
schema leaf has a provenance entry. derive_schema.py already raises
ProvenanceGapError on an uncovered leaf every time it runs, which is stronger
than anything statable in a schema -- see workflow/staging/test_staging_schema.py.

Run directly: python3 workflow/validate/test_curated.py
"""

import glob
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..", "..")

sys.path.insert(0, os.path.join(_ROOT, "workflow", "common"))
from layout import (  # noqa: E402
    FIELD_PROVENANCE_PATH, REVIEW_DIR, SCHEMAS_DIR, SHAPES_DIR, SUPPLEMENT_DIR,
)

sys.path.insert(0, os.path.join(_ROOT, "workflow", "extract"))
from validate_entry import validate_document, ValidationError  # noqa: E402

_ENTRY_KEY_RE = re.compile(r"^[a-z0-9]+:[A-Za-z0-9_{}]+$")


def _load(path):
    with open(path) as f:
        return json.load(f)


def _schema(name):
    return _load(os.path.join(SCHEMAS_DIR, name))


def _rel(path):
    return os.path.relpath(path, _ROOT)


def _check_schema(path, schema, failures):
    """-> the loaded document, or None if it failed to load/validate."""
    try:
        doc = _load(path)
    except (OSError, ValueError) as e:
        failures.append(f"{_rel(path)}: cannot load: {e}")
        return None
    try:
        validate_document(doc, schema)
    except ValidationError as e:
        failures.append(f"{_rel(path)}: {e}")
        return None
    return doc


def _cross_check_provenance(provenance, failures):
    tiers = set(provenance.get("tiers", {}))
    for i, field in enumerate(provenance.get("fields", [])):
        tier = field.get("tier")
        if tier not in tiers:
            failures.append(
                f"field-provenance.json: fields[{i}] ({field.get('path')!r}) has tier {tier!r}, "
                f"which is not one of the documented tiers {sorted(tiers)}")
    paths = [f.get("path") for f in provenance.get("fields", [])]
    dupes = sorted({p for p in paths if paths.count(p) > 1})
    if dupes:
        failures.append(f"field-provenance.json: duplicate field path(s) {dupes} -- "
                        f"whichever appears first silently wins in every lookup")


def _cross_check_shapes(shapes, seed, failures):
    ids = [s.get("id") for s in shapes]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        failures.append(f"shapes.json: duplicate shape id(s) {dupes}")
    known = set(ids)
    if seed:
        for i, a in enumerate(seed.get("assignments", [])):
            ref = a.get("shape_ref")
            if ref not in known:
                failures.append(f"seed-assignments.json: assignments[{i}] references unknown "
                                f"shape {ref!r}")
    for shape in shapes:
        for key in shape.get("motivated_by", []):
            if not _ENTRY_KEY_RE.match(key):
                failures.append(f"shapes.json: {shape.get('id')!r} motivated_by {key!r} is not a "
                                f"'model:function_key' entry key")


def _cross_check_review(path, record, failures):
    label = _rel(path)
    ids = [g.get("group_id") for g in record.get("groups", [])]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        failures.append(f"{label}: duplicate group_id(s) {dupes} -- a decision would apply to both")
    for g in record.get("groups", []):
        for member in g.get("members", []):
            if not _ENTRY_KEY_RE.match(member):
                failures.append(f"{label}: group {g.get('group_id')!r} member {member!r} "
                                f"is not a 'model:function_key' entry key")
                break
        for key in g.get("exceptions", {}):
            if not _ENTRY_KEY_RE.match(key.split("::")[0]):
                failures.append(f"{label}: group {g.get('group_id')!r} exception key {key!r} "
                                f"does not start with a 'model:function_key' entry key")


def run():
    failures = []
    checked = 0

    provenance = _check_schema(FIELD_PROVENANCE_PATH, _schema("field-provenance.schema.json"), failures)
    checked += 1
    if provenance:
        _cross_check_provenance(provenance, failures)

    shapes_schema = _schema("shapes.schema.json")
    shapes = _check_schema(os.path.join(SHAPES_DIR, "shapes.json"), shapes_schema, failures)
    checked += 1
    seed = _check_schema(os.path.join(SHAPES_DIR, "seed-assignments.json"),
                         _schema("seed-assignments.schema.json"), failures)
    checked += 1
    if shapes:
        _cross_check_shapes(shapes, seed, failures)

    supplement_schema = _schema("supplement-input.schema.json")
    for path in sorted(glob.glob(os.path.join(SUPPLEMENT_DIR, "supplement-*.json"))):
        _check_schema(path, supplement_schema, failures)
        checked += 1

    review_schema = _schema("review-record.schema.json")
    for path in sorted(glob.glob(os.path.join(REVIEW_DIR, "*.review.json"))):
        record = _check_schema(path, review_schema, failures)
        checked += 1
        if record:
            _cross_check_review(path, record, failures)

    print(f"{checked} curated file(s) checked.")
    if failures:
        print(f"\n{len(failures)} FAILURE(S):")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("All curated files validate against their schemas, and their cross-references agree.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
