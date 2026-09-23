'''
This includes common functions that all tools require.
'''


import sys
import logging


def check_for_sufficient_version() -> None:
    '''
    Check that python version is at least 3.7.
    '''

    logging.info('python version detected %s', sys.version_info)

    if not (sys.version_info.major >= 4 or
            (sys.version_info.major == 3 and sys.version_info.minor >= 7)):
        raise RuntimeError('This python installation is too old! '
                           'Use Python 3.7 or later')


# the version check is done here for clarity
check_for_sufficient_version()


import subprocess
import re


LINE_BREAK_LENGTH = 80


def set_logging_level(log_level: str) -> None:
    '''
    Set the logging level to the one specified on the command line.
    '''

    # convert string to numeric level
    numeric_level = getattr(logging, log_level.upper(), None)

    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % log_level)

    logging.basicConfig(level=numeric_level)




def set_line_width_to_terminal() -> None:
    '''
    Sets the LINE_BREAK_LENGTH to the terminal width.
    '''

    proc = subprocess.run(['stty', 'size'],
                          capture_output=True,
                          check=False,
                          text=True)

    if proc.returncode == 0:
        _, columns = proc.stdout.split()

        # pylint: disable=global-statement
        global LINE_BREAK_LENGTH
        LINE_BREAK_LENGTH = int(columns)


def remove_unexpected_indentation(contents: str) -> str:
    '''
    Removes leading spaces from every line.
    '''

    # first line indicates indent
    match = re.match(r'( *)\w', contents)
    if not match:
        raise RuntimeError('empty binding given')

    spaces = len(match[1])

    if spaces <= 0:
        return contents

    modified = []
    for line in contents.split('\n'):
        modified.append(line[spaces:])

    return '\n'.join(modified)
