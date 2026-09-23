"""
Shared C-header reading for the adapters that parse a vendored runtime header
directly: workflow/extract/openmp/adapter.py (LLVM's omp.h) and
workflow/extract/cuda/adapter.py (cuda_runtime_api.h).

NCCL's and NVSHMEM's adapters each keep their own small _parse_c_param and are
deliberately left alone -- their golden output must not move. These two headers
need more than that parser handles:

  - omp.h declares most parameters without a name (`omp_init_lock(omp_lock_t *)`)
    and spells const after the type (`char const *`);
  - cuda_runtime_api.h has pointer-to-pointer parameters (`void **devPtr`), C++
    default arguments (`__dv(0)`), and a `__CUDA_API_VERSION_INTERNAL` block
    that declares most of the stream-ordered routines a second time;
  - both hide C++-only declarations behind `#ifdef __cplusplus`.

Everything here is deterministic and dependency-free, and every transform
preserves character offsets (removed text becomes spaces, newlines are kept),
so an offset or line number computed on processed text is also valid in the
vendored file.
"""

import bisect
import re

# --- parameters whose direction the const/pointer heuristic gets wrong --------

# Direction is inferred from const-qualification and pointer-ness in every
# adapter that reads a bare C header, because C states nothing else. That
# inference has one systematic failure: a non-const pointer becomes "out",
# which is right for an output parameter (`int *count`) and wrong for a handle
# the call *consumes* -- memory being released, or a registration being undone.
# Nothing in the C declaration separates the two, and nothing in the OpenMP
# specification's argument-properties table does either: it spells
# omp_target_memcpy's written `dst` and omp_free's released `ptr` identically
# ("iso_c, value"). So the cases are enumerated, each grounded in the sentence
# of its own routine's documentation that settles it, rather than generalised
# into a verb rule -- `cudaGraphAddMemFreeNode` is exactly why, since its
# `pGraphNode` is a genuine output on a routine whose name says "Free".
#
# This table is deliberately small and deliberately explicit. A new entry needs
# a quotation, not a pattern.
RELEASED_PARAMETERS = {
    ("cuda", "cudaFree", "devPtr"):
        'cuda_runtime_api.h: "\\param devPtr - Device pointer to memory to free"',
    ("cuda", "cudaFreeAsync", "devPtr"):
        'cuda_runtime_api.h, \\brief "Frees memory with stream ordered semantics"; '
        'the doxygen calls this parameter dptr, "memory to free"',
    ("cuda", "cudaFreeHost", "ptr"):
        'cuda_runtime_api.h: "\\param ptr - Pointer to memory to free"',
    ("cuda", "cudaHostUnregister", "ptr"):
        'cuda_runtime_api.h: "\\param ptr - Host pointer to memory to unregister"',
    ("cuda", "cudaGraphAddMemFreeNode", "dptr"):
        'cuda_runtime_api.h: "\\param dptr - Address of memory to free". The same routine\'s '
        'pGraphNode is "Returns newly created node" and stays an output -- which is why this '
        'table is keyed by parameter and not by a verb in the routine name',
    ("nccl", "ncclMemFree", "ptr"):
        "the deallocation counterpart of ncclMemAlloc: the pointer names the allocation to release",
    ("openmp", "omp_free", "ptr"):
        'OpenMP 6.0 section 27.12 Effect: "The omp_free routine deallocates the memory to which '
        'the ptr argument points"',
    ("openmp", "omp_target_free", "device_ptr"):
        'OpenMP 6.0 section 25.4 Effect: "The omp_target_free routine frees the memory in the '
        'device data environment associated with device_ptr"',
}


def released_direction(model, routine, parameter):
    """-> the documented reason this parameter is an input, or None."""
    return RELEASED_PARAMETERS.get((model, routine, parameter))

# --- conditional compilation ----------------------------------------------

_DIRECTIVE_RE = re.compile(r"^\s*#\s*(\w*)(.*)$")
_DEFINED_RE = re.compile(r"\bdefined\s*(?:\(\s*(\w+)\s*\)|(\w+))")
_INT_SUFFIX_RE = re.compile(r"\b(\d+)[uUlL]+\b")
_IDENT_RE = re.compile(r"\b[A-Za-z_]\w*\b")
_ALLOWED_EXPR_RE = re.compile(r"^(?:\s|\d+|\band\b|\bor\b|\bnot\b|[()<>=!])*$")


