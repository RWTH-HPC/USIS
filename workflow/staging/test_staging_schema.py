"""
Derivation check for the staging schemas.

There are no checked-in staging-schema files to drift anymore (2026-07-22):
every stage derives its own in memory at startup via
derive_schema.staging_schema_for(), so "someone edited api-schema.json and
forgot to regenerate" is structurally impossible rather than something a test
has to catch. What is still worth checking is that the derivation succeeds for
every stage the workflow knows about and produces a usable schema rather than a
degenerate one -- a ProvenanceGapError, or a silently field-less result, would
break every stage's validation at once.

Run directly: python3 workflow/staging/test_staging_schema.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from derive_schema import STAGE_TIERS, ProvenanceGapError, staging_schema_for


def _entry_required(schema):
    return schema.get("$defs", {}).get("entry", {}).get("required", [])


def run():
    failures = []
    checked = 0

    for stage in sorted(STAGE_TIERS):
        checked += 1
        try:
            derived = staging_schema_for(stage)
        except ProvenanceGapError as e:
            failures.append(f"stage '{stage}': derivation raised ProvenanceGapError: {e}")
            continue
        except Exception as e:  # noqa: BLE001 -- any failure here breaks every stage at once
            failures.append(f"stage '{stage}': derivation raised {type(e).__name__}: {e}")
            continue

        if not derived.get("$defs"):
            failures.append(f"stage '{stage}': derived schema has no $defs")
        if not _entry_required(derived):
            failures.append(f"stage '{stage}': derived entry has an empty `required` list -- "
                            f"a schema that requires nothing validates everything")
        try:
            json.dumps(derived)
        except (TypeError, ValueError) as e:
            failures.append(f"stage '{stage}': derived schema is not JSON-serializable: {e}")

    print(f"{checked} stage(s) checked.")
    if failures:
        print(f"\n{len(failures)} FAILURE(S):")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("All known stages derive cleanly into a non-degenerate schema.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
