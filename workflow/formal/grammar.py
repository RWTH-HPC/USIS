"""
Reference/selector-grammar validator -- the enforcement half of
docs/schema/reference-grammar.md's normative EBNF (added 2026-07-19).

Until this existed, grammar strings (participants[].selector,
data_flow[].offset, tool_integration.invariants) were validated by nothing
at all -- they are plain `string`-typed schema fields, checked only by
convention. That is how an invented `scope:all_pes` token once slipped
through, and why the one part of the schema consumers must *parse* now has
its own validator.

Pure recursive-descent parser, zero dependencies, zero I/O in the parse
path -- same purity bar as expand.py. Three entry points matching the
EBNF's three start symbols:

    validate_selector(s)   -- participants[].selector
    validate_offset(s)     -- data_flow[].offset / source.offset
    validate_invariant(s)  -- tool_integration.invariants[] (the one context
                              where bare parameter names, UPPERCASE PPM
                              constants, and comm_size() are legal)

plus two structural helpers:

    validate_match_key(s)  -- sync.matching.match_keys[] elements: a
                              param_ref or a documented match-key token
                              (currently exactly "self_rank_as_source")
    validate_formal_grammar(formal) -- walk a fully-inlined formal block and
                              check every grammar-typed string in it; returns
                              a list of error strings (empty = clean).

All single-string validators raise GrammarError with the offending string
and position. Strings still containing "{{slot}}" placeholders (shape
*templates*, pre-expansion) are NOT this module's input -- validate the
expansion, not the template; validate_formal_grammar raises if it meets one,
since a placeholder in post-expansion output is a bug in its own right.
"""

import re

MATCH_KEY_TOKENS = frozenset({"self_rank_as_source"})

_TOKEN_RE = re.compile(r"""
    \s*(?:
      (?P<op2>==|!=|>=|<=|\|\||&&)
    | (?P<op1>[!()<>*+,\-])
    | (?P<param>param:[A-Za-z_][A-Za-z0-9_]*)
    | (?P<int>\d+)
    | (?P<name>[A-Za-z_][A-Za-z0-9_]*)
    )""", re.VERBOSE)

_BUILTIN_CALLS = {"rank_in", "is_neighbor", "extent_size", "comm_size"}


class GrammarError(ValueError):
    pass


def _tokenize(s):
    tokens = []
    pos = 0
    while pos < len(s):
        m = _TOKEN_RE.match(s, pos)
        if m is None or m.end() == m.start():
            # nothing matched, or only whitespace matched with no token
            rest = s[pos:].strip()
            if not rest:
                break
            raise GrammarError(f"unrecognized token at position {pos} in {s!r}: {rest[:20]!r}")
        kind = m.lastgroup
        tokens.append((kind, m.group(kind), m.start(kind) if m.group(kind) else pos))
        pos = m.end()
    return tokens


class _Parser:
    def __init__(self, s, mode):
        self.s = s
        self.mode = mode  # "selector" | "offset" | "invariant"
        self.tokens = _tokenize(s)
        self.i = 0

    # -- token helpers ------------------------------------------------------
    def _peek(self):
        return self.tokens[self.i] if self.i < len(self.tokens) else (None, None, len(self.s))

    def _next(self):
        tok = self._peek()
        self.i += 1
        return tok

    def _expect(self, value):
        kind, text, pos = self._next()
        if text != value:
            raise GrammarError(f"expected {value!r} at position {pos} in {self.s!r}, got {text!r}")

    def _fail(self, why):
        _kind, text, pos = self._peek()
        raise GrammarError(f"{why} at position {pos} in {self.s!r} (near {text!r})")

    def _done(self):
        return self.i >= len(self.tokens)

    def _assert_consumed(self):
        if not self._done():
            self._fail("unexpected trailing input")

    # -- boolean expression layer (selector / invariant) --------------------
    def or_expr(self):
        self.and_expr()
        while self._peek()[1] == "||":
            self._next()
            self.and_expr()

    def and_expr(self):
        self.unary()
        while self._peek()[1] == "&&":
            self._next()
            self.unary()

    def unary(self):
        kind, text, _pos = self._peek()
        if text == "!":
            self._next()
            self.unary()
            return
        if text == "(":
            self._next()
            self.or_expr()
            self._expect(")")
            return
        self.comparison()

    def comparison(self):
        self.operand()
        kind, text, _pos = self._peek()
        if text in ("==", "!=", ">=", "<=", ">", "<"):
            self._next()
            self.operand()
            return
        if kind == "name" and text == "in":
            self._next()
            self.scope()
            return
        self._fail("expected a comparison operator or 'in'")

    def scope(self):
        kind, text, _pos = self._next()
        if kind == "param":
            return
        if kind == "name" and text == "all_pes":
            return
        raise GrammarError(f"scope must be a param: ref or 'all_pes' in {self.s!r}, got {text!r}")

    def operand(self):
        kind, text, _pos = self._peek()
        if kind == "param":
            self._next()
            return
        if kind == "int":
            self._next()
            return
        if kind == "name":
            if text == "rank":
                self._next()
                return
            if text in _BUILTIN_CALLS:
                self._builtin_call()
                return
            if self.mode == "invariant":
                # bare parameter names (count, comm) and UPPERCASE PPM
                # constants (MPI_COMM_NULL) are legal in invariants only.
                self._next()
                return
            self._fail(f"bare identifier {text!r} is not legal outside invariants")
        self._fail("expected an operand")

    def _builtin_call(self):
        _kind, name, _pos = self._next()
        self._expect("(")
        if name == "rank_in":
            self._param_arg()
        elif name == "comm_size":
            if self.mode != "invariant":
                self._fail("comm_size() is legal only in invariants")
            kind, _text, _p = self._next()
            if kind not in ("param", "name"):
                self._fail("comm_size() takes a param: ref or a bare parameter name")
        elif name == "is_neighbor":
            self.operand()
            self._expect(",")
            self._param_arg()
        elif name == "extent_size":
            if self.mode != "offset":
                self._fail("extent_size() is legal only in offset expressions")
            self._param_arg()
            self._expect(",")
            self._param_arg()
        self._expect(")")

    def _param_arg(self):
        kind, text, pos = self._next()
        if kind != "param":
            raise GrammarError(f"expected a param: ref at position {pos} in {self.s!r}, got {text!r}")

    # -- arithmetic layer (offset) ------------------------------------------
    def offset_expr(self):
        self.term()
        while self._peek()[1] in ("+", "-"):
            self._next()
            self.term()

    def term(self):
        self.factor()
        while self._peek()[1] == "*":
            self._next()
            self.factor()

    def factor(self):
        kind, text, _pos = self._peek()
        if text == "(":
            self._next()
            self.offset_expr()
            self._expect(")")
            return
        if kind == "param" or kind == "int":
            self._next()
            return
        if kind == "name":
            if text == "rank":
                self._next()
                return
            if text in ("rank_in", "extent_size"):
                self._builtin_call()
                return
        self._fail("expected an offset factor (rank, rank_in(), extent_size(), param: ref, integer)")


