"""
Defines the F90 binding generator function.
"""


import collections
from typing import MutableMapping, Mapping, Any, List, Sequence, Optional


def emit_binding(parseset: Mapping[str, Any],
                 postfix: str,
                 kind_map: Mapping[str, str]) -> Optional[str]:
    """
    Generates the F90 MPI bindings from given parseset and kind_map.
    """

    # early exit if no F90 binding needed
    if not parseset['attributes']['f90_expressible']:
        return None

    # find all valid parameters
    valid_params = list(filter(
        lambda p: ('f90_parameter' not in p['suppress'] and
                   p['kind'] != 'VARARGS' and
                   p['large_only'] is False),
        parseset['parameters']))

    # set fargs if needed
    fargs = ' \\fargs ' if valid_params else ''

    # index overload for F90 APIs
    overload = '' if not parseset['attributes']['f90_index_overload'] else (
        r"\mpifoverloadOnlyInAnnex{"
        f"{parseset['attributes']['f90_index_overload']}}}")

    # glue together F90 MPI binding
    binding = (
        # latex macro
        f"{_emit_latex_macro(parseset, kind_map)}"
        # return type
        # API name
        f"{_emit_routine_name(parseset, postfix)}"
        # name is separate
        "}{"
        # parameter list
        f"{_emit_parameter_list(valid_params)}"
        # \fargs if required
        f"{fargs}"
        # parameter descriptors if required
        f"{_emit_parameter_descriptors(parseset, valid_params, kind_map)}"
        # index overload if required
        f"{overload}"
        "}")

    return binding


def _emit_latex_macro(parseset: Mapping[str, Any], kind_map: Mapping[str, str]) -> str:
    """
    Emit the required f90 latex macro.
    """

    if parseset['attributes']['not_with_mpif']:
        return r'\mpifbindspecial{'

    if parseset['attributes']['callback']:
        if parseset['attributes']['render_main']:
            return r'\mpifsubbindmain{'
        else:
            return r'\mpifsubbind{'

    return (r'\mpifbindmain{' if parseset['return_kind'] in ('NOTHING', 'ERROR_CODE')
            else f"\\mpifbindretmain{{{kind_map[parseset['return_kind']]}}}{{" )


def _emit_return_type(parseset: Mapping[str, Any],
                      kind_map: Mapping[str, str]) -> str:
    """
    Emit the required return type for the binding.
    """

    return ('' if parseset['return_kind'] in ('NOTHING', 'ERROR_CODE')
            else f"{kind_map[parseset['return_kind']]} ")


def _emit_routine_name(parseset: Mapping[str, Any],
                       postfix: str
                       ) -> str:
    """
    Emit the correct name for the API.
    """

    name = parseset['name_f90'] if parseset['name_f90'] else parseset['name']
    return f"{name}{postfix}".upper()


def _emit_parameter_list(parameters: Sequence[Mapping[str, Any]]) -> str:
    """
    Construct the parameter list.
    """

    parameter_names = (param['name'].upper() for param in parameters)
    return f"({', '.join(parameter_names)})"


def _emit_parameter_descriptors(parseset: Mapping[str, Any],
                                valid: Sequence[Mapping[str, Any]],
                                kind_map: Mapping[str, str],
                                ) -> str:
    """
    Emits the parameter descriptors.
    """

    groupings = _find_parameter_ordering(valid, kind_map)

    separator = ' :: ' if parseset['attributes']['f90_use_colons'] else ' '

    descriptors = (_emit_parameter_descriptor(kind, parameters, separator)
                   for kind, parameters in groupings.items())

    #    return r' \\ '.join(descriptors)
    rval = ''
    narg = ''
    for arg in descriptors:
        if narg != '':
            if rval != '':
                rval = rval + r'\fnarg{}'
            rval = rval + narg
        narg = arg
    rval = rval + r'\fnfinalarg{}' + narg
    return rval


def _emit_parameter_descriptor(kind: str,
                               parameter_names: List[str],
                               separator: str):
    """
    Emit a single type + parameters combination.
    """

    descriptor = ", ".join(parameter_names)

    return f"{kind}{separator}{descriptor}"


def _find_parameter_ordering(valid_parameters: Sequence[Mapping[str, Any]],
                             kind_map: Mapping[str, str]
                             ) -> MutableMapping[str, List[str]]:
    """
    Determine the order of the fortran parameter descriptors.
    The ordering chosen is by order of parameter list, and all
    paramters of same type are combined into the earliest type.
    """

    groupings: MutableMapping[str, List[str]] = collections.OrderedDict()

    for parameter in valid_parameters:
        left = kind_map[parameter['kind']]

        # Save the "left" and "right"
        if left not in groupings:
            groupings[left] = list()

        parameter_expression = f'\\mbox{{{_construct_parameter(parameter)}}}'

        groupings[left].append(parameter_expression)

    return groupings


def _construct_parameter(parameter: Mapping[str, Any]) -> str:
    """
    Construct the array parenthetical to the right of the parameter name
    for the parameter descriptors.
    """

    right = [parameter['name'].upper()]

    if ('f90_parenthesis' in parameter['suppress'] or
            'f90_buf_paren' in parameter['suppress']):
        return right[0]

    dimensions = list()

    if parameter['kind'] in ('BUFFER', 'C_BUFFER2', 'C_BUFFER3',
                             'STRING_ARRAY'):
        # can these be set to length?
        # length is not None for many
        dimensions.append('*')

    elif parameter['kind'] == 'F90_STATUS':
        dimensions.append('MPI_STATUS_SIZE')

    elif parameter['kind'] == 'STATUS':
        dimensions.append('MPI_STATUS_SIZE')

        if parameter['length'] is not None:
            dimensions.append(parameter['length'])

    # There are cases where we need to emit a length
    elif parameter['kind'] == 'C_BUFFER4':
        dimensions.append(parameter['length'].upper())

    elif parameter['kind'] == 'STRING_2DARRAY':
        dimensions.append(parameter['length'].upper())
        dimensions.append('*')

    # what is this?
    # why do we need to exclude these?
    elif (parameter['kind'] != 'STRING' and
          parameter['length'] is not None and
          parameter['kind'] != 'C_BUFFER4'):
        if isinstance(parameter['length'], list):
            # As of MPI-4.0, MPI has parameters with -- at most --
            # 2 dimensions.  No need for a loop.  Indeed, we only
            # want to emit one dimension here -- the other will be
            # '*', and will be handled below.
            # TODO use array_type, hidden or some other

            dimensions.append(parameter['length'][1])

            # use in mpi_group_incl/excl

        # We always need a '*' at the end
        dimensions.append('*')

    if dimensions:
        right.append('(')
        right.append(', '.join(dimensions))
        right.append(')')

    return ''.join(right)
