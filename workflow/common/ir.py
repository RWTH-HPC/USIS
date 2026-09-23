"""
Confident: a value wrapper shared by every workflow component that derives
some fields by heuristic rather than reading them literally off a source --
originally built for Extract (workflow/extract/ir.py), promoted here
2026-07-16 when Classify semantics (workflow/classify/) needed the identical
wrapper for its own naming-convention/co-located-flag guesses. Fully generic
-- nothing below is specific to any one component's IR shape (each
component's own required-key list and field vocabulary stay in that
component's own ir.py, e.g. workflow/extract/ir.py's REQUIRED_IR_KEYS /
LANG_INCLUSION_KEYS).

`Confident` wraps a value that wasn't read literally off the source. Its
`confidence` field is one of three values -- named by *how* the value was
derived, not by a vague magnitude, matching this project's general
preference for closed, meaningful vocabularies over numeric scales
(curated/field-provenance.json's own tiers follow the same naming style):

  - "static"        -- deterministically certain, not a guess at all (e.g.
                        NCCL/NVSHMEM's execution.launch="cpu": guaranteed by
                        Extract's scope, not inferred per-function). Ships
                        into the entry immediately, no flag, never reviewed.
  - "pattern"        -- derived from a recognized naming/structural
                        convention (e.g. MPI's I-prefix, SHMEM's atomic-
                        suffix naming) that's reliable but not infallible.
                        Ships into the entry immediately (trusted enough to
                        use automatically), and the consuming component's
                        emit.py raises a status.Flag(severity="low_confidence")
                        for optional human spot-checking -- not a blocking
                        review requirement.
  - "needs_approval" -- proposed by an LLM from open-ended interpretation
                        (prose reading, or shape-assignment matching), with
                        no structural guarantee. Must NEVER be written into
                        a shipped entry directly -- the field stays null
                        (an honest gap) until a human reviews the proposal
                        and promotes it. See docs/workflow/
                        workflow/README.md for the review-
                        queue mechanism this drives (not yet built, since
                        nothing produces "needs_approval" values yet).

A bare (non-Confident) value means "read directly from source, no
derivation involved at all."
"""

from collections import namedtuple

CONFIDENCE_LEVELS = ("static", "pattern", "needs_approval")

_ConfidentBase = namedtuple("Confident", ["value", "confidence", "note"])


class Confident(_ConfidentBase):
    __slots__ = ()

    def __new__(cls, value, confidence, note):
        if confidence not in CONFIDENCE_LEVELS:
            raise ValueError(f"unknown confidence {confidence!r}; must be one of {CONFIDENCE_LEVELS}")
        return super().__new__(cls, value, confidence, note)


def unwrap(value):
    """(value_or_Confident) -> (plain_value, confidence_or_None, note_or_None)."""
    if isinstance(value, Confident):
        return value.value, value.confidence, value.note
    return value, None, None
