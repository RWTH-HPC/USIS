#!/usr/bin/env python3

'''
MPI Binding emitter tool, consumes latex files and a prepass json file and
produces file latex compatible MPI bindings.
'''


# the version check is done here for clarity
import common
common.check_for_sufficient_version()


import argparse
import logging
from pathlib import Path
import re
import json
from typing import Mapping, List


import bindingtypes
import bindingc
import bindingf90
import bindingf08
import bindinglis
import patterns
import binding
from userfuncs import *


LANGUAGE_MODULES_SMALL = {
        'lis': (bindinglis, '', bindingtypes.LIS_KIND_MAP),
        'c': (bindingc, '', bindingtypes.SMALL_C_KIND_MAP),
        'f08': (bindingf08, '', bindingtypes.SMALL_F08_KIND_MAP),
        'f90': (bindingf90, '', bindingtypes.SMALL_F90_KIND_MAP)
        }


LANGUAGE_MODULES_BIG = {'lis': (bindinglis, '', bindingtypes.LIS_KIND_MAP),
                        'c': (bindingc, '', bindingtypes.BIG_C_KIND_MAP),
                        'f08': (bindingf08, '', bindingtypes.BIG_F08_KIND_MAP),
                        'f90': (bindingf90, '', bindingtypes.BIG_F90_KIND_MAP)}


LANGUAGE_MODULES_POLY = {'lis': [(bindinglis, '', bindingtypes.LIS_KIND_MAP)],
                         'c': [(bindingc, '', bindingtypes.SMALL_C_KIND_MAP),
                               (bindingc, '_c', bindingtypes.BIG_C_KIND_MAP)],
                         'f08': [(bindingf08, '', bindingtypes.SMALL_F08_KIND_MAP),
                                 (bindingf08, '_c', bindingtypes.BIG_F08_KIND_MAP)],
                         'f90': [(bindingf90, '', bindingtypes.SMALL_F90_KIND_MAP)]
                         }


def _latex_backslash_formatter(latex: str) -> str:
    """
    Makes sure that underscores are correctly escaped.
    """

    # reset to Python strings
    latex = latex.replace(r'\_', '_')

    # escape all underscores
    latex = latex.replace('_', r'\_')

    return latex


def emit_callback_index_macros(
        ref: Mapping,
        render: str,
        postfix: str = ''
        ) -> List[str]:
    """
    Emits all appropriate callbackindex macro calls, which should be placed
    before the language binding.
    """

    if render not in ('c', 'f90'):
        return []

    funcs = dict()

    # exclude F08, exclude duplicate

    for parameter in ref['parameters']:
        if parameter['func_type']:
            funcs[parameter['func_type']] = parameter['kind']

    calls = []

    for function, kind in funcs.items():
        if render == 'c':
            if "POLY" in kind:
                name = f'{function}{postfix}'

            else:
                name = function

        else:
            name = function[4:].upper()

        name = name.replace('_', r'\_')

        calls.append(f'\\mpicallbackindex{{{name}}}%')

    return calls


