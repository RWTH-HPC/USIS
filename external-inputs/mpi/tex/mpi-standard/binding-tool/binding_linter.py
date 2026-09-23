#!/usr/bin/env python3

"""
Binding linting tool for the MPI Standard.
"""


# pylint: disable=import-error, wrong-import-order, wrong-import-position
# flake8: noqa: E402


# the version check is done here for clarity
import common
common.check_for_sufficient_version()


import subprocess
from pathlib import Path
import argparse
import logging


import patterns


def lint_binding(binding: str) -> str:
    """
    Lint mpi-binding block using the black formatter.
    """

    # clean spaces from front
    binding = common.remove_unexpected_indentation(binding)

    process = subprocess.run(['black', '--code', binding,
                              '--target-version', 'py37',
                              '--line-length', str(80 - 4)],
                             check=True,
                             capture_output=True,
                             text=True)

    # process = subprocess.run(['autopep8', '-'],
    #                          input=binding,
    #                          check=True,
    #                          capture_output=True,
    #                          text=True)

    return process.stdout


def wrap_binding(binding: str) -> str:
    """
    Wraps the python source code into a latex binding.
    """

    indent = 4

    lines = binding.split('\n')
    lines = [(' '*indent + line) for line in lines[:-2]]

    return ('\\begin{mpi-binding}\n' +
            '\n'.join(lines) +
            '\n\\end{mpi-binding}\n')


def lint_file(file: Path, dryrun: bool = False) -> None:
    """
    Search through file for mpi-binding blocks and lint them.
    """

    logging.info('linting file %s', file)

    output = []

    # read in original latex
    with file.open(mode='r') as latex:
        # read entire file
        contents = latex.read()

        last_match_end = 0

        while True:
            # find next match
            match = patterns.MPI_BINDING_PATTERN.search(contents,
                                                        last_match_end)
            if not match:
                break

            # output all text up to binding
            if not dryrun:
                output.append(contents[last_match_end: match.start()])

            # lint binding text
            linted = lint_binding(match[1])

            # inject linted code
            output.append(wrap_binding(linted))

            # continue stepping through file
            last_match_end = match.end()

        if not dryrun:
            output.append(contents[last_match_end:])

    if not output:
        raise RuntimeError('Nothing to emit.')

    if dryrun:
        print('\n'.join(output))

    else:
        # output original latex with formatted bindings
        with file.open(mode='w') as latex:
            latex.write(''.join(output))


def lint_directory(directory: Path, dryrun: bool = False) -> None:
    """
    Given a directory file latex files and lint them.
    """

    logging.info('linting directory %s', directory)

    # determine if chapter directory
    if 'chap-' in directory.name:
        files = directory.glob('*.tex')

    else:
        files = directory.glob('chap-*/*.tex')

    for file in files:
        lint_file(file, dryrun)


def parse_arguments() -> argparse.Namespace:
    """
    Parses the arguments to the MPI Binding Tool.
    """

    parser = argparse.ArgumentParser(
        description='MPI Standard Language Bindings Generation Tool')

    parser.add_argument('--log', default='WARNING')
    parser.add_argument('--dryrun', action='store_true')
    parser.add_argument('directory')

    return parser.parse_args()


def main() -> None:
    """
    Main function for the linting tool.
    """

    common.check_for_sufficient_version()

    arguments = parse_arguments()
    common.set_logging_level(arguments.log)

    lint_directory(Path(arguments.directory), arguments.dryrun)


if __name__ == '__main__':
    main()
