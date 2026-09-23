"""
"""

from pathlib import Path
import json
import logging


import pytest


@pytest.fixture(scope="session")
def database():
    """
    Load the database.
    """

    path = Path.cwd()
    found = list(path.glob('apis.json'))
    while not found:
        if path == Path(path.root):
            pytest.exit('apis.json not found, need to execute make')

        path = path.parent
        found = list(path.glob('apis.json'))

    with (path / 'apis.json').open() as apis:
        return json.load(apis)
