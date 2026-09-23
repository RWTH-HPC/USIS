#!/usr/bin/env python3

'''
Regression testing tool for separate MPI Standard git repositories.
'''


import common
common.check_for_sufficient_version()


import logging
from pathlib import Path
from typing import MutableMapping, Mapping, Tuple, Iterable, Set
from collections import OrderedDict, Counter
from difflib import ndiff, SequenceMatcher
import argparse
import re
import dataclasses
from enum import Enum
from pprint import pprint
import json
import os
import sys

import patterns


class Language(Enum):
    '''
    Languages present in MPI Standard.
    '''

    LIS = 'lis'
    C = 'c'
    F08 = 'f08'
    F90 = 'f90'


class Statistics(Enum):
    '''
    Possible statistics to gather.
    '''

    DIFFERENCES = 'differences'
    INDENT_DIFFS = 'indents'
    ANGLE_DIFFS = 'angles'
    SPACE_DIFFS = 'spaces'
    TILDA_DIFFS = 'tilda'
    TOTAL_ORIG = 'original_count'
    TOTAL_MOFD = 'modified_count'
    OTHER_DIFFS = 'other'


BINDING_MAP: Mapping[str, Language] = {
        'funcdef': Language.LIS,
        'funcdef2': Language.LIS,
        'funcdefna': Language.LIS,

        'mpibind': Language.C,
        'mpibindnotint': Language.C,
        'mpitypedefbind': Language.C,
        'mpitypedefbindvoid': Language.C,
        'mpitypedefemptybind': Language.C,

        'mpifbind': Language.F90,
        'mpifsubbind': Language.F90,

        'mpifnewbind': Language.F08,
        'mpifnewsubbind': Language.F08,
    }


SMALL_CHANGE_MSG = None
BIG_CHANGE_MSG = None


def set_messages() -> None:
    '''
    Sets the small/big messages based on LINE_BREAK_LENGTH
    '''
    msg = '-- small change '
    # pylint: disable=global-statement
    global SMALL_CHANGE_MSG
    SMALL_CHANGE_MSG = msg + ('-' * (common.LINE_BREAK_LENGTH - len(msg)))

    msg = '## BIG CHANGE '
    # pylint: disable=global-statement
    global BIG_CHANGE_MSG
    BIG_CHANGE_MSG = msg + ('#' * (common.LINE_BREAK_LENGTH - len(msg)))


@dataclasses.dataclass
class Binding:
    '''
    Binding namedtuple with all relevant information.
    '''

    latex: str
    filename: Path


@dataclasses.dataclass
class API:
    '''
    The representation of a single API.
    '''

    name: str
    bindings: MutableMapping[Language, Binding]


def parse_file(filename: Path) -> MutableMapping[str, API]:
    '''
    Ingests into the database an individual file found in a chapter
    directory.
    '''

    # always skip appLang, it is an annex of bindings
    if filename.name == 'appLang-Const.tex':
        return {}

    apis: MutableMapping[str, API] = {}

    with filename.open() as latex:
        contents = latex.read()

        matches = []
        matches.extend(patterns.PATTERN_LIS_SINGLE_BINDING.findall(contents))
        matches.extend(patterns.PATTERN_LIS_DOUBLE_BINDING.findall(contents))
        matches.extend(patterns.PATTERN_LIS_NA_BINDING.findall(contents))

        matches.extend(patterns.PATTERN_C_BINDING.findall(contents))
        matches.extend(patterns.PATTERN_C_NOTINT_BINDING.findall(contents))
        matches.extend(patterns.PATTERN_C_TYPEDEF_BINDING.findall(contents))
        matches.extend(
            patterns.PATTERN_C_TYPEDEF_EMPTY_BINDING.findall(contents))
        matches.extend(
            patterns.PATTERN_C_TYPEDEF_VOID_BINDING.findall(contents))

        matches.extend(patterns.PATTERN_F08_BINDING.findall(contents))
        matches.extend(patterns.PATTERN_F08_SUB_BINDING.findall(contents))

        matches.extend(patterns.PATTERN_F90_BINDING.findall(contents))
        matches.extend(patterns.PATTERN_F90_SUB_BINDING.findall(contents))

        for match in matches:
            language = BINDING_MAP[match[1]]
            api_name = match[2].replace('\\', '').lower()

            if '_' not in api_name:
                logging.warning('found match without underscore in '
                                'identified name')
                logging.warning('%s', match)

            # add API to function database
            if api_name not in apis:
                apis[api_name] = API(api_name, {})

            api = Binding(latex=match[0],
                          filename=filename)

            apis[api_name].bindings[language] = api

    return apis


