"""
A minimal structural validator for expanded semantics.formal blocks,
checked directly against curated/schemas/api-schema.json's own $defs.

This is NOT a general JSON Schema validator (no jsonschema package is
available in this environment -- no network access to install one). It
covers exactly what this project's shapes actually need checked: required
keys present, enum membership, and the oneOf branches of data_flow[].source.
That is enough to catch the mistakes an authored shape or a bad expansion
would actually make (a typo'd enum value, a missing required field), which
is the same bar Validate's "schema conformance" check
(workflow/README.md) is described as clearing.

Load $defs directly from the schema file rather than hardcoding enums here,
so this stays correct if the schema's vocabulary grows (see
docs/schema/schema-versioning.md) without needing a matching edit here.
"""

import json
import os
import sys

_LAYOUT_COMMON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common")
sys.path.insert(0, _LAYOUT_COMMON)
from layout import SCHEMAS_DIR  # noqa: E402

_SCHEMA_PATH = os.path.join(SCHEMAS_DIR, "api-schema.json")


def _load_defs():
    with open(_SCHEMA_PATH) as f:
        return json.load(f)["$defs"]


class ValidationError(Exception):
    pass


def _check_required(obj, required, path):
    for key in required:
        if key not in obj:
            raise ValidationError(f"{path}: missing required field '{key}'")


def _check_enum(value, enum, path):
    if value not in enum:
        raise ValidationError(f"{path}: '{value}' not in allowed values {enum}")


def validate_participant(p, defs, path="participant"):
    d = defs["participant"]
    _check_required(p, d["required"], path)
    _check_enum(p["role_kind"], d["properties"]["role_kind"]["enum"], f"{path}.role_kind")
    _check_enum(p["cardinality"], d["properties"]["cardinality"]["enum"], f"{path}.cardinality")


def validate_data_flow_entry(e, defs, path="data_flow[]"):
    d = defs["data_flow_entry"]
    _check_required(e, d["required"], path)
    _check_enum(e["op"], d["properties"]["op"]["enum"], f"{path}.op")

    source = e["source"]
    if source is not None:
        if "kind" not in source:
            raise ValidationError(f"{path}.source: missing 'kind'")
        if source["kind"] == "structural":
            _check_required(source, ["kind", "ref"], f"{path}.source")
        elif source["kind"] == "reduced":
            _check_required(source, ["kind", "ref"], f"{path}.source")
        elif source["kind"] == "gathered":
            # Per-participant assembly with no operator (allgather).
            _check_required(source, ["kind", "ref", "scope"], f"{path}.source")
        elif source["kind"] == "matched":
            _check_required(source, ["kind", "via"], f"{path}.source")
        else:
            raise ValidationError(f"{path}.source.kind: '{source['kind']}' is not structural/reduced/gathered/matched")


def validate_sync(s, defs, path="sync"):
    d = defs["sync"]
    _check_required(s, d["required"], path)

    for i, ev in enumerate(s["events"]):
        ev_path = f"{path}.events[{i}]"
        _check_required(ev, d["properties"]["events"]["items"]["required"], ev_path)
        _check_enum(ev["event_type"], d["properties"]["events"]["items"]["properties"]["event_type"]["enum"], f"{ev_path}.event_type")

    for i, o in enumerate(s["ordering"]):
        o_path = f"{path}.ordering[{i}]"
        _check_required(o, d["properties"]["ordering"]["items"]["required"], o_path)
        _check_enum(o["scope"], d["properties"]["ordering"]["items"]["properties"]["scope"]["enum"], f"{o_path}.scope")

    matching = s["matching"]
    if matching is not None:
        # Hardened 2026-07-19: this used to check only `kind`, which is why
        # the rma.* templates' illegal literal-null matched_across/
        # program_order_required sailed past THIS validator and were only caught much later by the
        # full-entry validator once upstream failures stopped masking them.
        # Now every present matching field is checked against its schema type,
        # and unknown keys are rejected (additionalProperties is false there).
        m_schema = d["properties"]["matching"]
        unknown = set(matching) - set(m_schema["properties"])
        if unknown:
            raise ValidationError(f"{path}.matching: unknown key(s) {sorted(unknown)}")
        _PY_TYPES = {"string": str, "boolean": bool, "array": list, "object": dict}
        for fname, fnode in m_schema["properties"].items():
            if fname not in matching:
                continue
            value = matching[fname]
            declared = fnode.get("type")
            declared_list = declared if isinstance(declared, list) else [declared] if declared else []
            if declared_list:
                ok = any(
                    (t == "null" and value is None) or
                    (t in _PY_TYPES and isinstance(value, _PY_TYPES[t]) and not (t != "boolean" and isinstance(value, bool)))
                    for t in declared_list
                )
                if not ok:
                    raise ValidationError(
                        f"{path}.matching.{fname}: value {value!r} does not match type {declared!r} "
                        f"(omit optional fields entirely rather than setting them null)"
                    )
            if fnode.get("enum") is not None and value is not None:
                _check_enum(value, fnode["enum"], f"{path}.matching.{fname}")
        if "match_keys" in matching and isinstance(matching["match_keys"], list):
            for i, mk in enumerate(matching["match_keys"]):
                if not isinstance(mk, str):
                    raise ValidationError(f"{path}.matching.match_keys[{i}]: expected string, got {type(mk).__name__}")


def validate_handle_lifecycle_entry(h, defs, path="handle_lifecycle[]"):
    d = defs["handle_lifecycle_entry"]
    _check_required(h, d["required"], path)
    _check_enum(h["handle_kind"], d["properties"]["handle_kind"]["enum"], f"{path}.handle_kind")
    _check_enum(h["role"], d["properties"]["role"]["enum"], f"{path}.role")


def validate_formal(formal, defs=None, path="formal"):
    """Validate an expanded semantics.formal block. Raises ValidationError on the first problem found."""
    if formal is None:
        return

    defs = defs or _load_defs()
    d = defs["formal"]
    _check_required(formal, d["required"], path)

    for i, p in enumerate(formal["participants"]):
        validate_participant(p, defs, f"{path}.participants[{i}]")
    for i, e in enumerate(formal["data_flow"]):
        validate_data_flow_entry(e, defs, f"{path}.data_flow[{i}]")
    validate_sync(formal["sync"], defs, f"{path}.sync")
    for i, h in enumerate(formal["handle_lifecycle"]):
        validate_handle_lifecycle_entry(h, defs, f"{path}.handle_lifecycle[{i}]")


def validate_shape_template(shape, defs=None, path="shape_template"):
    """
    Validate a shapes.json entry's own id/slots structure.

    Deliberately does NOT validate `template` against $defs/formal: a
    template legitimately contains unbound "{{slot}}" placeholders in
    enum/const positions (e.g. resource.lifecycle's handle_kind), which
    can never satisfy $defs/formal's enum constraints pre-expansion. This
    is the exact tension docs/schema/shape-catalog.md notes as the reason
    a separate, relaxed entries-authored.schema.json is needed and not yet
    written -- until that exists, a template's correctness is checked the
    way this module's own test harness does it: by expanding it against a
    real binding and validating *that* with validate_formal().
    """
    defs = defs or _load_defs()
    d = defs["shape_template"]
    _check_required(shape, d["required"], path)

    slot_kind_enum = d["properties"]["slots"]["items"]["properties"]["kind"]["enum"]
    for i, slot in enumerate(shape["slots"]):
        slot_path = f"{path}.slots[{i}]"
        _check_required(slot, ["name", "kind", "optional"], slot_path)
        _check_enum(slot["kind"], slot_kind_enum, f"{slot_path}.kind")
