"""
Collection of tests for proper use of language macros

\ctype{MPI_...} invalid
\ftype{MPI_...} invalid
\type{MPI_...} deprecated (use mpidtype or mpidtypemain
"""


import re


def test_lang_type(latex_file):
    """
    Tests for incorrect use of ctype, ftype, and type macros
    """

    patternc = re.compile(r"[^%]*(\\ctype{MPI).*")
    patternf = re.compile(r"[^%]*(\\ftype{MPI).*")
    patternt = re.compile(r"[^%]*(\\type{[^M]).*")

    for line_number, line in enumerate(latex_file.contents.split('\n')):
        match = patternc.match(line)

        assert not match, (f"{latex_file.path.name}:{line_number+1} "
                           f"contains improper ctype")

        match = patternf.match(line)

        assert not match, (f"{latex_file.path.name}:{line_number+1} "
                           f"contains improper ftype")

        match = patternt.match(line)

        assert not match, (f"{latex_file.path.name}:{line_number+1} "
                           f"contains improper type")