def merge_apis(db1: MutableMapping[str, API],
               db2: MutableMapping[str, API]) -> MutableMapping[str, API]:
    '''
    Merged two function sets.
    '''

    for name, api in db2.items():
        if name in db1:
            # check for equivalence
            for language, binding in db2[name].bindings.items():
                if language not in db1[name].bindings:
                    logging.error('language binding not found in db1')
                    raise RuntimeError('language binding not found in db1.')

                if binding.latex != db1[name].bindings[language].latex:
                    logging.error('Multiple same bindings found %s', name)
                    logging.error('%s %s', binding.filename,
                                  db1[name].bindings[language].filename)

                    logging.error('\n%s\n%s', binding.latex, db1[name].bindings[language].latex)
                    raise RuntimeError(f'Found {name} as duplicated in ' +
                                       'multiple files and not equivalent ' +
                                       'latex.')

            continue

        db1[name] = api

    return db1


def parse_apis(repository: Path) -> MutableMapping[str, API]:
    '''
    Ingests an entire repository of the MPI Standard and generates a
    database of all latex MPI bindings.
    '''

    functions: MutableMapping[str, API] = {}

    # identify chapter / root
    if 'chap-' in repository.name:
        pattern = '*.tex'

    else:
        pattern = 'chap-*/*.tex'

    # find all chapter directories
    for filename in repository.glob(pattern):
        if filename.is_file():

            logging.debug('reading %s', filename)
            functions = merge_apis(functions, parse_file(filename))

        else:
            logging.error('Non-file found %s', str(filename))

    return functions


def print_difference(original_binding, modified_binding, language) -> None:
    '''
    Prints the differences of the bindings.
    '''

    # preprocess bindings
    original = []
    modified = []

    # break LIS bindings to be able to compare
    if language is Language.LIS:
        tmp_o = original_binding.latex.replace('\n', '')
        tmp_m = modified_binding.latex.replace('\n', '')

        tmp_o = tmp_o.replace('\\funcarg', '#\\funcarg')
        tmp_m = tmp_m.replace('\\funcarg', '#\\funcarg')

        original.extend(tmp_o.split('#'))
        modified.extend(tmp_m.split('#'))

    else:
        original.append(original_binding.latex)
        modified.append(modified_binding.latex)

    # print the diff of the base and modified
    for base, mod in zip(original, modified):
        deltas = list(ndiff([base],
                            [mod]))

        longest = max(len(string) for string in deltas)

        for chunk_idx in range(0, longest, common.LINE_BREAK_LENGTH):
            print('`' * common.LINE_BREAK_LENGTH)
            for string_comparison in deltas:
                print(string_comparison[chunk_idx:
                                        chunk_idx + common.LINE_BREAK_LENGTH])


def print_separator(ratio: float) -> None:
    '''
    Prints the binding separator based on mismatch ratio.
    '''

    if ratio < 0.95:
        # pylint: disable=global-statement
        global BIG_CHANGE_MSG
        print(BIG_CHANGE_MSG)

    else:
        # pylint: disable=global-statement
        global SMALL_CHANGE_MSG
        print(SMALL_CHANGE_MSG)


def find_mismatch_causes(original: str, modified: str) -> Iterable[str]:
    '''
    Finds potential individual causes for a mismatch between the bindings.
    '''

    causes = []

    if identify_tilda_changes(original, modified):
        causes.append('tildas')

    if identify_spacing_changes(original, modified):
        causes.append('spacing')

    if identify_dollar_sign_changes(original, modified):
        causes.append('dollars')

    if identify_reordering(original, modified):
        causes.append('reordered')

    if len(causes) > 0:
        return causes

    return ['unknown']


def print_binding_diff(matcher, original_binding, modified_binding, language):
    '''
    Convience function to print a diff summary of a binding.
    '''

    print_separator(matcher.ratio())
    print()
    print(f'Language: {language}')
    print(f'likeness ratio {matcher.ratio()*100:0.1f}%')
    print(f'- {original_binding.filename}')
    print(f'+ {modified_binding.filename}')
    print()
    print('Probable reasons: ' + ' '.join(find_mismatch_causes(
        original_binding.latex,
        modified_binding.latex)))
    print()
    print_difference(original_binding, modified_binding, language)
    print()