def emit_4_0_bindings(reference: Mapping, parseset: Mapping) -> str:
    """
    Emit bindings using the MPI-4.0 style:

    - LIS
    - If there are count or displacement arguments:
        - C:
            - MPI_Foo with int count/displacement
            - MPI_Foo with MPI_Count count/MPI_Aint displacement
            - MPI_Foo_l with MPI_Count count/MPI_Aint displacement
              (^^ unless no_l_variant() was invoked)
        - F08:
            - MPI_Foo with int count/displacement
            - MPI_Foo with MPI_Count count/MPI_Aint displacement
        - F90:
            - MPI_Foo with int count/displacement
    - otherwise, emit one binding for each of the following:
        - C
        - F08
        - F90
    """

    output = []

    for render in parseset['temporaries']['renders']:
        # lookup and define reference
        if parseset['temporaries']['reference'] is not None:
            ref = reference[parseset['temporaries']['reference']]
        else:
            ref = parseset

        render_main = ref['attributes']['render_main']
        if 'render_main' in parseset['temporaries']:
            ref['attributes']['render_main'] = parseset['temporaries']['render_main']

        # check if POLY type
        if any((param['kind'].startswith('POLY'))
               for param in ref['parameters']):
            # Most functions want to print an "_l" variant.  But some do
            # not (e.g., MPI_GET_ELEMENTS, because there's a different
            # MPI_GET_ELEMENTS_X function).
            # can we just assume yes, _x functions should not have poly
            # types
            for language, postfix, kind_map in LANGUAGE_MODULES_POLY[render]:
                latex = _latex_backslash_formatter(
                    language.emit_binding(ref, postfix, kind_map))

                if latex not in ('', '\n'):
                    output.extend(emit_callback_index_macros(ref, render, postfix))
                    output.append(latex)

        else:
            # Note that the distinction between "SMALL" and "BIG" kind
            # maps doesn't matter here, because the only difference
            # between them is the POLY* types, and per the "if"
            # conditional above, if we get to this block of code, there
            # are not POLY* types to be rendered.
            language, postfix, kind_map = LANGUAGE_MODULES_BIG[render]

            latex = _latex_backslash_formatter(
                language.emit_binding(ref, postfix, kind_map))

            if latex not in ('', '\n'):
                output.extend(emit_callback_index_macros(ref, render))
                output.append(latex)
        ref['attributes']['render_main'] = render_main

    # render the f90_overload text if required
    if parseset['temporaries']['f90_overload_render']:
        ref = reference[parseset['temporaries']['f90_overload_render']]

        output.append(r"\begin{verbatim}")

        # convert index format to normal text format
        for line in ref['attributes']['f90_index_overload'].split(r'\\'):
            clean = (line.strip()[2:]).strip().replace(r'\>', '    ').replace(r'\_', '_').replace(r'\&', '&')

            output.append(clean)

        output.append(r"\end{verbatim}")

    return '\n'.join(output)


def emit_bindings(reference: Mapping, parseset: Mapping) -> str:
    '''
    Emit bindings for thise parseset.
    '''

    output = []

    if parseset['attributes']['predefined_function']:
        output.append('\\OnlyForAutomaticAnnexGeneration{%')

    # output appropriate binding
    output.append(emit_4_0_bindings(reference, parseset))

    if parseset['attributes']['predefined_function']:
        output.append('}%')

    return '\n'.join(output)


def process_pass(reference: Mapping,
                 contents: str,
                 pattern: re.Pattern,
                 dryrun: bool = False) -> str:
    '''
    Performs a binding emission pass with the given pattern.
    '''

    output = []
    last_match_end = 0

    while True:
        match = pattern.search(contents, last_match_end)

        # if no more match, then done with pass
        if not match:
            break

        # output contents up to match
        if not dryrun:
            output.append(contents[last_match_end: match.start()])

        # translate pattern match to binding
        parseset = binding.execute_binding(match[1])
        output.append(emit_bindings(reference, parseset))
        output.append('\n')

        last_match_end = match.end()

    # output remainder of contents
    if not dryrun:
        output.append(contents[last_match_end:])

    return ''.join(output)


def process_file(prepass: Path,
                 filename: Path,
                 dryrun: bool = False) -> str:
    '''
    Processes the given input file.
    '''

    with prepass.open(mode='r') as ref_file:
        reference = json.load(ref_file)

        with filename.open(mode='r') as latex:
            # read entire file
            contents = latex.read()

            output = process_pass(reference,
                                  contents,
                                  patterns.MPI_BINDING_PATTERN,
                                  dryrun)

    return output


def parse_arguments() -> argparse.Namespace:
    """
    Parses the arguments to the MPI Binding Tool.
    """

    parser = argparse.ArgumentParser(
        description='MPI Standard Language Bindings Generation Tool')

    parser.add_argument('--log', default='WARNING')
    parser.add_argument('--dryrun', action='store_true')

    parser.add_argument('prepass')
    parser.add_argument('file',
                        help='latex input, "-" allows stdin')

    return parser.parse_args()


def main() -> None:
    """
    Main function of the MPI Binding Tool.
    """

    common.check_for_sufficient_version()
    arguments = parse_arguments()
    common.set_logging_level(arguments.log)

    # The LIS bindings module needs a separate setup call
    bindinglis.init(bindingtypes.LIS_KIND_MAP)

    # decided between file or stdin
    if arguments.file != '-':
        logging.debug('Using %s as latex file.', arguments.file)

        output = process_file(Path(arguments.prepass),
                              Path(arguments.file),
                              arguments.dryrun)

    else:
        logging.debug('Using stdin as latex.')

        output = process_file(Path(arguments.prepass),
                              Path('/dev/stdin'),
                              arguments.dryrun)

    # output replaced latex
    print(output)


if __name__ == '__main__':
    main()
