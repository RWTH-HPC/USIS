#!/usr/bin/env python3

"""
MPI Binding prepass tool, consumes the latex mpi-binding blocks and
generates a json document for all bindings as an intermediary respresentation.
"""


# the version check is done here for clarity
import common

common.check_for_sufficient_version()


import argparse
import logging
from pathlib import Path
from typing import Mapping
import json


import patterns
import binding


def parse_file(filename: Path) -> Mapping:
    """
    Parse given file into a dictionary.
    """

    logging.info("parsing %s", filename)

    dataset = {}

    with filename.open(mode="r") as latex:
        # read entire file
        contents = latex.read()

        # search through file for bindings
        last_match_end = 0

        while True:
            # find next match
            match = patterns.MPI_BINDING_PATTERN.search(contents, last_match_end)
            if not match:
                break

            # convert binding
            try:
                parseset = binding.execute_binding(match[1], require_definition=True)
            except Exception as exception:
                print("Error happened at " + match.group(0))
                raise exception

            if parseset and parseset["temporaries"]["reference"] is None:
                # remove temporaries when writing api json
                del parseset["temporaries"]

                dataset[parseset["name"].lower()] = parseset

            # continue searching
            last_match_end = match.end()

    return dataset


def parse_directory(directory: Path) -> Mapping:
    """
    Parse the given directory.
    """

    dataset = {}

    logging.info("searching directory %s", directory)

    for filename in directory.glob("**/*.tex"):
        fileset = parse_file(filename)

        # merge datasets
        # function_name must be unique
        dataset.update(fileset)

    return dataset


def parse_arguments() -> argparse.Namespace:
    """
    Parses the arguments to the MPI Binding Tool.
    """

    parser = argparse.ArgumentParser(
        description="MPI Standard Language Bindings Generation Tool"
    )

    parser.add_argument("--log", default="WARNING")

    parser.add_argument("directory")
    parser.add_argument("output")

    return parser.parse_args()


def main() -> None:
    """
    Main function of the MPI Binding Tool.
    """

    arguments = parse_arguments()
    common.set_logging_level(arguments.log)

    # parse directory
    dataset = parse_directory(Path(arguments.directory))

    # write out json document
    with Path(arguments.output).open(mode="w") as output:
        json.dump(dataset, output, indent=4, sort_keys=True)


if __name__ == "__main__":
    main()
