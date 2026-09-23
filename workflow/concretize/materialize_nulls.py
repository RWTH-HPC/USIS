"""
The very last step in the chain: turn every still-absent field into an
explicit null, so the shipped artifact satisfies R1 ("all sections always
present, nulls explicit") without any earlier stage having to invent a
default null it has no basis for.

Why this exists (project owner's direction, 2026-07-22)
-------------------------------------------------------
The staging rule (docs/overview/glossary.md (Staging schema)) draws a hard line
through the staged corpus: a key's PRESENCE means "the owning stage
examined this and decided", a key's ABSENCE means "not reached yet". That
line is what makes a staged `null` trustworthy, and it stays exactly as it
was for 0_ through 3_.

But it left an awkward pressure at the edges. A field whose owning stage
has nothing to say -- no signal, no heuristic, no source text -- forced a
choice between two bad options: leave it absent forever (and never satisfy
R1), or have that stage write a "default null" it cannot actually justify.
The second option was tried once, for relationships.superseded_by, and it
is what this module replaces: a stage writing null purely so the field
would be present is a placeholder wearing a considered answer's clothes,
which is precisely what Resolution v2 exists to prevent. Worse, it does not
generalize -- doing it field by field means every future field with a weak
signal gets its own bespoke "write null here" line in whichever stage
happens to own it.

So the null-filling moves to one place, at the end, applied uniformly:

  - 0_ .. 3_ keep the null/absent distinction intact. 3_ remains the
    artifact where a reviewer can still read "nobody has answered this"
    (absent) as distinct from "answered, and the answer is nothing" (null).
  - 4_ (the final artifact) is where R1 takes over: every remaining absence
    becomes an explicit null, once, mechanically, with no stage having to
    pretend it decided something.

This deliberately collapses the distinction in 4_. That is the point, not a
regression: 4_ is the shipped form, and the schema's own contract for a
shipped entry has always been that null means "not applicable" -- consumers
were never given the absent state to read in the first place. 3_ is one
file away for anyone who needs to know which nulls were considered answers.

What gets written
-----------------
Filling is driven by the strict schema, never guessed:

  - the field admits null            -> null
  - the field is an array            -> []
  - the field is an object           -> {} recursed, so its own required
                                        keys materialize the same way
  - anything else (a required
    non-nullable scalar/enum)        -> LEFT ABSENT, path reported

That last case is the honest one and the reason this returns a report
rather than just mutating. A required non-nullable boolean has no null to
fall back on, so an entry missing one is genuinely incomplete -- inventing
`false` there would be exactly the "plausible-looking wrong output" the
project's philosophy rejects. Those paths stay absent and surface through
assemble.py's existing validation_errors, unchanged.

Nullability is decided by the same two helpers workflow/staging/
derive_schema.py already uses to decide it (_resolve / _has_null_option),
imported rather than reimplemented -- if the two ever disagreed about what
"admits null" means, the staging schemas and the final fill would diverge
silently, which is the sort of drift this project keeps out of its tooling
by construction.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "staging"))
from derive_schema import _resolve, _has_null_option  # noqa: E402


def _fill(node, defs, instance, path, unfillable):
    """Returns the value to store at `path`, given the schema `node`.

    `instance` is the current value (or _MISSING). Recurses into objects and
    array items that are already present, so a nested absence inside an
    otherwise-populated object is filled too -- an entry can legitimately
    have `semantics.collective` present but one of its leaves never written.
    """
    resolved = _resolve(node, defs)

    if instance is _MISSING:
        if _has_null_option(resolved, defs):
            return None
        types = resolved.get("type")
        types = types if isinstance(types, list) else [types]
        if "array" in types:
            return []
        if "object" in types:
            instance = {}  # fall through and materialize its required keys
        else:
            unfillable.append(path)
            return _MISSING

    if isinstance(instance, dict):
        properties = resolved.get("properties") or {}
        for key in resolved.get("required") or []:
            sub = properties.get(key)
            if sub is None:
                continue  # required but undescribed -- not this module's call to invent
            value = _fill(sub, defs, instance.get(key, _MISSING), f"{path}.{key}".lstrip("."), unfillable)
            if value is not _MISSING:
                instance[key] = value
        # Present-but-not-required keys still get recursed into: their own
        # nested required fields are just as much R1's business.
        for key, value in instance.items():
            if key in (resolved.get("required") or []) or key not in properties:
                continue
            filled = _fill(properties[key], defs, value, f"{path}.{key}".lstrip("."), unfillable)
            if filled is not _MISSING:
                instance[key] = filled
        return instance

    if isinstance(instance, list) and "items" in resolved:
        for i, item in enumerate(instance):
            filled = _fill(resolved["items"], defs, item, f"{path}[{i}]", unfillable)
            if filled is not _MISSING:
                instance[i] = filled
        return instance

    return instance


class _Missing:
    def __repr__(self):
        return "<MISSING>"


_MISSING = _Missing()


def materialize_nulls(entry, schema):
    """(entry, strict schema) -> (entry, [unfillable dotted paths]).

    Mutates and returns `entry`. Call once, on the final artifact, after
    every other stage -- calling it earlier would erase exactly the
    null/absent distinction 0_ through 3_ are built to preserve.
    """
    unfillable = []
    _fill(schema["$defs"]["entry"], schema["$defs"], entry, "", unfillable)
    return entry, unfillable


def materialize_corpus(entries, schema):
    """{entry_key: entry} -> {entry_key: [unfillable path, ...]} for the
    entries that still have a genuinely unfillable required field. Entries
    that filled cleanly are absent from the report, so an empty dict means
    the whole corpus now satisfies R1."""
    report = {}
    for entry_key, entry in entries.items():
        _entry, unfillable = materialize_nulls(entry, schema)
        if unfillable:
            report[entry_key] = unfillable
    return report
