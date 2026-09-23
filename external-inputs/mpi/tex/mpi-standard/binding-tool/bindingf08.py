"""
Defines the F08 binding generator.
"""


import collections
from typing import OrderedDict, Any, Mapping, Optional, Sequence, Iterable


def _suppress_parameter(parameter: Mapping[str, Any], postfix: str) -> bool:
    """
    Determine whether this parameter should be suppressed.
    """

    # ordering of these ifs matters, these are any of the conditions that
    # suppress the parameter
    if 'f08_parameter' in parameter['suppress']:
        return True

    if parameter['large_only'] and not postfix:
        return True

    if parameter['kind'] == 'VARARGS':
        return True

    if not parameter['large_only']:
        return False

    return False


def emit_binding(parseset: Mapping[str, Any],
                 postfix: str,
                 kind_map: Mapping[str, str]
                 ) -> Optional[str]:
    """
    Generates the F08 MPI binding.
    """

    # early exit if F08 binding not needed
    if not parseset['attributes']['f08_expressible']:
        if parseset['attributes']['proxy_render']:
            return (r'\mpifnewnonebind{For this routine, an interface within '
                    r'the \code{mpi\_f08} module was never defined.}')
        return None

    valid_parameters = []
    for parameter in parseset['parameters']:
        if not _suppress_parameter(parameter, postfix):
            valid_parameters.append(parameter)

    # If we have any C_BUFFER params, we need to emit an extra line
    require = ('C_BUFFER', 'C_BUFFER2', 'C_BUFFER3', 'C_BUFFER4')
    intrinsic = (r'USE, INTRINSIC\ ::\ ISO_C_BINDING, ONLY : C_PTR \\ '
                 if any((parameter['kind'] in require
                         for parameter in parseset['parameters']))
                 else '')

    descriptors = _emit_parameter_descriptors(
        valid_parameters,
        postfix,
        kind_map,
        (parseset['attributes']['callback'] or
         parseset['attributes']['predefined_function']))

    latex = _emit_latex_macro(parseset, kind_map)

    name = (f"{parseset['name']}{postfix}"
            if (parseset['attributes']['callback'] or
                not parseset['attributes']['f08_abstract_interface'])
            else parseset['name'])

    if parseset['attributes']['capitalized']:
        name = name.upper()

    sep = '}{'
    parameter_list = _emit_parameter_list(valid_parameters)
    comment_c = f' !({postfix})' if postfix else ''
    fargs = '' if parameter_list == '()' else ' \\fargs '

    return (f"{latex}{name}{sep}{parameter_list}{comment_c}{fargs}{intrinsic}"
            f"{descriptors}}}")


def _emit_latex_macro(parseset: Mapping[str, Any], kind_map: Mapping[str, str]) -> str:
    """
    Emits the required latex macro.
    """

    return ('\\mpifnewsubbind{' if parseset['attributes']['callback']
            else '\\mpifnewbindmainref{' if not parseset['attributes']['c_expressible']
            else '\\mpifnewbindmain{' if parseset['return_kind'] in ('NOTHING', 'ERROR_CODE')
            else f"\\mpifnewbindretmain{{{kind_map[parseset['return_kind']]}}}{{")


def _emit_return_kind(parseset: Mapping[str, Any],
                      kind_map: Mapping[str, str]
                      ) -> str:
    """
    Emits the return type if required.
    """

    return ("" if parseset['return_kind'] in ('NOTHING', 'ERROR_CODE')
            else f"{kind_map[parseset['return_kind']]} ")


def _emit_parameter_list(parameters: Sequence[Mapping[str, Any]]) -> str:
    """
    Construct the parameter list string.
    """

    parameter_names = (parameter['name'] for parameter in parameters)

    return f"({', '.join(parameter_names)})"


def _emit_parameter_descriptors(valid: Sequence[Mapping[str, Any]],
                                postfix: str,
                                kind_map: Mapping[str, str],
                                ignore_intent: bool
                                ) -> str:
    """
    Emit parameter descriptors for F08 binding.
    """

    groupings = find_parameter_ordering(valid, postfix,
                                        kind_map, ignore_intent)

    descriptors = (_emit_parameter_descriptor(kind_f08, parameter_names)
                   for kind_f08, parameter_names in groupings.items())

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
                               parameter_names: Iterable[str]
                               ) -> str:
    """
    """

    descriptor = ", ".join(parameter_names)

    return f"{kind}\\ ::\\ {descriptor}"


