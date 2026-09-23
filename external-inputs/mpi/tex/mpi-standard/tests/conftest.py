"""
Defines general fixtures for tests.
"""


# pylint: disable=redefined-outer-name


from pathlib import Path
from dataclasses import dataclass
from typing import Iterable


import pytest


@dataclass
class LatexFile:
    """
    Contains the path and the contents of a latex file.
    """

    path: Path
    contents: str


def unrendered_latex_files() -> Iterable[Path]:
    """
    Finds all unrendered latex files.

    "*.tex" not "*-rendered.tex"
    """

    paths = Path.cwd().glob("chap-*/*.tex")

    return (path for path in paths if '-rendered' not in path.name)


@pytest.fixture(scope="session",
                params=unrendered_latex_files(),
                ids=(path.stem for path in unrendered_latex_files()))
def latex_file(request) -> LatexFile:
    """
    Read all Standard latex files.
    """

    with request.param.open() as latex:
        return LatexFile(request.param, latex.read())


@dataclass
class BindingLatex:
    """
    Contains the latex of the LIS, C, F08 and F90 of a single MPI procedure.
    """

    name: str
    lang_lis: str = None
    lang_c: str = None
    lang_f08: str = None
    lang_f09: str = None


@pytest.fixture(scope="session")
def binding_latex(request) -> BindingLatex:
    """
    This fixture provides access to all bindings found in the -rendered.tex
    files.
    """

    raise NotImplementedError