def validate_selector(s):
    """participants[].selector: 'self' as the whole selector, or a boolean expression."""
    if not isinstance(s, str) or not s.strip():
        raise GrammarError(f"selector must be a non-empty string, got {s!r}")
    if s.strip() == "self":
        return
    p = _Parser(s, "selector")
    p.or_expr()
    p._assert_consumed()


def validate_offset(s):
    if not isinstance(s, str) or not s.strip():
        raise GrammarError(f"offset must be a non-empty string, got {s!r}")
    p = _Parser(s, "offset")
    p.offset_expr()
    p._assert_consumed()


def validate_invariant(s):
    if not isinstance(s, str) or not s.strip():
        raise GrammarError(f"invariant must be a non-empty string, got {s!r}")
    p = _Parser(s, "invariant")
    p.or_expr()
    p._assert_consumed()


def validate_match_key(s):
    if not isinstance(s, str):
        raise GrammarError(f"match_key must be a string, got {s!r}")
    if s.startswith("param:") and re.fullmatch(r"param:[A-Za-z_][A-Za-z0-9_]*", s):
        return
    if s in MATCH_KEY_TOKENS:
        return
    raise GrammarError(
        f"match_key {s!r} is neither a param: ref nor a documented match-key token "
        f"({sorted(MATCH_KEY_TOKENS)}) -- see docs/schema/reference-grammar.md"
    )


def validate_formal_grammar(formal):
    """Walk a fully-inlined formal block; return a list of error strings (empty = clean).

    Checks: participants[].selector, data_flow[].offset, structural source
    offsets, sync.matching.match_keys[]. Raises GrammarError immediately if a
    string still contains a '{{slot}}' placeholder -- post-expansion output
    must never carry one.
    """
    errors = []

    def _check(fn, value, where):
        if value is None:
            return
        if isinstance(value, str) and "{{" in value:
            raise GrammarError(f"{where}: unexpanded slot placeholder in post-expansion output: {value!r}")
        try:
            fn(value)
        except GrammarError as e:
            errors.append(f"{where}: {e}")

    if formal is None:
        return errors

    for i, p in enumerate(formal.get("participants") or []):
        _check(validate_selector, p.get("selector"), f"participants[{i}].selector")

    for i, df in enumerate(formal.get("data_flow") or []):
        _check(validate_offset, df.get("offset"), f"data_flow[{i}].offset")
        source = df.get("source")
        if isinstance(source, dict):
            # structural's and reduced's per-recipient slice offset
            _check(validate_offset, source.get("offset"), f"data_flow[{i}].source.offset")
            # gathered: the contributing participant's placement offset
            _check(validate_offset, source.get("placement_offset"), f"data_flow[{i}].source.placement_offset")

    sync = formal.get("sync") or {}
    matching = sync.get("matching")
    if isinstance(matching, dict):
        for i, mk in enumerate(matching.get("match_keys") or []):
            _check(validate_match_key, mk, f"sync.matching.match_keys[{i}]")

    return errors
