"""
Tests for the F90 Binding generation.
"""


# pylint: disable=import-error
# pylint: disable=protected-access
# pylint: disable=redefined-outer-name


import bindingf90
from bindingtypes import SMALL_F90_KIND_MAP


def test_expressibility(database):
    """
    Tests whether a F90 expressible API is expressed.
    """

    api = database['mpi_init']

    expression = bindingf90.emit_binding(api, '', SMALL_F90_KIND_MAP)

    assert expression is not None


def test_inexpressibility(database):
    """
    Tests whether a F90 inexpressible API is expressed.
    """

    api = database['mpi_t_init_thread']

    expression = bindingf90.emit_binding(api, '', SMALL_F90_KIND_MAP)

    assert expression is None


def test_for_normal_macro(database):
    """
    Tests whether a normal f90 macro is emitted for a non-callback function.
    """

    api = database['mpi_wait']
    expression = bindingf90._emit_latex_macro(api, SMALL_F90_KIND_MAP)
    assert 'mpifbind' in expression


def test_for_callback_macro(database):
    """
    Tests whether a callback f90 macro is emitted for a callback API.
    """

    api = database['mpi_type_copy_attr_function']
    expression = bindingf90._emit_latex_macro(api, SMALL_F90_KIND_MAP)
    assert 'mpifsubbind' in expression


def test_error_code_return(database):
    """
    Tests whether a normal ERROR_CODE return type is correctly emitted.
    """

    api = database['mpi_test']
    expression = bindingf90._emit_return_type(api, SMALL_F90_KIND_MAP)
    assert not expression


def test_non_error_code_return(database):
    """
    Tests whether the output is correct for non-error code returns.
    """

    api = database['mpi_wtime']
    expression = bindingf90._emit_return_type(api, SMALL_F90_KIND_MAP)
    assert expression == 'DOUBLE PRECISION '


def test_routine_name_always_capitalized(database):
    """
    Tests whether the routine name is capitalized.
    """

    api = database['mpi_wtime']
    expression = bindingf90._emit_routine_name(api, '')
    assert expression == api['name'].upper()


def test_identical_routine_name(database):
    """
    Tests whether the identical name is used as the name.
    """

    api = database['mpi_init']
    expression = bindingf90._emit_routine_name(api, '')
    assert expression == 'MPI_INIT'


def test_non_identical_routine_name(database):
    """
    Tests whether the special F90 name is used.
    """

    api = database['mpi_comm_copy_attr_function']
    expression = bindingf90._emit_routine_name(api, '')
    assert expression == api['name_f90'].upper()


def test_normal_parameter_list(database):
    """
    Tests if a normal parameter list is emitted correctly.

    An example is MPI_Wait.
    """

    parseset = database['mpi_wait']

    parameter_list = bindingf90._emit_parameter_list(parseset['parameters'])

    assert ''.join(parameter_list) == '(REQUEST, STATUS, IERROR)'


def test_suppressed_parameters(database):
    """
    Tests if suppressed parameters are treated correctly.

    An example if MPI_Init.
    """

    parseset = database['mpi_test']

    parameter_list = bindingf90._emit_parameter_list(parseset['parameters'])

    assert ''.join(parameter_list) == '(REQUEST, FLAG, STATUS, IERROR)'


def test_parameter_capitalization(database):
    """
    Tests whether parameters are capitalized.
    """

    api = database['mpi_wait']
    parameter = api['parameters'][0]
    expression = bindingf90._construct_parameter(parameter)

    assert expression == parameter['name'].upper()


def test_f90_parenthesis_suppression(database):
    """
    Tests whether the f90_buf_paren suppression works.
    """

    api = database['mpi_sizeof']
    parameter = api['parameters'][0]
    expression = bindingf90._construct_parameter(parameter)

    assert expression == parameter['name'].upper()


def test_kind_buffer_parenthetical(database):
    """
    Tests whether the KIND BUFFER outputs a (*).
    """

    api = database['mpi_allgather']
    parameter = api['parameters'][0]
    expression = bindingf90._construct_parameter(parameter)
    assert expression == 'SENDBUF(*)'


def test_kind_status_parenthetical(database):
    """
    Tests whether the KIND Status outputs a MPI_STATUS_SIZE.
    """

    api = database['mpi_wait']
    parameter = api['parameters'][1]
    expression = bindingf90._construct_parameter(parameter)

    assert expression == 'STATUS(MPI_STATUS_SIZE)'


def test_kind_cbuffer4_parenthetical(database):
    """
    Tests whether the KIND C_BUFFER4 outputs (parameter['length']).
    """

    api = database['mpi_user_function']
    parameter = api['parameters'][0]
    expression = bindingf90._construct_parameter(parameter)

    assert expression == 'INVEC(LEN)'


def test_kind_string_2darray_parenthetical(database):
    """
    Tests whether the STRING 2DARRAY KIND outputs (length, *).
    """

    api = database['mpi_comm_spawn_multiple']
    parameter = api['parameters'][2]
    expression = bindingf90._construct_parameter(parameter)

    assert expression == 'ARRAY_OF_ARGV(COUNT, *)'


def test_length_array_parentheical(database):
    """
    Tests whether the length parameter as a list is correctly output.

    MPI_Group_range_incl, MPI_Group_range_excl
    """

    api = database['mpi_group_range_incl']
    parameter = api['parameters'][2]
    expression = bindingf90._construct_parameter(parameter)

    assert expression == 'RANGES(3, *)'


def test_kind_string_parenthetical(database):
    """
    Tests whether the STRING KIND is correct.
    """

    api = database['mpi_add_error_string']
    parameter = api['parameters'][1]
    expression = bindingf90._construct_parameter(parameter)

    assert expression == 'STRING'


def test_special_mpif_macro(database):
    """
    Tests whether the special macro is correctly used.
    """

    api = database['mpi_status_f082f']

    expression = bindingf90.emit_binding(api, '', SMALL_F90_KIND_MAP)

    assert r'\mpifbindspecial' in expression


