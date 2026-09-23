"""
Test collection for language related concerns.
"""


import re
import pytest


@pytest.mark.parametrize('word', ['slave', 'master', 'his', 'hers', 'she', 'he', 'him', 'her', 'himself', 'herself'])
def test_undesired_words(word: str, latex_file) -> None:
    """
    Tests if any of the given undesired words are used.
    """

    msg = f"{word} found in {latex_file.path.name}"

    search = re.search(r'\b' + word.lower() + r'\b', latex_file.contents.lower(), re.DOTALL)

    assert search is None, msg
