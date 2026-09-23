"""
Tests for the F08 Binding generation.
"""


# pylint: disable=import-error
# pylint: disable=protected-access
# pylint: disable=redefined-outer-name


import bindingf08
from bindingtypes import SMALL_F08_KIND_MAP, BIG_F08_KIND_MAP


def test_normal_parameter_list(database):
    """
    Tests if a normal parameter list is correctly emitted.

    An example is MPI_Wait.
    """

    parseset = database['mpi_wait']
    parameters = parseset['parameters']
    parameter_list = bindingf08._emit_parameter_list(parameters)

    assert parameter_list == '(request, status, ierror)'


def test_parameter_list_with_suppressed(database):
    """
    Tests if suppressed parameters are treated correctly.

    An example of this is MPI_Init.
    """

    api = database['mpi_init']

    parameters = list(filter(
        lambda p: (p['kind'] != 'VARARGS' and
                   'f08_parameter' not in p['suppress']),
        api['parameters']))

    parameter_list = bindingf08._emit_parameter_list(parameters)

    assert parameter_list == '(ierror)'


def test_parameter_list_with_varargs(database):
    """
    Tests if varargs are ignored.
    """

    api = database['mpi_pcontrol']
    parameters = list(filter(
        lambda p: (p['kind'] != 'VARARGS' and
                   'f08_parameter' not in p['suppress']),
        api['parameters']))

    parameter_list = bindingf08._emit_parameter_list(parameters)

    assert parameter_list == '(level)'


def test_expressibility(database):
    """
    Tests if an expressible F08 API is expressed.
    """

    api = database['mpi_init']
    expression = bindingf08.emit_binding(api, '', SMALL_F08_KIND_MAP)
    assert expression is not None


def test_inexpressibility(database):
    """
    Tests whether an inexpressible F08 API is expressed.
    """

    api = database['mpi_t_cvar_handle_alloc']
    expression = bindingf08.emit_binding(api, '', SMALL_F08_KIND_MAP)
    assert expression is None


def test_inexpressibility_with_proxy_phrase(database):
    """
    Tests whether an inexpressible F08 API is not expressed, but a proxy phrase
    is used when required.
    """

    api = database['mpi_keyval_create']
    expression = bindingf08.emit_binding(api, '', SMALL_F08_KIND_MAP)

    assert expression == (r'\mpifnewnonebind{For this routine, an interface '
                          r'within the \code{mpi\_f08} module was never '
                          r'defined.}')


def test_callback_macro(database):
    """
    Tests whether the correct latex macro is returned for a callback.
    """

    api = database['mpi_comm_copy_attr_function']

    expression = bindingf08._emit_latex_macro(api, SMALL_F08_KIND_MAP)

    assert 'mpifnewsubbind' in expression


def test_non_callback_macro(database):
    """
    Tests whether the correct latex macro is returned for a non-callback
    API.
    """

    api = database['mpi_send']

    expression = bindingf08._emit_latex_macro(api, SMALL_F08_KIND_MAP)
    assert 'mpifnewbindmain' in expression


def test_asynchronous_attribute(database):
    """
    Tests whether the 'asynchronous' attribute of the F08 type
    is correctly expressed.
    """

    api = database['mpi_send_init']

    expression = bindingf08._emit_asynchronous_attribute(api['parameters'][0])
    assert 'ASYNCHRONOUS' in expression

    expression = bindingf08._emit_asynchronous_attribute(api['parameters'][1])
    assert 'ASYNCHRONOUS' not in expression


def test_optional_attribute(database):
    """
    Tests whether the 'optional' attribute of the F08 type
    is correctly expressed.
    """

    api = database['mpi_send']

    expression = bindingf08._emit_optional_attribute(api['parameters'][0])
    assert 'OPTIONAL' not in expression

    expression = bindingf08._emit_optional_attribute(api['parameters'][-1])
    assert 'OPTIONAL' in expression


def test_callbacks_no_intent(database):
    """
    Tests whether callbacks don't output an intent attribute.
    """

    api = database['mpi_comm_copy_attr_function']

    expression = bindingf08.emit_binding(api, '', SMALL_F08_KIND_MAP)

    assert 'INTENT' not in expression


def test_predefined_functions_no_intent(database):
    """
    Tests whether predefined functions don't output an intent attribute.
    """

    api = database['mpi_comm_dup_fn']

    expression = bindingf08.emit_binding(api, '', SMALL_F08_KIND_MAP)

    assert 'INTENT' not in expression


def test_string_type_length(database):
    """
    Tests whether the kind STRING outputs a type length.
    """

    api = database['mpi_add_error_string']
    parameter = api['parameters'][1]

    expression = bindingf08._emit_type_length(parameter)

    assert expression == '(LEN=*)'


