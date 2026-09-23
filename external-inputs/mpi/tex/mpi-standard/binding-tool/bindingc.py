"""
Defines the C binding generator for MPI Binding Generator Tool.
"""


import logging
from typing import Any, Mapping, Optional


def emit_binding(parseset: Mapping[str, Any],
                 postfix: str,
                 kind_map: Mapping[str, str]) -> Optional[str]:
    """
    Function to generate C bindings for given parseset and kind_map.
    """

    if parseset is None:
        raise RuntimeError("API given is None")

    # early exit if no C binding needed
    if not parseset['attributes']['c_expressible']:
        return None

    interface_name = f"{parseset['name']}{postfix}"
    
    if parseset['attributes']['capitalized']:
        interface_name = interface_name.upper()

    binding = (
        f"{_emit_latex_macro(parseset, kind_map[parseset['return_kind']])}"
        f"{interface_name}"
         "}{"
        f"{_emit_parameter_list(parseset, postfix, kind_map)}"
        "}")

    if parseset['attributes']['index_upper']:
        binding += "{" + kind_map[parseset['return_kind']] + "}"
        binding += "{" + parseset['name'].upper() + "}"

    # function index attribute
    index_macro = f"\\MPIbindindex{{{parseset['name']}{postfix}}}\n" if postfix and not parseset['attributes']['callback'] else ''

    return f"{index_macro}{binding}"


def _emit_latex_macro(parseset: Mapping[str, Any],
                      return_type: str) -> str:
    """
    Emit the required latex macro.
    """

    if parseset['attributes']['callback']:
        # API is callback
        if parseset['attributes']['render_main']:
            # main definition
            if parseset['return_kind'] == 'NOTHING':
                return '\\mpitypedefbindvoidmain{'
            return '\\mpitypedefbindmain{'
        else:
            # render(), prior main defition
            if parseset['return_kind'] == 'NOTHING':
                return '\\mpitypedefbindvoid{'
            return '\\mpitypedefbind{'


    if parseset['attributes']['index_upper']:
        # API is a mpiemptybindidx
        return r'\mpiemptybindidx{'

    # API is normal function
    if parseset['return_kind'] == 'ERROR_CODE':
        return '\\mpibindmain{'

    return f'\\mpibindnotintmain{{{return_type}}}{{'


def _parameter_suppression(parameter: Mapping[str, Any], postfix: str) -> bool:
    """
    """

    if 'c_parameter' in parameter['suppress']:
        return True

    if not parameter['large_only']:
        return False

    if parameter['large_only'] and not postfix:
        return True

    return False


def _emit_parameter_list(parseset: Mapping[str, Any],
                         postfix: str,
                         kind_map: Mapping[str, str]) -> str:
    """
    Constructs the entire parameter list.
    """

    # find expressible parameters
    # parameters = list(filter(lambda p: 'c_parameter' not in p['suppress'],
    #                          parseset['parameters']))

    # TODO replace
    parameters = []
    for parameter in parseset['parameters']:
        if not _parameter_suppression(parameter, postfix):
            parameters.append(parameter)

    # no C expressible parameters -> void parameter list
    if not parameters:
        return '(void)'

    # with valid parameters
    parameter_list = [_emit_c_param(param, postfix, kind_map)
                      for param in parameters]

    goodbreak = r"\gb{}"
    return f"({goodbreak}{', '.join(parameter_list)})"


def _emit_c_param(parameter: Mapping[str, Any],
                  postfix: str,
                  kind_map: Mapping[str, str]
                  ) -> str:
    """
    Emit a single paramter.
    """

    assert parameter['name']
    assert 'c_parameter' not in parameter['suppress']
    assert parameter['kind'] in kind_map

    # variable arguments is special MPI_Pcontrol
    if parameter['kind'] == 'VARARGS':
        return kind_map[parameter['kind']]

    return (f"{_emit_const_attribute(parameter)}"
            f"{_emit_type_attribute(parameter, postfix, kind_map)}~"
            f"{_emit_pointer_attribute(parameter)}"
            f"{parameter['name']}"
            f"{_emit_array_attribute(parameter)}")


