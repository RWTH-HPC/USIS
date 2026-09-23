"""
Test for warnings listed in the file `warnindex.txt`.
"""

import pytest

def test_nonempty_warnindex() -> None:
    """
    Tests if the file `warnindex.txt` created during build is actually empty.
    """

    with open(r"warnindex.txt", 'r') as fp:
        lines = len(fp.readlines())
        assert lines == 0, "Please fix the index warnings listed in `warnindex.txt`."
