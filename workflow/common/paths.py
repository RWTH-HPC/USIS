"""
Shared dotted-path get/set for the proposal-merge machinery (workflow/supplement/
propose.py reads with these, workflow/assemble/assemble.py writes with them) --
split out here rather than duplicated per-file so the two can never drift
apart on what a path segment means, which matters because propose.py's
"is this field currently null" check and assemble.py's "write the promoted
value here" must resolve the exact same location for the precedence rule
(curated/README.md: "supplement never overrides") to hold.

Segments are plain dict keys ("identity.desc") except one shape: `key[name]`
addresses a list-of-dicts field by matching an element's own "name" property
(e.g. "parameters[buf].length" -- MPI_Isend's `buf` parameter's `length`).
This reuses the same "reference a parameter by its name" idea as the
schema's own `param:name` selector token (docs/schema/reference-grammar.md)
rather than inventing a second convention for the same concept.
"""

import re

ABSENT = "__ABSENT__"

_INDEXED_RE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*)\[([^\[\]]+)\]$")


def _find_named(items, name):
    if not isinstance(items, list):
        return None
    return next((item for item in items if isinstance(item, dict) and item.get("name") == name), None)


def get_path(entry, dotted_path):
    """Returns the value at dotted_path, or ABSENT if any segment doesn't
    resolve (missing key, or no parameters[]-style element with that name)."""
    node = entry
    for part in dotted_path.split("."):
        m = _INDEXED_RE.match(part)
        if m:
            list_key, name = m.groups()
            if not isinstance(node, dict) or list_key not in node:
                return ABSENT
            match = _find_named(node[list_key], name)
            if match is None:
                return ABSENT
            node = match
            continue
        if not isinstance(node, dict) or part not in node:
            return ABSENT
        node = node[part]
    return node


def set_path(entry, dotted_path, value):
    """Writes value at dotted_path, creating intermediate plain-dict
    segments as needed. The final segment must not be an indexed one --
    every current caller only ever indexes to descend into a parameter,
    then sets one of that parameter's own plain fields."""
    parts = dotted_path.split(".")
    node = entry
    for part in parts[:-1]:
        m = _INDEXED_RE.match(part)
        if m:
            list_key, name = m.groups()
            match = _find_named(node.get(list_key), name)
            if match is None:
                raise KeyError(f"{dotted_path!r}: no element named {name!r} in {list_key!r}")
            node = match
            continue
        nxt = node.get(part)
        if nxt is None:
            nxt = {}
            node[part] = nxt
        node = nxt

    last = parts[-1]
    if _INDEXED_RE.match(last):
        raise ValueError(f"{dotted_path!r}: path cannot end on an indexed segment")
    node[last] = value
