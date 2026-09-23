"""
Collection of tests for --- spacing accoridng to instr.tex.

"word---word" valid
"word --- word" invalid
"""


import re


def test_em_dash_spacing(latex_file):
    """
    Tests for incorrect em dash spacing.
    """

    pattern = re.compile(r"[^%]*(?: --- ).*")

    for line_number, line in enumerate(latex_file.contents.split('\n')):
        match = pattern.match(line)

        assert not match, (f"{latex_file.path.name}:{line_number+1} "
                           f"contains ' --- '")


def test_no_newlines_near_em_dash(latex_file):
    """
    Tests whether there is an em dash with a new line character near it.
    """

    pattern_end = re.compile(r"[^%-]*---\s?$")
    pattern_begin = re.compile(r"^\s?---.*")

    for line_number, line in enumerate(latex_file.contents.split('\n')):
        match_end = pattern_end.match(line)
        match_begin = pattern_begin.match(line)

        assert not match_end, (f"{latex_file.path.name}:{line_number+1} "
                               f"contains '---' at end")

        assert not match_begin, (f"{latex_file.path.name}:{line_number+1} "
                                 f"contains '---' at beginning")
