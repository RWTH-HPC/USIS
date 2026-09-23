"""
Per-run status/report tracking, shared by every workflow component that
produces partial/flagged output rather than erroring out on the first
imperfect case -- originally built for Extract (workflow/extract/), promoted
here 2026-07-16 when Classify semantics (workflow/classify/) needed the
identical machinery. Always fully PPM- and stage-agnostic; nothing below
assumes which component is using it.

workflow/README.md explicitly flags "malformed source input
and functions with no clean syntactic-field mapping" as a gap this fixes: a
Flag is a side-channel note ("skipped this function", "this field is a
heuristic guess, not a literal read"), collected across a whole run and
written to a component's own report file separately from the entry corpus
itself -- mirroring the assign stage's pattern (a per-entry status alongside
the output, not embedded in the entry itself). Nothing about an entry's
validity depends on its flags; they exist purely so a human doing Review
can triage without reading the full corpus.

Three severities, deliberately distinct rather than collapsed into one
"warning" bucket, because they triage differently:
  - "skipped"        -- no entry was emitted at all for this function.
  - "low_confidence"  -- an entry WAS emitted, but this field's value is a
                         heuristic guess that could be wrong (e.g. every
                         NCCL/NVSHMEM parameters[].direction, derived from
                         const-qualification alone; or Heuristic
                         Classification's naming-convention guesses).
  - "note"            -- a field was left null because no mechanical source
                         exists at all. Distinguished from low_confidence:
                         "we didn't guess" triages differently than
                         "we guessed and might be wrong."
"""

import json
from dataclasses import dataclass, field, asdict

SEVERITIES = ("skipped", "low_confidence", "note")


@dataclass
class Flag:
    entry_key: str | None    # "mpi:mpi_bcast", or None for a whole-run/whole-file flag
    field: str | None        # dotted path this concerns, or None if about the whole entry
    severity: str
    reason: str

    def __post_init__(self):
        if self.severity not in SEVERITIES:
            raise ValueError(f"unknown severity {self.severity!r}; must be one of {SEVERITIES}")


@dataclass
class Report:
    flags: list = field(default_factory=list)
    ppm_counts: dict = field(default_factory=dict)

    def add(self, flag):
        self.flags.append(flag)

    def extend(self, flags):
        self.flags.extend(flags)

    def summary(self):
        entries_skipped = len({f.entry_key for f in self.flags if f.severity == "skipped" and f.entry_key})
        low_confidence_fields = sum(1 for f in self.flags if f.severity == "low_confidence")
        notes = sum(1 for f in self.flags if f.severity == "note")
        return {
            "entries_skipped": entries_skipped,
            "low_confidence_fields": low_confidence_fields,
            "notes": notes,
        }

    def to_dict(self, timestamp):
        return {
            "run": {"timestamp": timestamp, "ppm_counts": self.ppm_counts},
            "summary": self.summary(),
            "flags": [asdict(f) for f in self.flags],
        }

    def write(self, path, timestamp):
        with open(path, "w") as f:
            json.dump(self.to_dict(timestamp), f, indent=2)
            f.write("\n")