def correct_weird_indentation(original: str,
                              modified: str
                              ) -> Tuple[str, str]:
    '''
    Identify "\\\\\\ \\ \\ \\ " is part of mismatch and remove.
    '''

    original = original.replace('\\\\\\ \\ \\ \\', '')
    original = original.replace('\\\\ \\ \\ \\ \\', '')

    original = original.replace('\\bindindent/', '')
    original = original.replace('\\bindindent', '')

    return (original, modified)


def correct_spacing_changes(original: str,
                            modified: str,
                            ) -> Tuple[str, str]:
    '''
    Identify spacing changes and remove them for matching.
    '''

    delta = ndiff(original, modified)
    changes = 0

    for idx, char in enumerate(delta):
        if char[0] == ' ':
            continue

        if char[0] == '-' and char[-1] == ' ':
            original = original[:changes+idx] + original[changes+idx+1:]
            changes -= 1

        if char[0] == '+' and char[-1] == ' ':
            original = original[:changes+idx] + ' ' + original[changes+idx:]

    return (original, modified)


def identify_spacing_changes(original: str,
                             modified: str
                             ) -> bool:
    '''
    Check whether spaces are the only cause for the mismatch.
    '''

    return (original.replace(' ', '').replace('\n', '') ==
            modified.replace(' ', '').replace('\n', ''))


def correct_tilda_changes(original: str,
                          modified: str,
                          ) -> Tuple[str, str]:
    '''
    Identify tilda changes and remove changes.
    '''

    original = original.replace('~', '')
    modified = modified.replace('~', '')

    return (original, modified)


def identify_tilda_changes(original: str,
                           modified: str,
                           ) -> bool:
    '''
    Check whether tildas are the only cause for the mismatch.
    '''

    return original.replace('~', '') == modified.replace('~', '')


def correct_dollar_sign(original: str,
                        modified: str,
                        ) -> Tuple[str, str]:
    '''
    Identify dollar signs and remove them.
    '''

    return (original.replace('$', ''), modified)


def identify_dollar_sign_changes(original: str,
                                 modified: str,
                                 ) -> bool:
    '''
    Identify whether dollar signs are the only cause for the mismatch.
    '''

    return original.replace('$', '') == modified.replace('$', '')


def correct_reordered(original: str,
                      modified: str
                      ) -> bool:
    '''
    Check whether the two bindings are just reordered.
    '''

    # if lengths are not equal, they cannot be 'just' reordered
    if len(original) != len(modified):
        return False

    # check for reordering
    delta = ndiff(original, modified)
    subs = []
    adds = []

    for char in delta:
        if char[0] == ' ':
            continue

        if char[0] == '-':
            subs.append(char[-1])

        if char[0] == '+':
            adds.append(char[-1])

    sub = ''.join(subs).replace('\\', '').replace(' ', '')
    add = ''.join(adds).replace('\\', '').replace(' ', '')

    if sub == add:
        # change original

        changed = ''
        for char in ndiff(original, modified):
            if char[0] in (' ', '+'):
                changed += char[-1]

            if char[0] == '-':
                continue

        original = changed

    return (original, modified)


PATTERN_C = r'[\w\*~]+'
PATTERN_F = r'[\w\*\.()=]+'


def identify_reordering(original: str, modified: str) -> bool:
    '''
    Identifies whether reordering is the problem between original and modified.
    '''

    # spacing errors break line length assumption
    # equal length means it might be reordered
    bindings = [original, modified]

    if len(bindings[0].replace(' ', '')) != len(bindings[1].replace(' ', '')):
        return False

    bindings = [b.replace('\\', '') for b in bindings]
    bindings = [b.replace('fargs', '') for b in bindings]

    # TODO can we strengthen this algorithm, we don't want false positives

    lang_sets_c = [Counter(re.findall(PATTERN_C, binding))
                   for binding in bindings]
    lang_sets_f = [Counter(re.findall(PATTERN_F, binding))
                   for binding in bindings]

    return all((lang_sets_c[0] == lang_sets_c[1],
                lang_sets_f[0] == lang_sets_f[1]))


def compare_binding(original: Binding,
                    modified: Binding,
                    language) -> None:
    '''
    Prints the difference between two latex bindings.
    '''

    matcher = SequenceMatcher(a=original.latex,
                              b=modified.latex)

    print_binding_diff(matcher,
                       original,
                       modified,
                       language)


