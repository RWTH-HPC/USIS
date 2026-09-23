"""
Parses OpenSHMEM's TYPE/TYPENAME lookup tables directly from the tex files that
define them -- a closed, small, enumerable table lookup, not a general LaTeX
table parser.

There are **six** such tables, in two shapes:

  - Four two-column ones ("\\TYPE & \\TYPENAME \\\\"): stdrmatypes and
    stdamotypes/extamotypes/bitamotypes, in content/rma_intro.tex and
    content/atomics_intro.tex.
  - Two five-column ones: teamreducetypes and asetreducetypes, in
    content/shmem_reductions.tex. Their last three columns say which reduction
    *operations* each type supports --

        char          & char  &              & MAX, MIN & SUM, PROD \\
        unsigned char & uchar & AND, OR, XOR & MAX, MIN & SUM, PROD \\

    -- so the type list for shmem_TYPENAME_and_reduce is not the whole table,
    only the rows whose bitwise column is non-empty. Reading the table as a
    plain type list would mint shmem_char_and_reduce, which the standard does
    not define.

The two reduction tables were missed when this parser was written (its previous
docstring said "confirmed by reading all 4 tables directly" -- there were six).
Because \\_resolve_axis could not resolve them, every reduction and scan
declaration was dropped: 14 in content/shmem_reductions.tex and 2 in
content/shmem_scan.tex, which refers to teamreducetypes for its SUM types.
"""

import glob
import os
import sys
import re

_LAYOUT_COMMON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "common")
sys.path.insert(0, _LAYOUT_COMMON)
from layout import EXTERNAL_INPUTS_DIR  # noqa: E402

_CONTENT_DIR = os.path.join(EXTERNAL_INPUTS_DIR, "shmem", "tex", "shmem-standard", "content")

_LABEL_RE = re.compile(r"\\label\{(\w+)\}")
# TYPE column allows a literal backslash (e.g. "int8\_t" for int8_t's
# escaped underscore) alongside word chars/spaces; TYPENAME column is a
# plain identifier.
_ROW_RE = re.compile(r"^\s*([\w\s\\]+?)\s*&\s*(\w+)\s*\\\\\s*(?:\\hline)?\s*$")

# Five-column rows: TYPE & TYPENAME & <bitwise> & <min/max> & <arithmetic> \\
# Any of the three operation columns may be empty for a given type.
_REDUCTION_ROW_RE = re.compile(
    r"^\s*([\w\s\\]+?)\s*&\s*(\w+)\s*&([^&]*)&([^&]*)&([^\\]*)\\\\")

_SIMPLE_TABLES = ("stdrmatypes", "stdamotypes", "extamotypes", "bitamotypes")
_REDUCTION_TABLES = ("teamreducetypes", "asetreducetypes")
_KNOWN_TABLES = _SIMPLE_TABLES + _REDUCTION_TABLES


def _c_type_from_row(raw):
    """'unsigned long long' stays as-is; 'int8\\_t' -> 'int8_t'."""
    return raw.replace("\\_", "_").strip()


def _scan_tables():
    """-> {table_label: [(c_type, typename, frozenset(ops))]}; ops is empty for
    the four two-column tables, which state no per-type operation support."""
    tables = {}
    for path in glob.glob(os.path.join(_CONTENT_DIR, "*.tex")):
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        pending_rows = []
        for line in lines:
            m = _ROW_RE.match(line)
            if m:
                c_type, typename = m.group(1), m.group(2)
                if c_type.strip() not in ("TYPE",):  # skip header row
                    pending_rows.append((_c_type_from_row(c_type), typename, frozenset()))
                continue

            m = _REDUCTION_ROW_RE.match(line)
            if m:
                c_type, typename = m.group(1), m.group(2)
                if c_type.strip() not in ("TYPE", "\\TYPE"):  # skip header row
                    ops = frozenset(
                        op.strip().lower()
                        for column in m.group(3, 4, 5)
                        for op in column.split(",")
                        if op.strip())
                    pending_rows.append((_c_type_from_row(c_type), typename, ops))
                continue

            label_match = _LABEL_RE.search(line)
            if label_match and label_match.group(1) in _KNOWN_TABLES:
                tables[label_match.group(1)] = list(pending_rows)
                pending_rows = []

    missing = set(_KNOWN_TABLES) - set(tables)
    if missing:
        raise RuntimeError(f"expected type tables not found while scanning {_CONTENT_DIR}: {missing}")
    return tables


def parse_type_tables():
    """-> {table_label: [(c_type, typename), ...]} for all six known tables.

    The operation columns of the two reduction tables are dropped here: a
    caller that needs them asks reduction_types_for_operation() instead, so
    this shape stays what it has always been for the four simple tables."""
    return {label: [(c_type, typename) for c_type, typename, _ops in rows]
            for label, rows in _scan_tables().items()}


def reduction_types_for_operation(table_label, operation):
    """The rows of a reduction table that support `operation` ("and", "sum",
    ...) -> [(c_type, typename), ...], or None if this is not a reduction
    table. Raises if the table lists the operation for no type at all, which
    would mean the operation name was misread rather than genuinely unsupported."""
    if table_label not in _REDUCTION_TABLES:
        return None
    rows = _scan_tables()[table_label]
    matching = [(c_type, typename) for c_type, typename, ops in rows if operation in ops]
    if not matching:
        raise RuntimeError(
            f"no type in {table_label} supports the reduction operation {operation!r}; "
            f"operations present are {sorted({o for _c, _t, ops in rows for o in ops})}")
    return matching
