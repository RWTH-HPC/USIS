"""
Builds the review records for the two curated artifacts that no stage produces:
the shape catalog and the supplement inputs.

The assignment record is written by the stage that generates the proposals
(workflow/formal/assign.py). These two have no such stage -- both files are
hand-authored -- so their review state is scaffolded here instead. All three go
through workflow/review/record.py, so a decision is treated identically
whichever artifact it belongs to.

Why they need a record at all, given a human wrote the files: authorship is not
review. The Author Shapes process specifies "human review, every time, no
sampling" but nothing recorded whether that happened for a given shape. And
supplement values are `needs_approval` by construction (docs/workflow/
curated/README.md) yet promote into entries unreviewed by default -- 2146
values today, ~97% of them method=general_knowledge, i.e. no citation to check
them against. That is the largest body of unverified content in the corpus, and
until now the only artifact with no way to record that anyone had looked.

Grouping, per artifact -- the unit is whatever makes two things "the same
decision" to a reviewer:

  shapes      one group per shape. 27 units: small enough to review outright,
              and a shape is exactly what a reviewer signs off on (its slots,
              its template, its own justification, its seed assignments).
  supplement  one group per (field_path, method). 180 units out of 2146 values:
              "MPI's identity.since, from general knowledge" is one judgment
              made 524 times, not 524 judgments. Deliberately not keyed by PPM
              too -- that yields 347 groups and splits one judgment across four
              files for no reviewer benefit.

Run: python3 workflow/review/scaffold.py [--shapes] [--supplement]
     (no flag = both)
"""

import argparse
import collections
import glob
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..", "..")

sys.path.insert(0, os.path.join(_ROOT, "workflow", "common"))
from layout import REVIEW_DIR, SHAPES_DIR, SUPPLEMENT_DIR  # noqa: E402

sys.path.insert(0, _HERE)
from record import BOILERPLATE, merge_and_write  # noqa: E402

_SHAPES_RECORD = os.path.join(REVIEW_DIR, "shapes.review.json")
_SUPPLEMENT_RECORD = os.path.join(REVIEW_DIR, "supplement.review.json")


def _load(path):
    with open(path) as f:
        return json.load(f)


def build_shape_groups():
    shapes = _load(os.path.join(SHAPES_DIR, "shapes.json"))
    seed = _load(os.path.join(SHAPES_DIR, "seed-assignments.json"))

    by_shape = collections.defaultdict(list)
    for a in seed["assignments"]:
        by_shape[a["shape_ref"]].append(a)

    groups = []
    for shape in sorted(shapes, key=lambda s: s["id"]):
        examples = by_shape.get(shape["id"], [])
        groups.append({
            # The shape id IS the decision's identity: rename a shape and the
            # decision correctly comes back unreviewed, because a renamed shape
            # is a different thing to sign off on.
            "group_id": shape["id"],
            "slots": [f"{s['name']}: {s['kind']}" + ("" if not s.get("optional") else " (optional)")
                      for s in shape["slots"]],
            "justification": shape.get("$comment"),
            "member_count": len(examples),
            "members": [f"{ex['ppm']}:{ex['function']}" for ex in examples],
            # One seed assignment inline: the concrete case a reviewer judges
            # the template by. The rest are in curated/shapes/seed-assignments.json.
            "exemplar": examples[0] if examples else None,
        })
    return groups


def build_supplement_groups():
    values = []
    for path in sorted(glob.glob(os.path.join(SUPPLEMENT_DIR, "supplement-*.json"))):
        ppm = os.path.splitext(os.path.basename(path))[0][len("supplement-"):]
        for function_key, fields in _load(path).items():
            for field_path, entry in fields.items():
                values.append((ppm, function_key, field_path, entry))

    grouped = collections.defaultdict(list)
    for ppm, function_key, field_path, entry in values:
        grouped[(field_path, entry["method"])].append((ppm, function_key, entry))

    groups = []
    for (field_path, method), members in sorted(grouped.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        ppm_counts = collections.Counter(ppm for ppm, _, _ in members)
        exemplar_ppm, exemplar_fn, exemplar_entry = members[0]
        groups.append({
            "group_id": f"{field_path}:{method}",
            "field_path": field_path,
            "method": method,
            "ppms": dict(sorted(ppm_counts.items())),
            "member_count": len(members),
            "members": [f"{ppm}:{fn}" for ppm, fn, _ in members],
            "exemplar": {
                "entry_key": f"{exemplar_ppm}:{exemplar_fn}",
                "value": exemplar_entry.get("value"),
                "source_url": exemplar_entry.get("source_url"),
                "note": exemplar_entry.get("note"),
            },
        })
    return groups


def scaffold_shapes():
    groups = build_shape_groups()
    summary = merge_and_write(
        path=_SHAPES_RECORD,
        reviews="curated/shapes/shapes.json",
        groups=groups,
        comment=(
            "Review record for the shape catalog. One group per shape -- the unit a reviewer "
            "actually signs off on: its slots, its own justification ($comment in shapes.json), "
            "and the seed assignments that exercise it. group_id is the shape id, so "
            "renaming a shape correctly returns it to unreviewed. Authorship is not review: the "
            "Author Shapes process specifies human review of every shape, and this is where that "
            "having happened is recorded. " + BOILERPLATE),
    )
    print(f"shapes: {summary['groups']} shape(s) ({summary['reviewed']} carrying an existing "
          f"decision, {summary['new']} new, {summary['orphaned']} orphaned) -> {_SHAPES_RECORD}")


def scaffold_supplement():
    groups = build_supplement_groups()
    summary = merge_and_write(
        path=_SUPPLEMENT_RECORD,
        reviews="curated/supplement/supplement-<ppm>.json",
        groups=groups,
        comment=(
            "Review record for the supplement inputs. One group per (field_path, method) -- one "
            "judgment call, however many times it was applied: 'identity.since from general "
            "knowledge' is a single decision made 524 times, not 524 decisions. Each group "
            "carries every member entry key and one exemplar value with its note and citation. "
            "This is the corpus's largest body of unverified content: supplement values are "
            "needs_approval by construction yet promote unreviewed by default, and ~97% carry "
            "method=general_knowledge, meaning there is no citation to check them against -- only "
            "a human who knows the PPM. " + BOILERPLATE),
    )
    print(f"supplement: {summary['groups']} group(s) covering {summary['covered']} value(s) "
          f"({summary['reviewed']} carrying an existing decision, {summary['new']} new, "
          f"{summary['orphaned']} orphaned) -> {_SUPPLEMENT_RECORD}")


def run(argv=None):
    parser = argparse.ArgumentParser(
        description="Scaffold or refresh the review records for the hand-authored curated "
                    "artifacts. Existing decisions are preserved; only the groups are rebuilt.")
    parser.add_argument("--shapes", action="store_true", help="only the shape catalog record")
    parser.add_argument("--supplement", action="store_true", help="only the supplement record")
    args = parser.parse_args(argv)

    both = not (args.shapes or args.supplement)
    if args.shapes or both:
        scaffold_shapes()
    if args.supplement or both:
        scaffold_supplement()
    return 0


if __name__ == "__main__":
    sys.exit(run())