def test_string_2darray_type_length(database):
    """
    Tests whether the kind STRING_2DARRAY outputs a type length.
    """

    api = database['mpi_comm_spawn_multiple']
    parameter = api['parameters'][2]

    expression = bindingf08._emit_type_length(parameter)

    assert expression == '(LEN=*)'


def test_buffer_type_length(database):
    """
    Tests whether the kind STRING doesn't output a type length.
    """

    api = database['mpi_send']
    parameter = api['parameters'][0]

    expression = bindingf08._emit_type_length(parameter)

    assert expression == ''


def test_parameter_type_function(database):
    """
    Tests whether the FUNCTION parameter type is correctly expressed.
    """

    api = database['mpi_comm_create_errhandler']
    parameter = api['parameters'][0]

    expression = bindingf08._emit_parameter_type(parameter,
                                                 '',
                                                 SMALL_F08_KIND_MAP)

    assert expression == 'PROCEDURE(MPI_Comm_errhandler_function)'


def test_parameter_type_normal(database):
    """
    Tests whether a non-FUNCTION parameter type is correctly expressed.
    """

    api = database['mpi_wait']
    parameter = api['parameters'][0]

    expression = bindingf08._emit_parameter_type(parameter,
                                                 '',
                                                 SMALL_F08_KIND_MAP)

    assert expression == 'TYPE(MPI_Request)'


def test_return_kind_error_code(database):
    """
    Tests whether an ERROR_CODE return kind is erroneously expressed.

    regression
    """

    api = database['mpi_reduce_scatter']

    expression = bindingf08._emit_return_kind(api, SMALL_F08_KIND_MAP)

    assert expression == ''


def test_return_kind_wall_time(database):
    """
    Tests whether a WALL_TIME return kind is correctly expressed.

    regression
    """

    api = database['mpi_wtime']

    expression = bindingf08._emit_return_kind(api, SMALL_F08_KIND_MAP)

    assert expression == 'DOUBLE PRECISION '


def test_ierror_intent(database):
    """
    Tests whether the MPI_TYPE_NULL_DELETE_FN predefined function
    outputs the intent attribute for the ierror parameter.
    """

    api = database['mpi_type_null_delete_fn']

    expression = bindingf08.emit_binding(api, '', SMALL_F08_KIND_MAP)

    assert r'INTEGER, INTENT(OUT)\ ::\ \mbox{ierror}' in expression


def test_non_polyfunction_expression_no_postfix(database):
    """
    Tests whether a FUNCTION[_SMALL] parameter correctly does not receive
    the postfix.
    """

    api = database['mpi_comm_create_errhandler']
    parameter = api['parameters'][0]

    expression = bindingf08._emit_parameter_type(parameter,
                                                 '_x',
                                                 SMALL_F08_KIND_MAP)

    assert expression.startswith('PROCEDURE(MPI_Comm_errhandler_function)')


def test_mpi_comm_errhandler_function(database):
    """
    Regression test for MPI_Comm_errhandler_function which erroneously printed
    a varargs parameter in F08.
    """

    api = database['mpi_comm_errhandler_function']

    expression = bindingf08.emit_binding(api, '', SMALL_F08_KIND_MAP)

    print(expression)
    assert 'None' not in expression
    assert 'varargs' not in expression


def test_embiggening_comment(database):
    """
    Tests whether a comment "!(_c)" is present for an embiggened interface.
    """

    api = database['mpi_send']

    postfix = '_c'

    # NOTE: non-empty postfix requires emitter to emit the large count binding

    expression = bindingf08.emit_binding(api, postfix, BIG_F08_KIND_MAP)

    assert f"!({postfix})" in expression


def test_embiggening_comment_not_in_normal_interfaces(database):
    """
    Tests whether a non-embiggend interface contains the embiggenment comment.

    It shouldn't.
    """

    api = database['mpi_session_get_num_psets']

    postfix = '_c'

    # TODO this is a bit of a no-op test, the postfix anything other than ''
    #      means that the comment should appear, so we can't test the existance
    #      at all really. This will be fixed by binding-tool v2.

    # NOTE: empty postfix requires emitter to emit the non-large count binding

    expression = bindingf08.emit_binding(api, '', SMALL_F08_KIND_MAP)

    assert f"!({postfix})" not in expression


def test_capitalized_property(database):
    """
    Tests whether the capitalization property correctly uses only
    uses uppercase letters.
    """

    api = database['mpi_conversion_fn_null']

    expression = bindingf08.emit_binding(api, '', SMALL_F08_KIND_MAP)

    assert r"MPI_CONVERSION_FN_NULL" in expression