def compare_bindings(original: MutableMapping[Language, Binding],
                     modified: MutableMapping[Language, Binding],
                     arguments: argparse.Namespace,
                     name: str
                     ) -> None:
    '''
    Compares two Latex bindings for a single API function.
    '''

    for language, original_binding in original.items():
        if skip_from_arguments(arguments, language, name):
            continue

        if language in modified:
            modified_binding = modified[language]

            if original_binding.latex != modified_binding.latex:
                # TODO check if name, language is on approved record

                matcher = SequenceMatcher(a=original_binding.latex,
                                          b=modified_binding.latex)

                print_binding_diff(matcher,
                                   original_binding,
                                   modified_binding,
                                   language)


def output_differences(original: MutableMapping[str, API],
                       modified: MutableMapping[str, API]) -> None:
    '''
    Prints out differences in the sets of functions present in
    the databases.
    '''

    original_names = set(original.keys())
    modified_names = set(modified.keys())

    print('Functions present in original, but not in modified')
    pprint(original_names.difference(modified_names))

    print()

    print('Functions present in modified, but not in original')
    pprint(modified_names.difference(original_names))


def is_known_mismatch(original_d: str, modified_d: str) -> bool:
    '''
    Tests whether the bindings differ in a known mismatch.
    '''

    # identify weird indentation
    original, modified = correct_weird_indentation(original_d, modified_d)

    if original == modified:
        print('indentation mismatch')
        return True

    # identify spacing
    original, modified = correct_spacing_changes(original, modified)

    if original == modified:
        print('spacing mismatch')
        return True

    # identify tildas
    original, modified = correct_tilda_changes(original, modified)

    if original == modified:
        print('tilda mismatch')
        return True

    # identify dollar sign
    original, modified = correct_dollar_sign(original, modified)

    if original == modified:
        print('dollar sign mismatch')
        return True

    # identify reorderings
    if identify_reordering(original_d, modified_d):
        print('reordered mismatch')
        return True

    return False


def skip_from_arguments(arguments: argparse.Namespace,
                        language: Language,
                        name: str
                        ) -> bool:
    '''
    Decide whether this binding should be skipped based on the arguments.
    '''

    if arguments.api is not None and arguments.api != name:
        return True

    skip_languages = []

    for key, value in vars(arguments).items():
        if 'skip_' in key and value:
            skip_languages.append(Language(key.replace('skip_', '')))

    logging.debug('skipping languages: %s', skip_languages)

    return language in skip_languages


def fetch_approvals(api_names: Set[str]) -> MutableMapping:
    '''
    Load or initialize the approvals json.
    '''

    if os.path.exists('approvals.json'):
        with open('approvals.json', 'r') as database:
            approvals = json.load(database)

    else:
        print('no prior approvals')
        approvals = OrderedDict()

        # add all names
        for name in api_names:
            approvals[name] = OrderedDict()

            for language in Language:
                approvals[name][str(language)] = False

    return approvals


def ask_for_approval(approvals: MutableMapping,
                     language: Language,
                     api_name: str) -> None:
    '''
    Ask user for approval interactively.
    '''

    # ask user for approval
    while True:
        command = input('approve(a), skip(s), exit(x): ')

        if command in ('a', 's', 'x'):
            break

        print('unknown command')

    # handle user command
    if command == 'a':
        approvals[api_name][str(language)] = True

        # write out approvals
        with open('approvals.json', 'w') as database:
            json.dump(approvals, database, indent=4, sort_keys=True)

    elif command == 's':
        pass

    elif command == 'x':
        # write out approvals
        with open('approvals.json', 'w') as database:
            json.dump(approvals, database, indent=4, sort_keys=True)

        sys.exit(0)