def _blank(text):
    return re.sub(r"[^\n]", " ", text)


def eval_condition(expr, macros):
    """A preprocessor #if expression -> bool, against an explicit macro table
    ({name: int}; a name absent from the table is undefined).

    Covers what the two vendored headers use -- defined(X), integer
    comparisons, !, &&, || and parentheses -- and raises ValueError on anything
    else rather than guessing, so a header update that introduces a new
    construct fails loudly instead of silently selecting the wrong branch.
    """
    e = re.sub(r"/\*.*?\*/|//.*$", " ", expr)
    e = _DEFINED_RE.sub(lambda m: "1" if (m.group(1) or m.group(2)) in macros else "0", e)
    e = _INT_SUFFIX_RE.sub(r"\1", e)
    # The C preprocessor's own rule: an identifier that is not a macro is 0.
    e = _IDENT_RE.sub(lambda m: str(int(macros.get(m.group(0), 0))), e)
    e = e.replace("&&", " and ").replace("||", " or ")
    e = re.sub(r"!(?!=)", " not ", e)
    if not _ALLOWED_EXPR_RE.match(e):
        raise ValueError(f"unsupported preprocessor expression: {expr!r}")
    return bool(eval(e, {"__builtins__": {}}, {}))  # noqa: S307 -- digits and operators only, checked above


def select_active_lines(text, macros):
    """Blank every line the preprocessor would drop under `macros`, and every
    directive line itself; line count and offsets are unchanged.

    Only conditionals are interpreted. #define/#undef are NOT tracked: the
    macro table is the whole configuration, stated by the adapter, so which
    branch was taken is visible in one place rather than depending on the
    header's own definition order.
    """
    out = []
    stack = []  # (parent_active, a_branch_was_taken) per open conditional
    active = True
    continuing = False  # inside a backslash-continued directive
    for line in text.split("\n"):
        if continuing:
            continuing = line.endswith("\\")
            out.append(_blank(line))
            continue
        m = _DIRECTIVE_RE.match(line)
        if m is None:
            out.append(line if active else _blank(line))
            continue
        out.append(_blank(line))
        continuing = line.endswith("\\")
        directive, rest = m.group(1), m.group(2).strip()
        if directive in ("if", "elif") and continuing:
            raise ValueError(f"multi-line #{directive} is not supported: {line!r}")
        if directive in ("if", "ifdef", "ifndef"):
            taken = False
            if active:
                if directive == "if":
                    taken = eval_condition(rest, macros)
                else:
                    taken = (rest.split()[0] in macros) == (directive == "ifdef")
            stack.append((active, taken))
            active = active and taken
        elif directive == "elif":
            parent, taken = stack[-1]
            now = parent and not taken and eval_condition(rest, macros)
            stack[-1] = (parent, taken or now)
            active = now
        elif directive == "else":
            parent, taken = stack[-1]
            active = parent and not taken
            stack[-1] = (parent, True)
        elif directive == "endif":
            active, _ = stack.pop()
    if stack:
        raise ValueError(f"{len(stack)} unterminated preprocessor conditional(s)")
    return "\n".join(out)


# --- comments -------------------------------------------------------------

_COMMENT_RE = re.compile(r"/\*.*?\*/|//[^\n]*", re.DOTALL)
_DOC_RE = re.compile(r"/\*\*(?!/).*?\*/", re.DOTALL)


def blank_comments(text):
    """Every comment replaced by spaces (newlines kept)."""
    return _COMMENT_RE.sub(lambda m: _blank(m.group(0)), text)


def blank_calls(text, macro):
    """Every `macro(...)` call (balanced parentheses) replaced by spaces --
    used for CUDA's `__dv(default)`, which expands to nothing in C."""
    chars = list(text)
    for m in re.finditer(rf"\b{re.escape(macro)}\s*\(", text):
        depth, i = 0, m.end() - 1
        while i < len(text):
            if text[i] == "(":
                depth += 1
            elif text[i] == ")":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        for j in range(m.start(), i + 1):
            if chars[j] != "\n":
                chars[j] = " "
    return "".join(chars)


class DocIndex:
    """The `/** ... */` blocks of a text, looked up by what they document."""

    def __init__(self, text):
        self._text = text
        self._blocks = [(m.end(), m.group(0)) for m in _DOC_RE.finditer(text)]
        self._ends = [end for end, _ in self._blocks]

    def before(self, pos):
        """The block that ends immediately before offset `pos` -- nothing but
        whitespace between them (blanked directive lines count as whitespace)
        -- or None."""
        i = bisect.bisect_right(self._ends, pos) - 1
        if i < 0:
            return None
        end, body = self._blocks[i]
        return body if not self._text[end:pos].strip() else None


