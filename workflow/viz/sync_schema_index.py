"""
Regenerates the schema-explorer data block inside
docs/viz/formal-semantics.html from curated/schemas/api-schema.json.

Why this exists: that page's explorer tab embedded hand-copied JSON Schema
fragments, and by 2026-07-22 they had gone nine schema versions stale
without anything noticing -- `identity.api_group` still showed the original
5-value enum (no "synchronization"), `execution.completion` was missing
"stream_ordered", `identity` still listed a `superseded_by` the schema had
since moved to `relationships`. A page whose whole purpose is "here is what the schema looks like"
is worse than no page when it silently disagrees with the schema.

Same treatment as workflow/staging/derive_schema.py, for the same reason:
the fragments are now GENERATED from the one source of truth, checked in as
generated output, and any drift shows up as a diff when this is re-run
rather than as a quietly wrong page. Re-run it after any schema change:

    python3 workflow/viz/sync_schema_index.py

The prose (`desc`, `group`, `title`) stays hand-written -- it's editorial,
not derivable -- and lives in _ENTRIES below. Only `code` is generated.
"""

import json
import os
import sys
import re

_LAYOUT_COMMON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common")
sys.path.insert(0, _LAYOUT_COMMON)
from layout import SCHEMAS_DIR  # noqa: E402

_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
_SCHEMA_PATH = os.path.join(SCHEMAS_DIR, "api-schema.json")
_PAGE_PATH = os.path.join(_ROOT, "docs", "viz", "formal-semantics.html")

# Width the collapsing pass in _compact aims for. The page renders these in
# a fixed-width code block; much beyond this and lines wrap awkwardly.
_MAX_LINE = 96

_BEGIN = "// <<< GENERATED SCHEMA_INDEX -- do not hand-edit; see workflow/viz/sync_schema_index.py"
_END = "// >>> END GENERATED SCHEMA_INDEX"

# (explorer id, $defs name, group label, title, editorial description).
# Order here is the order the explorer lists them in.
_ENTRIES = [
    ("entry", "entry", "core", "entry",
     "Top-level object — the eight sections, always present."),
    ("identity", "identity", "core", "identity",
     "Provenance and classification — model, name, api_group, lifecycle version strings, type_family. "
     "The supersession edge lives in relationships."),
    ("bindings", "bindings", "core", "bindings",
     "One named sub-object per language; null = unsupported by this PPM."),
    ("execution", "execution", "core", "execution",
     "When/where the call executes — all fields present in every entry."),
    ("semantics", "semantics", "core", "semantics",
     "At most one of collective/point_to_point/one_sided/atomic is non-null, and which one IS the operation class. "
     "memory and formal are separately nullable; formal is the layer this document is about."),
    ("semantics_memory", "semantics_memory", "core", "semantics.memory",
     "Completion and consistency facts. Nullable as a whole object — null where the call has "
     "no memory semantics to state."),
    ("parameter", "parameter", "core", "parameter",
     "Per-argument semantics — one entry per formal parameter, including where its buffer lives (memory_space)."),
    ("parameter_kind", "parameter_kind", "core", "parameter_kind",
     "The kind vocabulary, shared by parameters[].kind and return.value_kind."),
    ("return", "return", "core", "return",
     "Return value semantics."),
    ("tool_integration", "tool_integration", "core", "tool_integration",
     "Correctness/perf-tool hooks; context_dependencies covers fields not fixed by the symbol alone."),
    ("context_dependency", "context_dependency", "core", "context_dependency",
     "One entry per field whose effective value isn't fixed by the function symbol alone."),
    ("relationships", "relationships", "core", "relationships",
     "Links to related entries, and nothing else. Every value is a model-qualified "
     "\"model:function_key\" reference, and the validator enforces it. supersedes "
     "is superseded_by's derived inverse."),
    ("formal", "formal", "formal layer", "formal",
     "The subject of this whole document — participants, data_flow, sync, handle_lifecycle."),
    ("participant", "participant", "formal layer", "participant",
     "Who is involved, and does each one actually invoke the function."),
    ("data_flow_entry", "data_flow_entry", "formal layer", "data_flow_entry",
     "One memory access; source is a tagged object stating where a written value provably came from. "
     "\"reduced\" sources can carry an offset, and \"gathered\" assembles contributions with no operator."),
    ("sync", "sync", "formal layer", "sync",
     "Events, ordering, and cross-instance matching."),
    ("handle_lifecycle_entry", "handle_lifecycle_entry", "formal layer", "handle_lifecycle_entry",
     "Tracks a handle across its create → use → destroy interval; also the basis for RMA epochs."),
    ("shape_template", "shape_template", "formal layer", "shape_template",
     "Authoring-time only — erased by the expander before anything ships. See 0x3/0x4."),
]


