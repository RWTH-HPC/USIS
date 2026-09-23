# Schema Versioning

The schema's version is part of its `$id` in `curated/schemas/api-schema.json`
(currently v0.1.0), and each shipped `final-<ppm>-api.json` states the version
it was validated against in `schema_version`. The `$id` is the file itself at
the release tag of that version, so it resolves:
`https://raw.githubusercontent.com/RWTH-HPC/USIS/v0.1.0/curated/schemas/api-schema.json`.
A version is therefore only final once its tag exists.

## Version numbers

Versions follow [Semantic Versioning](https://semver.org/). While the major
version is 0, the schema is not yet stable:

- **Minor** (`0.1.0` → `0.2.0`): any change to the vocabulary or structure,
  including one that is purely additive for data (see below).
- **Patch** (`0.1.0` → `0.1.1`): description and documentation changes only;
  an instance valid against one patch version is valid against every other.

`1.0.0` will mark the point from which removing or renaming a field or enum
value requires a major bump.

## Why vocabulary growth bumps the version

The schema uses closed `enum` arrays throughout (see "Enumerable vocabulary" in
`docs/schema/design-conventions.md`). Adding an enum value is therefore additive
for data but not for validation: a validator built against an older `$id`
rejects a newer, valid document. So any vocabulary growth bumps `$id`, and
consumers validate against the version an instance declares, rather than the
schema loosening its enums into open-ended patterns to avoid bumps.

Two kinds of change need no bump:

- **New `data_flow[].inputs[].scope` values.** `scope` is a free string with a
  documented registry (`docs/schema/semantics-formal.md`), precisely so a new
  scope such as the two-party `rma_target_prior` does not force a bump.
- **New shapes.** Shapes are erased before shipping, so the shape catalog grows
  independently of the schema. Only new `formal`-layer vocabulary (a new `op`,
  a new `source.kind`) needs a bump; a new shape built from existing vocabulary
  does not.

Consumers and tools should check the version an instance declares rather than
assume one: the schema keeps growing.
