"""
A collection of tests which enforce the decisions made about specific usage
of words in the Standard.
"""


# pylint: disable=redefined-outer-name


import re


import pytest


@pytest.mark.parametrize("word",
                         ["intercommunicator",
                          "Intercommunicator",
                          "intracommunicator",
                          "Intracommunicator",
                          "intra-Communicator",
                          "inter-Communicator"])
def test_incorrect_word_usage(word: str, latex_file) -> None:
    """
    Tests if word is used in file, if so, then fails.

    The given words are incorrect to use in the MPI Standard.

    They should be:
        intercommunicator -> inter-communicator
        Intercommunicator -> Inter-communicator

        intracommunicator -> intra-communicator
        Intracommunicator -> Intra-communicator
    """

    match = re.search(word, latex_file.contents)

    assert match is None, f"file {latex_file.path.name} contains {word}"


@pytest.mark.parametrize("word",
                         ["Inter-Communicator",
                          "Intra-Communicator"])
def test_word_only_in_titles(word: str, latex_file) -> None:
    """
    Tests whether the word only appears in titles.
    """

    titles = (r"(?:part|chapter|section|subsection|subsubsection"
              r"|paragraph|subparagraph|paraheading)")

    pattern = re.compile(r".*\\" + titles + r"\*?\{[^}]*?" + word + r"[^}]*?\}.*")

    for line_number, line in enumerate(latex_file.contents.split('\n')):
        # only look at lines that have the "word"
        if word in line:
            # search line for valid title
            match = pattern.search(line)

            assert match, (f"{latex_file.path.name}:{line_number+1} contains "
                           f"{word} without being a title")


@pytest.mark.parametrize("word",
                         ["Inter-communicator",
                          "inter-communicator",
                          "Intra-communicator",
                          "intra-communicator"])
def test_word_not_in_titles(word: str, latex_file) -> None:
    """
    Tests whether the word only appears outside titles.
    """

    titles = (r"(?:part|chapter|section|subsection|subsubsection"
              r"|paragraph|subparagraph)")

    pattern = re.compile(r".*\\" + titles + r"\{[^}]*?" + word + r"[^}]*?\}.*")

    for line_number, line in enumerate(latex_file.contents.split('\n')):
        # only look at lines with "word"
        if word in line:
            # search line for valid
            match = pattern.search(line)

            assert not match, (f"{latex_file.path.name}:{line_number+1} "
                               f"contains {word} in a title")