# --- declarations ---------------------------------------------------------

_QUALIFIERS = frozenset({"const", "volatile", "restrict", "__restrict", "__restrict__"})
_TAGS = frozenset({"struct", "enum", "union"})
_BUILTIN_TYPES = frozenset({"void", "char", "short", "int", "long", "float", "double", "signed", "unsigned", "_Bool"})
_TOKEN_RE = re.compile(r"\*|[A-Za-z_]\w*|\[[^\]]*\]")


def _tokens(text):
    tokens = _TOKEN_RE.findall(text)
    if "".join(tokens) != re.sub(r"\s", "", text):
        raise ValueError(f"not a plain C type/declarator (function pointer, default argument, ...): {text!r}")
    return tokens


def _render(tokens):
    out = ""
    for tok in tokens:
        if tok == "*":
            out += "*" if out.endswith("*") else " *"
        elif out.endswith("*"):
            out += tok
        else:
            out += (" " if out else "") + tok
    return out


def normalize_type(text):
    """'void*' / 'void *' / 'void  *' -> 'void *'; 'char const*' -> 'char const *'."""
    return _render(_tokens(" ".join(text.split())))


def parse_c_param(text):
    """One parameter declaration -> dict, or None for an empty slot / `void`.

    {"name": str|None, "c_type": str, "base_type": str, "array_suffix": str,
     "constant": bool, "pointer": bool, "pointer_depth": int}

    `name` is None when the declaration carries none (`omp_lock_t *`, `int`,
    `struct cudaExtent`). For a pointer, `constant` means the object it points
    at DIRECTLY is const -- a `const` between its last `*` and the one before
    (or the start) -- since that is what decides whether the callee can write
    through it: `const void *src` and `void *const *dsts` (an array of fixed
    pointers the callee only reads) are constant, `const cudaGraphNode_t
    **deps_out` (the callee stores a pointer into it) is not.
    Raises ValueError on anything that is not a plain declarator.
    """
    t = " ".join(text.split())
    if t in ("", "void"):
        return None
    tokens = _tokens(t)
    array_suffix = ""
    if tokens and tokens[-1].startswith("["):
        array_suffix = tokens.pop()
    name = None
    last = tokens[-1] if tokens else None
    if last and last != "*" and last not in (_BUILTIN_TYPES | _QUALIFIERS | _TAGS):
        prefix = tokens[:-1]
        # The last identifier is the parameter's name only if a complete type
        # precedes it: `size_t size` yes, `size_t` / `const omp_interop_t` /
        # `struct cudaExtent` no (there it IS the type).
        if prefix and prefix[-1] not in _TAGS and any(tok not in (_QUALIFIERS | _TAGS) for tok in prefix):
            name = last
            tokens = prefix
    if not tokens:
        raise ValueError(f"parameter has no type: {text!r}")
    stars = [i for i, tok in enumerate(tokens) if tok == "*"]
    first_star = stars[0] if stars else len(tokens)
    pointee = tokens[stars[-2] + 1 if len(stars) > 1 else 0:stars[-1]] if stars else tokens
    depth = len(stars) + (1 if array_suffix else 0)
    return {
        "name": name,
        "c_type": _render(tokens),
        "base_type": " ".join(tok for tok in tokens[:first_star] if tok not in _QUALIFIERS),
        "array_suffix": array_suffix,
        "constant": "const" in pointee,
        "pointer": depth > 0,
        "pointer_depth": depth,
    }


def render_param(p):
    """A parsed parameter back to declaration text: 'void *dst', 'omp_lock_t *'."""
    if p["name"] is None:
        return p["c_type"] + p["array_suffix"]
    sep = "" if p["c_type"].endswith("*") else " "
    return f"{p['c_type']}{sep}{p['name']}{p['array_suffix']}"


def split_top_level(text, start, end):
    """(start, end) offset spans of the comma-separated items in
    text[start:end], ignoring commas nested in parentheses."""
    spans, depth, item_start = [], 0, start
    for i in range(start, end):
        c = text[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
        elif c == "," and depth == 0:
            spans.append((item_start, i))
            item_start = i + 1
    spans.append((item_start, end))
    return spans
