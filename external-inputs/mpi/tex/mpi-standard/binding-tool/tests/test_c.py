"""
Tests for the C Binding generation.
"""


# pylint: disable=import-error
# pylint: disable=protected-access
# pylint: disable=redefined-outer-name


from typing import Mapping, Any, Iterable


import pytest


import bindingc
from bindingtypes import SMALL_C_KIND_MAP


def test_expressibility(database):
    """
    Tests if an expressible API is expressed in C.
    """

    api = database['mpi_init']

    expression = bindingc.emit_binding(api, '', SMALL_C_KIND_MAP)

    assert expression is not None, (f"{api['name']} is not expressed, "
                                    f"but it should be")


def test_inexpressible(database):
    """
    Tests if an API marked as inexpressible is not expressed.
    """

    api = database['mpi_sizeof']

    expression = bindingc.emit_binding(api, '', SMALL_C_KIND_MAP)

    assert expression is None, (f"{api['name']} is expressed, "
                                f"but shouldn't be")


@pytest.fixture(scope="module")
def constant_parameters(database) -> Iterable[Mapping[str, Any]]:
    """
    Loads all constant parameters from the database.
    """

    parameters = []

    for item in database.values():
        for parameter in item['parameters']:
            if parameter['constant']:
                parameters.append(parameter)

    return parameters


@pytest.fixture(scope="module")
def non_constant_parameters(database) -> Iterable[Mapping[str, Any]]:
    """
    Filters all non-constant parameters from database.
    """

    parameters = []

    for api in database.values():
        for parameter in api['parameters']:
            if not parameter['constant']:
                parameters.append(parameter)

    return parameters


def test_callback_latex(database):
    """
    Tests whether a callback API is correctly expressed.
    """

    api = database['mpi_file_errhandler_function']

    latex = bindingc._emit_latex_macro(api,
                                       SMALL_C_KIND_MAP[api['return_kind']])

    assert 'mpitypedefbind' in latex


def test_int_latex_macro(database):
    """
    Tests whether an API with an ERROR_CODE return kind uses the correct
    latex macro.
    """

    api = database['mpi_get_version']

    latex = bindingc._emit_latex_macro(api,
                                       SMALL_C_KIND_MAP[api['return_kind']])

    assert latex == '\\mpibindmain{'


def test_non_error_code_latex_macro(database):
    """
    Tests whether a function which doesn't return an ERROR_CODE is
    expressed correctly.
    """

    api = database['mpi_wtime']

    latex = bindingc._emit_latex_macro(api,
                                       SMALL_C_KIND_MAP[api['return_kind']])

    assert 'mpibindnotint' in latex


def test_void_if_no_parameters(database):
    """
    Tests if the parameter list is correctly voided when no parameters are
    present.

    This applies to MPI_Wtick, MPI_Wtime, MPI_Finalize, MPI_T_finalize
    """

    parameter_list = bindingc._emit_parameter_list(database['mpi_finalize'],
                                                   '',
                                                   SMALL_C_KIND_MAP)

    assert parameter_list == "(void)"


def test_single_parameter_list(database):
    """
    Tests whether with a single parameter the parameter list is correctly
    expressed.
    """

    api = database['mpi_cancel']

    expression = bindingc._emit_parameter_list(api, '', SMALL_C_KIND_MAP)

    assert expression == r"(\gb{}MPI_Request~*request)"


def test_multi_parameter_list(database):
    """
    Tests whether with multiple parameters the parameter list is correctly
    expressed.
    """

    api = database['mpi_wait']

    expression = bindingc._emit_parameter_list(api, '', SMALL_C_KIND_MAP)

    assert expression == r"(\gb{}MPI_Request~*request, MPI_Status~*status)"


def test_varargs_parameter(database):
    """
    Tests whether the VARARGS is correctly expressed.

    MPI_Pcontrol is an example.
    """

    parameter = database['mpi_pcontrol']['parameters'][1]

    expression = bindingc._emit_c_param(parameter, '', SMALL_C_KIND_MAP)

    assert expression == '\\ldots'


def test_const_prefix(constant_parameters: Iterable[Mapping[str, Any]]):
    """
    Tests if the 'const' is prefixed on a constant parameter.

    This applies to MPI_Send and many others.
    """

    for parameter in constant_parameters:
        assert bindingc._emit_const_attribute(parameter) == 'const~'


def test_non_const_no_prefix(non_constant_parameters):
    """
    Test if the 'const' is not added when the parameter is not constant.
    """

    for parameter in non_constant_parameters:
        assert bindingc._emit_const_attribute(parameter) == ''


def test_function_pointer(database):
    """
    Tests whether a function callback pointer is correctly expressed.
    """

    api = database['mpi_op_create']

    parameter = bindingc._emit_c_param(api['parameters'][0],
                                       '',
                                       SMALL_C_KIND_MAP)

    assert parameter == 'MPI_User_function~*user_fn'


def test_normal_non_function_type_parameter(database):
    """
    Tests if a parameter type other than a function pointer is expressed
    correctly.
    """

    api = database['mpi_testany']

    parameter = bindingc._emit_c_param(api['parameters'][0],
                                       '',
                                       SMALL_C_KIND_MAP)

    assert parameter[:parameter.find('~')] == 'int'


def test_normal_array_attribute(database):
    """
    Tests whether normal array outputs work.
    """

    api = database['mpi_waitany']
    parameter = api['parameters'][1]

    attribute = bindingc._emit_array_attribute(parameter)

    assert attribute == '[]'