def _emit_const_attribute(parameter: Mapping[str, Any]) -> str:
    """
    Emits the const attribute of the parameter expression.
    """

    return 'const~' if parameter['constant'] else ''


def _emit_type_attribute(parameter: Mapping[str, Any],
                         postfix: str,
                         kind_map: Mapping[str, str]) -> str:
    """
    Emits the type attribute of the parameter expression.
    """

    # If this is a FUNCTION, we have to get the type from
    # parameter['func_type'] (because every function type is
    # different)
    if parameter['kind'] in ('FUNCTION', 'FUNCTION_SMALL'):
        return f"{parameter['func_type']}"

    if parameter['kind'] == 'POLYFUNCTION':
        return f"{parameter['func_type']}{postfix}"

    return kind_map[parameter['kind']]


def _emit_pointer_attribute(parameter: Mapping[str, Any]) -> str:
    """
    Emits the pointer attribute of the parameter expression.
    """

    # Add a star if:
    # - This is a BUFFER or C_BUFFER, or
    # - This is a STRING, or
    # - This is a STATUS, or
    # - This is a TOOL_MPI_OBJ, or
    # - This is a F90_STATUS or F08_STATUS, or
    # - This is an EXTRA_STATE, or
    # - This is an IN FUNCTION, or
    # - This is an INOUT or OUT and there is no "length" inidicated, or
    # - "pointer" is True

    if parameter['pointer'] is not None and not parameter['pointer'] and parameter['kind'] == 'ARGUMENT_LIST':
        return '*'

    if parameter['pointer'] is not None and not parameter['pointer']:
        return ''

    if parameter['kind'] == 'STRING_2DARRAY':
        return '**'

    if parameter['kind'] == 'ARGUMENT_LIST':
        return '***'

    # needed for MPI_UNPACK_EXTERNAL[_size]
    if (parameter['kind'] == 'STRING' and
            parameter['length'] == '*' and
            not parameter['pointer']):
        return ''

    if parameter['kind'] in ('BUFFER', 'C_BUFFER', 'C_BUFFER2', 'C_BUFFER3',
                             'C_BUFFER4', 'STRING', 'EXTRA_STATE',
                             'EXTRA_STATE2', 'ATTRIBUTE_VAL', 'STATUS',
                             'ATTRIBUTE_VAL_10', 'STRING_ARRAY',
                             'FUNCTION', 'FUNCTION_SMALL', 'POLYFUNCTION',
                             'TOOL_MPI_OBJ', 'F08_STATUS', 'F90_STATUS'):
        return '*'

    if (parameter['param_direction'] == 'inout' or
            parameter['param_direction'] == 'out' or
            parameter['pointer']) and parameter['length'] is None:
        return '*'

    return ''


def _emit_array_attribute(parameter: Mapping[str, Any]) -> str:
    """
    Emits the array attribute of the parameter expression.
    """

    # Add "[]" if:
    # - This is not a STRING, and
    # - length > 0, and
    # - "pointer" was not specified
    # OR
    # - The type is STRING_ARRAY or STRING_2DARRAY

    if parameter['kind'] == 'C_BUFFER4':
        # length set on MPI_User_function
        return ''

    if (parameter['kind'] != 'STRING' and
            parameter['length'] is not None and
            not isinstance(parameter['length'], list) and
            not parameter['pointer']):
        return '[]'

    # required by MPI_UNPACK_EXTERNAL, it uses array notation for a string.
    if (parameter['kind'] == 'STRING' and
            parameter['length'] == '*' and
            not parameter['pointer']):
        return '[]'

    if (parameter['kind'] == 'STRING_ARRAY' or
            parameter['kind'] == 'STRING_2DARRAY'):
        return '[]'

    # As of MPI-4.0, we have array parameters with -- at most -- 2
    # dimensions.  Always print the first dimension as [] (above).
    # If we have a second dimension, print it (e.g.,
    # MPI_GROUP_RANGE_INCL & EXCL).
    if isinstance(parameter['length'], list):
        return '[][{len}]'.format(len=parameter['length'][1])

    return ''
