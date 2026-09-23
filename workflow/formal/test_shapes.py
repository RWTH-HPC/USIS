"""
Self-contained test harness for the seed shape catalog.

For every golden example in curated/shapes/seed-assignments.json: re-derive the
expansion from curated/shapes/shapes.json via expand()+apply_extra(), diff it
byte-for-byte against the stored expected_expansion, and structurally
validate the result against api-schema.json's $defs/formal.

This is the golden-diff check for the shape catalog. The
algorithm used here -- exact structural equality after expansion -- is
the simplest one that could work; it is NOT claimed to be the final
answer for the real workflow's Validate stage (e.g. it says nothing about
which kinds of field reordering or optional-field variance should be
tolerated for a *proposed*, not hand-authored, expansion). It's exactly
enough to keep this seed catalog and its expander implementation honest
with each other.

Run directly: python3 workflow/formal/test_shapes.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from expand import expand_entry
from validate import validate_formal, validate_shape_template, ValidationError

_LAYOUT_COMMON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common")
sys.path.insert(0, _LAYOUT_COMMON)
from layout import SHAPES_DIR  # noqa: E402

_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
_SHAPES_PATH = os.path.join(SHAPES_DIR, "shapes.json")
_SEED_PATH = os.path.join(SHAPES_DIR, "seed-assignments.json")
# The pinned expansions are a test fixture, not curated content -- they live
# beside this test, and are deliberately never regenerated (see their own
# $comment). Not layout-resolved: a fixture belongs to the test, not to a
# redirectable root.
_EXPANSIONS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "testdata", "expansions.json")


def load_shapes():
    with open(_SHAPES_PATH) as f:
        shapes = json.load(f)
    return {s["id"]: s for s in shapes}, shapes


def load_golden():
    """Rejoins the curated bindings with their pinned expansions, keyed
    'ppm:function' -- the two halves were split 2026-07-22 (assign.py consumes
    the bindings in production; the expansions only ever serve this test)."""
    with open(_SEED_PATH) as f:
        seed = json.load(f)["assignments"]
    with open(_EXPANSIONS_PATH) as f:
        expansions = json.load(f)["expansions"]
    examples = []
    for b in seed:
        key = f"{b['ppm']}:{b['function']}"
        examples.append(dict(b, expected_expansion=expansions.get(key), _key=key,
                             _has_expansion=key in expansions))
    return {"examples": examples, "expansions": expansions}


def run():
    shapes_by_id, shapes = load_shapes()
    golden = load_golden()

    failures = []
    checked = 0

    # 1. Every shape's own id/slots structure is well-formed.
    for shape in shapes:
        try:
            validate_shape_template(shape)
        except ValidationError as e:
            failures.append(f"shape '{shape['id']}': {e}")

    # 2a. Every binding has a pinned expansion, and vice versa -- a binding
    # added without one would silently skip the only correctness check there is.
    for g in golden["examples"]:
        if not g["_has_expansion"]:
            failures.append(f"seed assignment '{g['_key']}' has no pinned expansion in "
                            f"workflow/formal/testdata/expansions.json")
    orphan_expansions = set(golden["expansions"]) - {g["_key"] for g in golden["examples"]}
    for key in sorted(orphan_expansions):
        failures.append(f"pinned expansion '{key}' has no seed assignment in "
                        f"curated/shapes/seed-assignments.json")

    # 2. Every shape referenced by a golden example actually exists.
    referenced_shapes = {g["shape_ref"] for g in golden["examples"]}
    missing_shapes = referenced_shapes - set(shapes_by_id)
    for shape_id in missing_shapes:
        failures.append(f"seed-assignments.json references undefined shape '{shape_id}'")

    # 3. Every shape has at least one golden example (catches an authored-but-unverified shape).
    unexercised = set(shapes_by_id) - referenced_shapes
    for shape_id in unexercised:
        failures.append(f"shape '{shape_id}' has no seed assignment exercising it")

    # 4. Re-expand every golden example and diff against the stored expansion.
    for g in golden["examples"]:
        checked += 1
        label = f"{g['ppm']}:{g['function']} ({g['shape_ref']})"

        shape = shapes_by_id.get(g["shape_ref"])
        if shape is None:
            continue  # already reported above

        if not g["_has_expansion"]:
            continue  # already reported above

        actual = expand_entry(shape, g["bindings"], g.get("extra"))
        expected = g["expected_expansion"]

        if actual != expected:
            failures.append(f"{label}: expand(bindings) != the pinned expansion -- drift between "
                            f"curated/shapes/{{shapes,seed-assignments}}.json and "
                            f"workflow/formal/testdata/expansions.json")
            continue

        try:
            validate_formal(actual)
        except ValidationError as e:
            failures.append(f"{label}: expansion fails validate_formal(): {e}")

    # 5. Every shape records what motivated it (design-by-concrete-example, enforced).
    # Moved into shapes.json itself 2026-07-22 -- a shape's justification travels
    # with the shape, rather than living in the file that happens to bind it.
    for shape in shapes:
        if not shape.get("motivated_by"):
            failures.append(f"shape '{shape['id']}' records no motivated_by -- every shape must "
                            f"name the real function(s) it was derived from")

    print(f"{checked} golden example(s) checked across {len(shapes_by_id)} shape(s).")
    if failures:
        print(f"\n{len(failures)} FAILURE(S):")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("All shapes structurally valid, all golden examples reproduce byte-identically, all shapes exercised.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
