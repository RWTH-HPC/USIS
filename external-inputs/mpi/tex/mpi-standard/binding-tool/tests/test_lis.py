"""
Tests for the Collectives chapter.
"""


# pylint: disable=import-error
# pylint: disable=protected-access
# pylint: disable=redefined-outer-name


from bindingtypes import LIS_KIND_MAP
import bindinglis


def test_expressibility(database):
    """
    Tests whether a API marked as expressible is expressible.
    """

    api = database['mpi_alloc_mem']

    expression = bindinglis.emit_binding(api, '', LIS_KIND_MAP)

    assert expression is not None


def test_inexpressibility(database):
    """
    Tests whether an LIS in expressible API is not expressed.
    """

    api = database['mpi_comm_errhandler_function']

    expression = bindinglis.emit_binding(api, '', LIS_KIND_MAP)

    assert expression is None


def test_array_of_prefix(database):
    """
    Tests if the 'array of' prefix is attached to the parenthetical if the
    length of the parameter is not None.

    This applies to MPI_Waitall, MPI_Waitany, etc.
    """

    parameter = database['mpi_waitall']['parameters'][1]

    parenthetical = bindinglis._emit_parameter_lis_type(
        parameter,
        LIS_KIND_MAP[parameter['kind']])

    assert 'array of ' in parenthetical


def test_plural_status(database):
    """
    Tests whether plural of STATUS is correctly determined.

    An example is MPI_Waitall.
    """

    parameter = database['mpi_waitall']['parameters'][2]
    assert parameter['kind'] == 'STATUS'

    parenthetical = bindinglis._emit_parameter_lis_type(
        parameter,
        LIS_KIND_MAP[parameter['kind']])

    assert parenthetical == '(array of status)'


def test_plural_normal(database):
    """
    Tests whether plurals of non-STATUS is correctly determined.

    An example is MPI_Waitall.
    """

    parameter = database['mpi_waitall']['parameters'][1]
    assert parameter['kind'] != 'STATUS'

    parenthetical = bindinglis._emit_parameter_lis_type(
        parameter,
        LIS_KIND_MAP[parameter['kind']])

    assert 's' in parenthetical


def test_varargs_in_parameter_list(database):
    """
    Tests if the ... is placed in the parameter list.

    This applies for any VARAGS parameter, used in MPI_Pcontrol.
    """

    parameters = database['mpi_pcontrol']['parameters']

    parameter_list = bindinglis._emit_parameter_list(parameters)

    assert ''.join(parameter_list) == r'(\mbox{level}, \mbox{\ldots})'


def test_normal_parameter_list(database):
    """
    Tests if the parameter list is emitted properly.

    An example is MPI_Wait without VARARGS.
    """

    parameters = database['mpi_wait']['parameters']

    valid_parameters = list(filter(
        lambda p: 'lis_parameter' not in p['suppress'], parameters))

    parameter_list = bindinglis._emit_parameter_list(valid_parameters)

    assert ''.join(parameter_list) == r'(\mbox{request}, \mbox{status})'


def test_api_name_capitalization(database):
    """
    Tests whether the name of the API is capitalized in the LIS binding.

    Any function with an LIS binding is an example.
    """

    parseset = database['mpi_recv']

    prototype = bindinglis._emit_api_prototype(parseset,
                                               parseset['parameters'])

    assert prototype[:prototype.find('}')] == 'MPI_RECV'


def test_last_parameter_description_exists(database):
    """
    Tests whether the last parameters descriptions is correctly written.

    Regression error
    """

    api = database['mpi_type_get_attr']
    parameter = api['parameters'][2]

    expression = bindinglis._emit_parameter_description(
        parameter,
        LIS_KIND_MAP[parameter['kind']])

    assert expression != ''


def test_no_lis_type_with_root_only(database):
    """
    Tests whether the '(significant only at root)' is placed at the end of an
    LIS description even if the type is suppressed.
    """

    api = database['mpi_gatherv']
    parameter = api['parameters'][4]

    expression = bindinglis._emit_parameter_lis_type(
        parameter,
        LIS_KIND_MAP[parameter['kind']])

    assert expression == "(significant only at root)"


def test_large_only_parenthetical(database):
    """
    Tests whether the large_only "only present for large count variants" is
    correctly expressed.
    """

    api = database['mpi_type_get_envelope']
    parameter = api['parameters'][3]

    expression = bindinglis._emit_parameter_lis_type(
        parameter,
        LIS_KIND_MAP[parameter['kind']])
    assert "only present for large count variants" in expression

    api = database['mpi_send']
    parameter = api['parameters'][0]

    expression = bindinglis._emit_parameter_lis_type(
        parameter,
        LIS_KIND_MAP[parameter['kind']])
    assert "only present for large count variants" not in expression
