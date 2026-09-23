"""
The one implementation of "merge review decisions forward".

Three artifacts now carry a review record (curated/review/*.review.json), and
each groups its proposals differently -- see docs/workflow/review-records.md:

    formal-assignments  by decision pattern   (outcome + shape_ref + rationale)
    shapes              by shape              (one group per catalog shape)
    supplement          by judgment call      (field_path + sourcing method)

What must NOT differ between them is what happens to a human's decision when
the groups are regenerated, which is why that half lives here rather than
being written three times: a group whose id still exists keeps its status,
reason, reviewed_at and exceptions verbatim; a group that has disappeared
moves to `orphaned_decisions` with a timestamp rather than being deleted; and
a group that is new comes back `unreviewed`. A reviewed judgment is never
silently dropped, and never silently carried onto something nobody read.

Group identity is the caller's job, because what makes two proposals "the same
decision" is artifact-specific. The rule each caller follows is the same one
though: derive the id from the substance of the decision, so that if the
substance changes the id changes with it and the group comes back unreviewed.
"""

import datetime
import json
import os

STATUSES = ("unreviewed", "approved", "withheld")

# The hand-edited half of a group. Regeneration rebuilds everything else.
DECISION_FIELDS = ("status", "reason", "reviewed_at", "exceptions")


def _blank_decision():
    return {"status": "unreviewed", "reason": None, "reviewed_at": None, "exceptions": {}}


def merge_and_write(path, reviews, groups, comment, generated_at=None):
    """Write `groups` to `path` as a review record, preserving any decisions
    already recorded there.

    `groups` are dicts carrying at least `group_id`, `members` and
    `member_count`; their decision fields are filled in here, never by the
    caller. Returns a summary dict for the caller to print.
    """
    generated_at = generated_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    previous = {}
    orphaned_carried = []
    if os.path.exists(path):
        with open(path) as f:
            old = json.load(f)
        previous = {g["group_id"]: g for g in old.get("groups", [])}
        orphaned_carried = old.get("orphaned_decisions", [])

    reviewed = new = 0
    for group in groups:
        prior = previous.pop(group["group_id"], None)
        if prior and prior.get("status") in STATUSES and prior["status"] != "unreviewed":
            for field in DECISION_FIELDS:
                group[field] = prior.get(field, _blank_decision()[field])
            reviewed += 1
        else:
            group.update(_blank_decision())
            new += 1

    orphaned = orphaned_carried + [
        dict(g, orphaned_at=generated_at) for g in previous.values()
        if g.get("status") in ("approved", "withheld")
    ]

    record = {
        "$comment": comment,
        "reviews": reviews,
        "generated_at": generated_at,
        "status_vocabulary": list(STATUSES),
        "summary": {
            "groups": len(groups),
            "groups_reviewed": reviewed,
            "groups_unreviewed": new,
            "proposals_covered": sum(g["member_count"] for g in groups),
            "proposals_in_reviewed_groups": sum(
                g["member_count"] for g in groups if g["status"] != "unreviewed"),
        },
        "groups": groups,
        "orphaned_decisions": orphaned,
    }

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(record, f, indent=2, sort_keys=True)
        f.write("\n")

    return {"groups": len(groups), "reviewed": reviewed, "new": new,
            "orphaned": len(orphaned), "covered": record["summary"]["proposals_covered"]}


BOILERPLATE = (
    "The `groups` list is regenerated; the `status`/`reason`/`reviewed_at`/`exceptions` fields "
    "on each group are HAND-EDITED and are preserved verbatim across regenerations. Set status "
    "to 'approved' or 'withheld' after reading a group's exemplar; use `exceptions` "
    "(entry_key -> {status, reason}) for members that deviate from their group's decision. "
    "A group that disappears moves to orphaned_decisions rather than being dropped. Nothing "
    "consumes this yet: the build chain has been ungated since 2026-07-21, so this records a "
    "human judgment rather than gating output. See docs/workflow/review-records.md."
)
