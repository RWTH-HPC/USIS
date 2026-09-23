"""
This module contains the mechanism to generate the Language
Independent Binding (LIS).
"""


import logging
from collections import defaultdict
from typing import Mapping, MutableMapping, Any, List, Optional, Sequence


# Define desc_map here so that it is global to this module
DEFAULT_DESCRIPTIONS: MutableMapping[str, str] = defaultdict(lambda: '')


def init(_: Mapping):
    """
    Set default descriptions for specific types.
    """

    # Default descriptions, if no description is provided.  Set keys in our
    # entire LIS kind map so that we guarantee to have all the dictionary
    # keys, and then set all the default descriptions to the empty string.

    # Now update a few of the default descriptions to the desired values.
    DEFAULT_DESCRIPTIONS.update({
        'ERROR_CODE': 'error code',
        'ERROR_CLASS': 'error class',

        'COMMUNICATOR': 'communicator',
        'ERRHANDLER': '\\MPI/ error handler',
        'INFO': 'info argument',
        'FILE': 'file',
        'REQUEST': 'communication request',
        'STATUS': 'status object',
        'WINDOW': 'window object',
        'ASSERT': 'program assertion',
        'SESSION': 'session',
    })


def emit_binding(parseset: Mapping,
                 _: str,
                 kind_map: Mapping
                 ) -> Optional[str]:
    '''
    Emit the language independent specification (LIS) binding.
    '''

    # early exit if LIS is not defined for API
    if not parseset['attributes']['lis_expressible']:
        return None

    logging.info('expressing %s', parseset['name'])

    listable_parameters = list(filter(
        lambda p: 'lis_parameter' not in p['suppress'],
        parseset['parameters']))

    definable_parameters = list(filter(lambda p: p['kind'] != 'VARARGS',
                                       listable_parameters))

    latex_macro = 'funcdef' if listable_parameters else 'funcdefna'

    begin_macro = (f"\\begin{{{latex_macro}}}"
                   f"{{{_emit_api_prototype(parseset, listable_parameters)}}}")

    definitions = (_emit_parameter_definition(parameter,
                                              kind_map[parameter['kind']])
                   for parameter in definable_parameters)
    funcargs = '\n'.join(definitions)

    end_macro = f"\\end{{{latex_macro}}}"
    # TODO do better
    if funcargs:
        end_macro = '\n' + end_macro

    return f"{begin_macro}\n{funcargs}{end_macro}"


def _emit_api_prototype(interface: Mapping[str, Any],
                        parameters: List[Mapping[str, Any]]
                        ) -> str:
    """
    Emit the API prototype statement.
    """

    return (f"{interface['name'].upper()}"
             "}{"
            f"{_emit_parameter_list(parameters)}")


def _emit_parameter_list(parameters: Sequence[Mapping[str, Any]]) -> str:
    """
    Emit the prototype parameter list of **valid** parameters.
    """

    # filter parameter names or varags dots
    parameter_names = ((parameter['name'] if parameter['kind'] != 'VARARGS'
                        else '\\ldots')
                       for parameter in parameters)

    # add mbox to prevent line breaking inside parameter name
    parameter_names = (f"\\mbox{{{parameter_name}}}"
                       for parameter_name in parameter_names)

    return f"({', '.join(parameter_names)})"


def _emit_parameter_definition(parameter: Mapping[str, Any],
                               lis_kind: str
                               ) -> str:
    """
    Emit the correct funcarg latex for the given parameter.
    """

    direction = parameter['lis_direction'].upper()

    name = parameter['name']

    desc = _emit_parameter_description(parameter, lis_kind)

    return f"\\funcarg{{\\{direction}}}{{{name}}}{{{desc}}}"


def _emit_parameter_description(parameter: Mapping[str, Any],
                                lis_kind: str
                                ) -> str:
    """
    Emit the description of the LIS parameter of the given parameter.
    """

    desc = (parameter['desc'] if parameter['desc']
            else DEFAULT_DESCRIPTIONS[parameter['kind']])

    # TODO improve this similar to _emit_parameter_lis_type
    suppress = (('lis_paren' in parameter['suppress'] or
                 'lis_kind' in parameter['suppress'] or
                 lis_kind is None) and not parameter['root_only'])

    if lis_kind is None:
        # MR 2020/01/1
        # this is a reminder, we shouldn't really have NONE LIS KINDs
        # the forum needs to decide what should be written for these
        logging.info('parameter %s kind is None for LIS', parameter['name'])

    space = ' ' if desc and not suppress else ''

    parenthetical = ('' if suppress
                     else _emit_parameter_lis_type(parameter, lis_kind))

    return f"{desc}{space}{parenthetical}"


def _emit_parameter_lis_type(parameter: Mapping[str, Any],
                             kind: str
                             ) -> str:
    """
    Emit the LIS type of the given parameter.
    """

    # TODO clean this up
    if (('lis_paren' in parameter['suppress'] or
         'lis_kind' in parameter['suppress']) and
            parameter['root_only']):
        return '(significant only at root)'

    # root significance
    significant = ('' if not parameter['root_only']
                   else ', significant only at root')

    # large count variant only
    # TODO as above, suppression should not exclude large_only
    count = ('' if not parameter['large_only']
             else ', \\textbf{only present for large count variants}')

    if parameter['kind'] in ('STRING', 'STRING_2DARRAY'):
        # these kinds are not normal arrays, emit them directly
        return f"({kind}{significant})"

    # array of
    array = 'array of ' if parameter['length'] is not None else ''

    # plural of kind
    # plural = (('es' if parameter['kind'] == 'STATUS' else 's')
    #          if array else '')
    plural = (('' if parameter['kind'] == 'STATUS' else 's')
              if array else '')

    return f"({array}{kind}{plural}{significant}{count})"