def compare_apis_interactive(original: MutableMapping[str, API],
                             modified: MutableMapping[str, API],
                             arguments: argparse.Namespace,
                             ) -> MutableMapping[Statistics, int]:
    '''
    Interactively allow user to suppress future warnings.
    '''

    common_names = sorted(set(original.keys()) & set(modified.keys()))

    # either load approvals or initialize
    approvals = fetch_approvals(common_names)

    # iterate all names for approval
    for name in common_names:
        # make names nicer to read
        name = name.replace(r'\\', '')

        # if only predefined functions, if it isnot one, then skip
        if arguments.predefinedfuncs and '_fn' not in name:
            continue

        # same for callback functions
        if arguments.callbacks and '_function' not in name:
            continue

        # line shorteners
        original_bindings = original[name].bindings
        modified_bindings = modified[name].bindings

        for language in original_bindings.keys():
            if skip_from_arguments(arguments, language, name):
                continue

            # skip if language variant not present in modified
            if language not in modified_bindings:
                print((f'skipping {name} in {language} '
                       'NOT PRESENT IN NEW BINDINGS'))

                logging.error('Binding not found %s %s', name, language)

                continue

            # skip already approved (name, language)
            if name in approvals:
                if (str(language) in approvals[name] and
                        approvals[name][str(language)]):
                    print(f'skipping {name} in {language} -- already approved')
                    continue

            else:
                approvals[name] = {}

            # if weird mpifoverloadOnlyInAnnex
            # TODO this is a TODO GLOBAL
            if ('mpifoverloadOnlyInAnnex' in
                    original_bindings[language].latex):
                print(f'skipping {name} due to weird macros')

                continue

            # skip and approve if identical bindings
            if (original_bindings[language].latex ==
                    modified_bindings[language].latex):
                logging.debug('binding files %s %s',
                              original_bindings[language].filename,
                              modified_bindings[language].filename)
                print((f'*** auto-approving {name} in {language} '
                       '-- bindings are equivalent ***'))

                approvals[name][str(language)] = True

                continue

            # automatically approve known cases
            if (arguments.autoidentify and
                    is_known_mismatch(original_bindings[language].latex,
                                      modified_bindings[language].latex)):
                print((f'*** auto-approving {name} in {language} '
                       '-- known mismatch ***'))

                approvals[name][str(language)] = True

                continue

            # print diff for name and language
            print('\n' * 10)
            print('\nName: ' + name)
            compare_binding(original_bindings[language],
                            modified_bindings[language],
                            language)

            ask_for_approval(approvals, language, name)

            print('')

    # write out approvals
    with open('approvals.json', 'w') as database:
        json.dump(approvals, database, indent=4, sort_keys=True)


def compare_apis(original: MutableMapping[str, API],
                 modified: MutableMapping[str, API],
                 arguments: argparse.Namespace
                 ) -> None:
    '''
    Compares to function databases and returns statistics.
    '''

    # load approvals or initialize approvals

    common_names = set(original.keys()) & set(modified.keys())

    # approvals = fetch_approvals(common_names)
    # for skipping approved differences

    output_differences(original, modified)

    for function_name in common_names:
        compare_bindings(original[function_name].bindings,
                         modified[function_name].bindings,
                         arguments,
                         function_name)


def parse_arguments() -> argparse.Namespace:
    '''
    Parse command line arguments nicely.
    '''

    parser = argparse.ArgumentParser(prog='MPI Bindings Regression Tool')

    parser.add_argument('--log',
                        default='warning',
                        type=str,
                        help='Set the python logging level')

    parser.add_argument('--interactive',
                        action='store_true',
                        help='Interactive approval mode')

    parser.add_argument('--stats',
                        action='store_true')

    parser.add_argument('--autoidentify',
                        action='store_true',
                        help=('Automatically approves known approved mismatch.'
                              'Spacing, tildas, etc...'))

    parser.add_argument('--skip-lis',
                        action='store_true')
    parser.add_argument('--skip-c',
                        action='store_true')
    parser.add_argument('--skip-f90',
                        action='store_true')
    parser.add_argument('--skip-f08',
                        action='store_true')

    parser.add_argument('--api',
                        default=None)

    parser.add_argument('--callbacks',
                        action='store_true')
    parser.add_argument('--predefinedfuncs',
                        action='store_true')

    parser.add_argument('original', type=str)
    parser.add_argument('modified', type=str)

    arguments = parser.parse_args()

    # check for valid input
    if not arguments:
        parser.print_help()

    return arguments


def main() -> None:
    '''
    Main function for regression tool.
    '''

    common.check_for_sufficient_version()
    common.set_line_width_to_terminal()
    set_messages()

    # handle command line arguments
    arguments = parse_arguments()
    if not arguments:
        return

    common.set_logging_level(arguments.log)

    # parse bindings from latex documents
    original = parse_apis(Path(arguments.original))
    modified = parse_apis(Path(arguments.modified))

    if arguments.interactive:
        compare_apis_interactive(original, modified, arguments)

    else:
        compare_apis(original, modified, arguments)


if __name__ == '__main__':
    main()