def find_parameter_ordering(valid: Sequence[Mapping[str, Any]],
                            postfix: str,
                            kind_map: Mapping[str, str],
                            ignore_intent: bool) -> OrderedDict[str, str]:
    """
    Determine the ordering of the parameter descriptors.
    """

    groupings: OrderedDict = collections.OrderedDict()

    for parameter in valid:
        left = (f"{_emit_parameter_type(parameter, postfix, kind_map)}"
                f"{_emit_type_length(parameter)}"
                f"{_emit_optional_attribute(parameter)}"
                f"{_emit_intent_attribute(parameter, ignore_intent)}"
                f"{_emit_asynchronous_attribute(parameter)}")

        right = f"\\mbox{{{parameter['name']}{_emit_name_length(parameter)}}}"

        # Save the "left" and "right"
        if left not in groupings:
            groupings[left] = list()

        groupings[left].append(right)

    return groupings


def _emit_intent_attribute(parameter: Mapping[str, Any],
                           ignore_intent: bool
                           ) -> str:
    """
    Emits the intent attribute for the parameter.
    """

    if parameter['kind'] == 'ERROR_CODE_SHOW_INTENT':
        # conflict between ignore_intent and this
        return ', INTENT(' + parameter['param_direction'].upper() + ')'

    if 'f08_intent' in parameter['suppress'] or ignore_intent:
        return ""

    param = parameter
    kind = parameter['kind']

    if (kind == 'STATUS' and
            param['param_direction'] == 'out'):
        # Do not issue an intent for OUT status because the
        # user may pass MPI_STATUS[ES]_IGNORE, and therefore
        # it's also an IN parameter, too.
        return ""

    if (kind == 'BUFFER' and
            param['param_direction'] == 'out'):
        # Similar to above, do not issue an intent for OUT
        # buffer because the user may pass MPI_BOTTOM, and
        # therefore it's also an IN parameter, too.
        return ""

    if (kind == 'BUFFER' and
            param['param_direction'] == 'inout'):
        # Similar to above, do not issue an intent for INOUT
        # see MPI_Sendrecv_replace
        return ""

    if (kind == 'FUNCTION' and
            param['param_direction'] == 'in'):
        # ...Jeff does not remember why we do not specify
        # INTENT for FUNCTION (i.e., PROCEDURE) types, but we
        # don't...
        return ""

    if (kind == 'POLYFUNCTION' and
            param['param_direction'] == 'in'):
        # ...Dan (for issue 396) duplicated the suppression of 
        # INTENT for POLYFUNCTION (i.e., PROCEDURE) types
        return ""

    if 'f08_intent' not in param['suppress']:
        # Otherwise, unless the binding specifically asked us
        # to suppress the F08 intent (e.g.,
        # MPI_BUFFER_ATTACH), emit it.
        return ', INTENT(' + param['param_direction'].upper() + ')'

    return ""


def _emit_optional_attribute(parameter: Mapping[str, Any]) -> str:
    """
    Emit the optional attribute if required.
    """

    return ', OPTIONAL' if parameter['optional'] else ""


def _emit_asynchronous_attribute(parameter: Mapping[str, Any]) -> str:
    """
    Emit the asynchronous attribute if required.
    """

    return ', ASYNCHRONOUS' if parameter['asynchronous'] else ""


def _emit_type_length(parameter: Mapping[str, Any]) -> str:
    """
    Emit the type length if required by the kind.
    """

    # If this is a string and we have a length, also emit that
    if parameter['kind'] in ('STRING', 'STRING_ARRAY'):
        return (f"(LEN={parameter['length']})" if parameter['length']
                else '(LEN=*)')

    if parameter['kind'] == 'STRING_2DARRAY':
        return '(LEN=*)'

    return ""


def _emit_parameter_type(parameter: Mapping[str, Any],
                         postfix: str,
                         kind_map: Mapping[str, str]
                         ) -> str:
    """
    Emit the parameter F08 type.
    """

    if parameter['kind'] in ('FUNCTION', 'FUNCTION_SMALL'):
        return f"PROCEDURE({parameter['func_type']})"

    if parameter['kind'] == 'POLYFUNCTION':
        return f"PROCEDURE({parameter['func_type']}{postfix})"

    return kind_map[parameter['kind']]


def _emit_name_length(parameter: Mapping[str, Any]) -> str:
    """
    """

    param = parameter
    kind = parameter['kind']

    right = ''

    # There are cases where we need to emit a length
    if kind == 'F90_STATUS':
        right += '(MPI_STATUS_SIZE)'

    elif kind == 'STRING_ARRAY':
        right += '(*)'

    elif kind == 'STRING_2DARRAY':
        right += '({length}, *)'.format(length=param['length'])

    elif param['length'] is not None and param['array_type'] == 'hidden':
        right += '(*)'

    elif (kind != 'STRING' and
          param['length'] is not None and
          kind != 'C_BUFFER4'):
        right += '('

        if isinstance(param['length'], list):
            right += ', '.join(reversed(param['length']))

        elif param['length'] == '':
            right += '*'

        elif param['length'] is not None:
            right += param['length']

        right += ')'

    return right
