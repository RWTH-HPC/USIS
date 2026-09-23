"""
Generate Formal's deterministic expansion half.

Ports the expand() prototype from docs/viz/formal-semantics.html
(section 0x3) to Python, faithfully: same two-mode string substitution,
zero model calls, zero side effects. Identical input always produces
byte-identical output — this is a hard requirement, not a nicety, because
Validate's golden-diff strategy (docs/cross-ppm-analysis/known-gaps-and-open-questions.md)
depends on it.

apply_extra() is NOT part of the original JS prototype. The design docs
(docs/schema/shape-catalog.md) describe `extra` as a second, separate step
("deep-merged onto the expansion after substitution") without giving it a
name or an algorithm — this is a direct, minimal implementation of that
description, kept as its own pure function so it stays independently
testable from expand() itself.
"""

SLOT_RE_WHOLE = None  # see _is_whole_slot_ref


def _is_whole_slot_ref(s):
    """True if the string is exactly '{{slot_name}}' with nothing else around it."""
    return (
        isinstance(s, str)
        and s.startswith("{{")
        and s.endswith("}}")
        and "{{" not in s[2:-2]
        and "}}" not in s[2:-2]
    )


def _slot_name(s):
    return s[2:-2]


def expand(template_node, bindings):
    """
    Pure substitution: template_node (a shape's `template`, or any sub-node
    of it) + bindings (slot name -> concrete value) -> fully inlined node.

    Two-mode string handling, matching the JS prototype exactly:
      - a string that IS exactly "{{slot}}" substitutes the whole bound
        value, preserving its type (object, array, number, ...).
      - a string that CONTAINS "{{slot}}" as a substring does textual
        replacement, stringifying non-string bindings.
    """
    if isinstance(template_node, list):
        return [expand(item, bindings) for item in template_node]

    if isinstance(template_node, dict):
        return {key: expand(value, bindings) for key, value in template_node.items()}

    if isinstance(template_node, str):
        if _is_whole_slot_ref(template_node):
            name = _slot_name(template_node)
            if name not in bindings:
                raise KeyError(f"template references unbound slot '{name}'")
            return bindings[name]

        if "{{" in template_node and "}}" in template_node:
            result = template_node
            for name, value in bindings.items():
                token = "{{" + name + "}}"
                if token in result:
                    replacement = value if isinstance(value, str) else _json_stringify(value)
                    result = result.replace(token, replacement)
            return result

        return template_node

    # numbers, booleans, null pass through unchanged
    return template_node


def _json_stringify(value):
    import json

    return json.dumps(value)


def _deep_merge(base, patch):
    """
    Deep-merge patch onto base: dict keys merge recursively, any other
    value (including lists) is replaced wholesale by the patch's value.
    Neither input is mutated.
    """
    if not isinstance(base, dict) or not isinstance(patch, dict):
        return patch

    merged = dict(base)
    for key, patch_value in patch.items():
        if key in merged:
            merged[key] = _deep_merge(merged[key], patch_value)
        else:
            merged[key] = patch_value
    return merged


def apply_extra(expanded, extra):
    """
    Apply an authored `extra` block on top of an already-expanded formal
    block. `extra` keys are dotted paths (e.g. "sync.matching") mapping to
    the object that replaces/merges onto whatever's at that path -- this
    matches every `extra` example in docs/schema/shape-catalog.md and the
    worked examples in formal-semantics.html, all of which use a single
    dotted key rather than nested objects.
    """
    if extra is None:
        return expanded

    result = expanded
    for dotted_path, patch_value in extra.items():
        parts = dotted_path.split(".")
        result = _set_dotted(result, parts, patch_value)
    return result


def _set_dotted(node, parts, patch_value):
    if len(parts) == 1:
        merged = dict(node)
        merged[parts[0]] = _deep_merge(merged.get(parts[0]), patch_value)
        return merged

    head, rest = parts[0], parts[1:]
    merged = dict(node)
    merged[head] = _set_dotted(merged.get(head, {}), rest, patch_value)
    return merged


def expand_entry(shape_template, bindings, extra=None):
    """Convenience wrapper: expand a shape's `template` against `bindings`, then apply `extra`."""
    expanded = expand(shape_template["template"], bindings)
    return apply_extra(expanded, extra)