def test_no_array_attribute(database):
    """
    Tests that the array attribute is empty for length==None.
    """

    api = database['mpi_wait']
    parameter = api['parameters'][0]

    expression = bindingc._emit_array_attribute(parameter)

    assert expression == ''


def test_array_notation_string(database):
    """
    Tests whether the array notation of a string is correctly expressed.

    The only API which this is for is MPI_UNPACK_EXTERNAL.
    """

    api = database['mpi_unpack_external']
    parameter = api['parameters'][0]

    expression = bindingc._emit_array_attribute(parameter)

    assert expression == '[]'


def test_string_array_attribute(database):
    """
    Tests whether the kind STRING_ARRAY is correctly expressed.

    Only MPI_Comm_spawn and MPI_Comm_spawn_multiple.
    """

    api = database['mpi_comm_spawn']
    parameter = api['parameters'][1]

    expression = bindingc._emit_array_attribute(parameter)

    assert expression == '[]'


def test_string_2darray_attribute(database):
    """
    Tests whether the kind STRING_2DARRAY is correctly expressed.

    Only MPI_Comm_spawn_multiple.
    """

    api = database['mpi_comm_spawn_multiple']
    parameter = api['parameters'][2]

    expression = bindingc._emit_array_attribute(parameter)

    assert expression == '[]'


def test_argument_list_init(database):
    """
    Tests whether the ARGUMENT_LIST kind receives a [] or not in the MPI_Init procedure.
    """

    api = database['mpi_init']
    parameter = api['parameters'][1]

    expression = bindingc._emit_array_attribute(parameter)
    assert expression == ''

    expression = bindingc._emit_pointer_attribute(parameter)
    assert expression == '***'


def test_argument_list_info(database):
    """
    Tests whether the ARGUMENT_LIST in the MPI_Info_create_env procedure receives a [].
    """

    api = database['mpi_info_create_env']
    parameter = api['parameters'][1]

    expression = bindingc._emit_array_attribute(parameter)
    assert expression == "[]"

    expression = bindingc._emit_pointer_attribute(parameter)
    assert expression == "*"


def test_length_multidimensional(database):
    """
    Tests whether a multidimensional length parameter is expressed
    as a multidimensional array in C.

    The only two APIs are MPI_Group_range_incl and MPI_Group_range_excl.
    """

    api = database['mpi_group_range_incl']

    attribute = bindingc._emit_array_attribute(api['parameters'][2])

    assert attribute == '[][3]'


def test_kind_buffer_receives_pointer(database):
    """
    Tests whether BUFFER receives a pointer for the parameter.
    """

    api = database['mpi_send']
    parameter = api['parameters'][0]

    attribute = bindingc._emit_pointer_attribute(parameter)

    assert attribute == '*'


def test_kind_2darray_receives_double_pointer(database):
    """
    Tests whether STRING_2DARRAY receives a double pointer for the parameter.
    """

    api = database['mpi_comm_spawn_multiple']
    parameter = api['parameters'][2]

    attribute = bindingc._emit_pointer_attribute(parameter)

    assert attribute == '**'


def test_pointer_set(database):
    """
    Tests whether a parameter with pointer=True will receive a pointer.
    """

    api = database['mpi_cancel']
    parameter = api['parameters'][0]

    attribute = bindingc._emit_pointer_attribute(parameter)

    assert attribute == '*'


def test_pointer_set_unless_array_wanted(database):
    """
    Tests whether a pointer is suppressed when pointer=False and array is not
    None.
    """

    api = database['mpi_unpack_external']
    parameter = api['parameters'][0]

    attribute = bindingc._emit_pointer_attribute(parameter)

    assert attribute == ''


def test_out_parameter_pointer(database):
    """
    Tests whether an OUT parameter receives a pointer.
    """

    api = database['mpi_test_cancelled']
    parameter = api['parameters'][1]

    attribute = bindingc._emit_pointer_attribute(parameter)

    assert attribute == '*'


def test_inout_parameter_pointer(database):
    """
    Tests whether an INOUT parameter receives a pointer.
    """

    api = database['mpi_start']
    parameter = api['parameters'][0]

    attribute = bindingc._emit_pointer_attribute(parameter)

    assert attribute == '*'


def test_array_notation_on_cbuffer4(database):
    """
    Tests whether array notation is not put on a C_BUFFER4 parameter.

    regression
    """

    api = database['mpi_user_function']
    parameter = api['parameters'][0]

    expression = bindingc._emit_array_attribute(parameter)

    assert expression == ''


def test_non_postfix_function(database):
    """
    Tests whether a FUNCTION correctly does not express a postfix.
    """

    api = database['mpi_comm_create_errhandler']
    parameter = api['parameters'][0]
    postfix = '_x'

    expression = bindingc._emit_c_param(parameter, postfix, SMALL_C_KIND_MAP)

    assert expression == 'MPI_Comm_errhandler_function~*comm_errhandler_fn'


def test_output_idx_macro(database):
    """
    Tests whether the 'mpiemptybindidx' is output for interfaces with a
    indexed_name value other than None.
    """

    api = database['mpi_comm_f2c']

    expression = bindingc.emit_binding(api, '', SMALL_C_KIND_MAP)

    assert 'mpiemptybindidx' in expression


def test_capitalized_property(database):
    """
    Tests whether the capitalization property correctly uses only
    uses uppercase letters.
    """

    api = database['mpi_conversion_fn_null']

    expression = bindingc.emit_binding(api, '', SMALL_C_KIND_MAP)

    assert r"MPI_CONVERSION_FN_NULL" in expression
