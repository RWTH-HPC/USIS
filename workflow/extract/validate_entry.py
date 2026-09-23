"""
Generic structural validator for a full 8-section entry, extended from
workflow/formal/validate.py's existing hand-rolled pattern (required keys
present + enum membership, plus pattern and minimum; no jsonschema package available and no network
access in this environment to install one -- see that module's own
docstring). validate.py itself only covers semantics.formal in isolation;
this module covers a whole entry against an arbitrary schema dict (the
strict api-schema.json, or a derived staging variant), which is what
Extract's golden-test harness needs to prove the interface contract is
actually met, not just internally self-consistent.

Deliberately generic (walks $defs via $ref/anyOf/oneOf resolution) rather
than one hardcoded function per section, the way validate.py's per-$def
functions are -- an entry has 8 sections plus nested sub-objects, so a
hand-written function per shape would just re-derive this same walk by
hand many times over.
"""

import json
import os
import re
import sys

_LAYOUT_COMMON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common")
sys.path.insert(0, _LAYOUT_COMMON)
from layout import SCHEMAS_DIR  # noqa: E402

_SCHEMA_PATH = os.path.join(SCHEMAS_DIR, "api-schema.json")


class ValidationError(Exception):
    pass


def _resolve(node, defs):
    while "$ref" in node:
        node = defs[node["$ref"].split("/")[-1]]
    return node


def _type_ok(value, node, defs):
    node = _resolve(node, defs)
    t = node.get("type")
    if t is None:
        return True
    types = t if isinstance(t, list) else [t]
    for candidate in types:
        if candidate == "null" and value is None:
            return True
        if candidate == "string" and isinstance(value, str):
            return True
        if candidate == "boolean" and isinstance(value, bool):
            return True
        if candidate == "integer" and isinstance(value, int) and not isinstance(value, bool):
            return True
        if candidate == "array" and isinstance(value, list):
            return True
        if candidate == "object" and isinstance(value, dict):
            return True
    return False


def _validate_node(value, node, defs, path):
    node = _resolve(node, defs)

    if "anyOf" in node or "oneOf" in node:
        branches = node.get("anyOf") or node.get("oneOf")
        errors = []
        for branch in branches:
            try:
                _validate_node(value, branch, defs, path)
                return
            except ValidationError as e:
                errors.append(str(e))
        raise ValidationError(f"{path}: value matches none of {len(branches)} anyOf/oneOf branches: {errors}")

    if not _type_ok(value, node, defs):
        raise ValidationError(f"{path}: value {value!r} does not match type {node.get('type')!r}")

    enum = node.get("enum")
    if enum is not None and value not in enum:
        raise ValidationError(f"{path}: {value!r} not in allowed enum values {enum}")

    pattern = node.get("pattern")
    if pattern is not None and isinstance(value, str) and not re.search(pattern, value):
        raise ValidationError(f"{path}: {value!r} does not match pattern {pattern!r}")
    minimum = node.get("minimum")
    if minimum is not None and isinstance(value, int) and not isinstance(value, bool) and value < minimum:
        raise ValidationError(f"{path}: {value!r} is below the minimum {minimum}")

    t = node.get("type")
    types = t if isinstance(t, list) else ([t] if t else [])

    if "object" in types or "properties" in node:
        if value is None:
            return  # already passed _type_ok, meaning null was an allowed alternative
        if not isinstance(value, dict):
            raise ValidationError(f"{path}: expected object, got {type(value).__name__}")
        required = node.get("required", [])
        extra_schema = node.get("additionalProperties")
        if extra_schema is False:
            allowed = set(node.get("properties", {}))
            extra = set(value) - allowed
            if extra:
                raise ValidationError(f"{path}: unexpected key(s) {sorted(extra)} not in schema's properties")
        elif isinstance(extra_schema, dict):
            # An open map whose VALUES have a shape (field-provenance's `tiers`,
            # a review record's `exceptions`). Only reachable for schemas other
            # than api-schema.json, which never uses this form.
            for key in set(value) - set(node.get("properties", {})):
                _validate_node(value[key], extra_schema, defs, f"{path}[{key!r}]")
        for key in required:
            if key not in value:
                raise ValidationError(f"{path}: missing required field {key!r}")
        for key, sub in node.get("properties", {}).items():
            if key in value:
                _validate_node(value[key], sub, defs, f"{path}.{key}")
        return

    if "array" in types:
        if value is None:
            return
        if not isinstance(value, list):
            raise ValidationError(f"{path}: expected array, got {type(value).__name__}")
        min_items = node.get("minItems")
        if min_items is not None and len(value) < min_items:
            raise ValidationError(f"{path}: array has {len(value)} item(s), schema requires at least {min_items}")
        items = node.get("items")
        if items:
            for i, item in enumerate(value):
                _validate_node(item, items, defs, f"{path}[{i}]")
        return


def validate_document(document, schema):
    """Validate a whole JSON document against `schema`'s root node (not
    $defs/entry). Used for the curated files that are not entry corpora --
    field-provenance.json, shapes.json, a review record, a supplement input --
    each of which has its own schema in curated/schemas/. Same hand-rolled
    subset of JSON Schema as validate_entry below; see this module's docstring
    for why there is no jsonschema dependency."""
    _validate_node(document, schema, schema.get("$defs", {}), schema.get("title", "document"))


def validate_entry(entry, schema=None):
    """Validate one full entry dict against $defs/entry of `schema`
    (api-schema.json's own structure, or a derived staging variant).
    Raises ValidationError on the first problem found.
    """
    if schema is None:
        with open(_SCHEMA_PATH) as f:
            schema = json.load(f)
    defs = schema["$defs"]
    _validate_node(entry, defs["entry"], defs, "entry")