def _compact(node, indent=2):
    """JSON Schema fragment -> a compact, readable string for the page.

    Descriptions are dropped: they're long-form prose in the real schema and
    would swamp a fragment meant to show STRUCTURE at a glance. The page
    links to the schema itself for the full text.
    """
    def strip(n):
        if isinstance(n, dict):
            return {k: strip(v) for k, v in n.items() if k not in ("description", "$comment")}
        if isinstance(n, list):
            return [strip(x) for x in n]
        return n

    # Render recursively rather than pretty-printing then re-collapsing: a
    # node whose single-line form fits the width budget is emitted inline,
    # otherwise it expands and its children get the same test one level in.
    # Fully-expanded indent-2 JSON is correct but unreadable at a glance,
    # and the hand-written fragments this replaces inlined leaves like
    # {"type":"string"} for exactly that reason -- showing structure at a
    # glance is the page's whole job.
    # `depth` drives indentation of children; `column` is only the fit test
    # (a value opened after a long key starts further right than its own
    # indent level). Keeping them separate is what stops nested values from
    # drifting rightward with each key length.
    def render(n, depth, column):
        flat = json.dumps(n, separators=(", ", ": "))
        if column + len(flat) <= _MAX_LINE or not isinstance(n, (dict, list)):
            return flat
        pad = " " * ((depth + 1) * indent)
        close = " " * (depth * indent)
        if isinstance(n, dict):
            items = [f'{pad}{json.dumps(k)}: {render(v, depth + 1, (depth + 1) * indent + len(json.dumps(k)) + 2)}'
                     for k, v in n.items()]
            return "{\n" + ",\n".join(items) + "\n" + close + "}"
        items = [f"{pad}{render(v, depth + 1, (depth + 1) * indent)}" for v in n]
        return "[\n" + ",\n".join(items) + "\n" + close + "]"

    return render(strip(node), 0, 0)


def build_block(schema):
    defs = schema["$defs"]
    lines = [_BEGIN, "const SCHEMA_INDEX = ["]
    for explorer_id, defs_name, group, title, desc in _ENTRIES:
        if defs_name not in defs:
            raise KeyError(f"$defs/{defs_name} is referenced by the explorer but missing from the schema")
        code = _compact(defs[defs_name])
        lines.append("  { id:%s, group:%s, title:%s, desc:%s," % (
            json.dumps(explorer_id), json.dumps(group), json.dumps(title), json.dumps(desc)))
        lines.append("    code:%s }," % json.dumps(code))
    lines.append("];")
    lines.append(_END)
    return "\n".join(lines)


def run():
    with open(_SCHEMA_PATH) as f:
        schema = json.load(f)
    with open(_PAGE_PATH) as f:
        page = f.read()

    block = build_block(schema)
    pattern = re.compile(re.escape(_BEGIN) + r".*?" + re.escape(_END), re.S)
    if not pattern.search(page):
        raise SystemExit(
            f"{_PAGE_PATH} has no generated-block markers. Insert:\n{_BEGIN}\n...\n{_END}\naround "
            "the SCHEMA_INDEX declaration first."
        )
    page = pattern.sub(lambda _m: block, page)

    with open(_PAGE_PATH, "w") as f:
        f.write(page)
    print(f"synced {len(_ENTRIES)} schema fragments from {os.path.basename(_SCHEMA_PATH)} "
          f"({schema['title']}) into {os.path.basename(_PAGE_PATH)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
