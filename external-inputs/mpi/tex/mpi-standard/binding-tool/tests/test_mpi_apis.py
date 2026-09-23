"""
This file is for regression tests on APIs that have caused feedback from
chapter authors.
"""


import pytest


from bindingtypes import LIS_KIND_MAP
from bindingtypes import SMALL_F08_KIND_MAP
from bindingtypes import SMALL_C_KIND_MAP

import bindinglis
import bindingf08
import bindingc


def test_mpi_comm_spawn_multiple(database):
    """
    Tests whether MPI_Comm_spawn_multiple is correct.
    """

    api = database['mpi_comm_spawn_multiple']

    bindinglis.init(None)
    expression = bindinglis.emit_binding(api, '', LIS_KIND_MAP).split('\n')

    truth = (
        r"\begin{funcdef}{MPI\_COMM\_SPAWN\_MULTIPLE}{(\mbox{count}, \mbox{array\_of\_commands}, \mbox{array\_of\_argv}, \mbox{array\_of\_maxprocs}, \mbox{array\_of\_info}, \mbox{root}, \mbox{comm}, \mbox{intercomm}, \mbox{array\_of\_errcodes})}",
        r"\funcarg{\IN}{count}{number of commands (positive integer, significant only at root)}",
        r"\funcarg{\IN}{array\_of\_commands}{programs to be executed (array of strings, significant only at root)}",
        r"\funcarg{\IN}{array\_of\_argv}{arguments for \mpiarg{commands} (array of array of strings, significant only at root)}",
        r"\funcarg{\IN}{array\_of\_maxprocs}{maximum number of processes to start for each command (array of integers, significant only at root)}",
        r"\funcarg{\IN}{array\_of\_info}{info objects telling the runtime system where and how to start processes (array of handles, significant only at root)}",
        r"\funcarg{\IN}{root}{rank of process in which previous arguments are examined (integer)}",
        r"\funcarg{\IN}{comm}{intra-communicator containing group of spawning processes (handle)}",
        r"\funcarg{\OUT}{intercomm}{inter-communicator between original group and the newly spawned group (handle)}",
        r"\funcarg{\OUT}{array\_of\_errcodes}{one error code per process (array of integers)}",
        r"\end{funcdef}"
        )

    truth = (line.replace('\\_', '_') for line in truth)

    for idx, pair in enumerate(zip(expression, truth)):
        assert pair[0] == pair[1], f"line {idx} failed to match"


def test_mpi_win_create(database):
    """
    Tests whether MPI_Win_create is correct.
    """

    api = database['mpi_win_create']

    # TODO refactor generators into classes!
    bindinglis.init(None)
    expression = bindinglis.emit_binding(api, '', LIS_KIND_MAP).split('\n')

    truth = (
        r"\begin{funcdef}{MPI\_WIN\_CREATE}{(\mbox{base}, \mbox{size}, \mbox{disp\_unit}, \mbox{info}, \mbox{comm}, \mbox{win})}",
        r"\funcarg{\IN}{base}{initial address of window (choice)}",
        r"\funcarg{\IN}{size}{size of window in bytes (nonnegative integer)}",
        r"\funcarg{\IN}{disp\_unit}{local unit size for displacements, in bytes (positive integer)}",
        r"\funcarg{\IN}{info}{info argument (handle)}",
        r"\funcarg{\IN}{comm}{intra-communicator (handle)}",
        r"\funcarg{\OUT}{win}{window object (handle)}",
        r"\end{funcdef}"
        )

    truth = (line.replace('\\_', '_') for line in truth)

    for idx, pair in enumerate(zip(expression, truth)):
        assert pair[0] == pair[1], f"line {idx} failed to match"


def test_mpi_win_allocate(database):
    """
    Tests whether MPI_Win_allocate is correct.
    """

    api = database['mpi_win_allocate']

    # TODO refactor generators into classes!
    bindinglis.init(None)
    expression = bindinglis.emit_binding(api, '', LIS_KIND_MAP).split('\n')

    truth = (
        r"\begin{funcdef}{MPI\_WIN\_ALLOCATE}{(\mbox{size}, \mbox{disp\_unit}, \mbox{info}, \mbox{comm}, \mbox{baseptr}, \mbox{win})}",
        r"\funcarg{\IN}{size}{size of window in bytes (nonnegative integer)}",
        r"\funcarg{\IN}{disp\_unit}{local unit size for displacements, in bytes (positive integer)}",
        r"\funcarg{\IN}{info}{info argument (handle)}",
        r"\funcarg{\IN}{comm}{intra-communicator (handle)}",
        r"\funcarg{\OUT}{baseptr}{initial address of window (choice)}",
        r"\funcarg{\OUT}{win}{window object (handle)}",
        r"\end{funcdef}"
        )

    truth = (line.replace('\\_', '_') for line in truth)

    for idx, pair in enumerate(zip(expression, truth)):
        assert pair[0] == pair[1], f"line {idx} failed to match"


def test_mpi_win_allocate_shared(database):
    """
    Tests whether MPI_Win_allocate_shared is correct.
    """

    api = database['mpi_win_allocate_shared']

    # TODO refactor generators into classes!
    bindinglis.init(None)
    expression = bindinglis.emit_binding(api, '', LIS_KIND_MAP).split('\n')

    truth = (
        r"\begin{funcdef}{MPI\_WIN\_ALLOCATE\_SHARED}{(\mbox{size}, \mbox{disp\_unit}, \mbox{info}, \mbox{comm}, \mbox{baseptr}, \mbox{win})}",
        r"\funcarg{\IN}{size}{size of local window in bytes (nonnegative integer)}",
        r"\funcarg{\IN}{disp\_unit}{local unit size for displacements, in bytes (positive integer)}",
        r"\funcarg{\IN}{info}{info argument (handle)}",
        r"\funcarg{\IN}{comm}{intra-communicator (handle)}",
        r"\funcarg{\OUT}{baseptr}{address of local allocated window segment (choice)}",
        r"\funcarg{\OUT}{win}{window object (handle)}",
        r"\end{funcdef}"
        )

    truth = (line.replace('\\_', '_') for line in truth)

    for idx, pair in enumerate(zip(expression, truth)):
        assert pair[0] == pair[1], f"line {idx} failed to match"


def test_mpi_put(database):
    """
    Tests whether MPI_Put is correct.
    """

    api = database['mpi_put']

    # TODO refactor generators into classes!
    bindinglis.init(None)
    expression = bindinglis.emit_binding(api, '', LIS_KIND_MAP).split('\n')

    truth = (
        r"\begin{funcdef}{MPI\_PUT}{(\mbox{origin\_addr}, \mbox{origin\_count}, \mbox{origin\_datatype}, \mbox{target\_rank}, \mbox{target\_disp}, \mbox{target\_count}, \mbox{target\_datatype}, \mbox{win})}",
        r"\funcarg{\IN}{origin\_addr}{initial address of origin buffer (choice)}",
        r"\funcarg{\IN}{origin\_count}{number of entries in origin buffer (nonnegative integer)}",
        r"\funcarg{\IN}{origin\_datatype}{datatype of each entry in origin buffer (handle)}",
        r"\funcarg{\IN}{target\_rank}{rank of target (nonnegative integer)}",
        r"\funcarg{\IN}{target\_disp}{displacement from start of window to target buffer (nonnegative integer)}",
        r"\funcarg{\IN}{target\_count}{number of entries in target buffer (nonnegative integer)}",
        r"\funcarg{\IN}{target\_datatype}{datatype of each entry in target buffer (handle)}",
        r"\funcarg{\IN}{win}{window used for communication (handle)}",
        r"\end{funcdef}"
        )

    truth = (line.replace('\\_', '_') for line in truth)

    for idx, pair in enumerate(zip(expression, truth)):
        assert pair[0] == pair[1], f"line {idx} failed to match"


def test_mpi_info_get(database):
    """
    Tests whether MPI_Info_get is expressed correctly.
    """

    api = database['mpi_info_get']

    bindinglis.init(None)
    expression = bindinglis.emit_binding(api, '', LIS_KIND_MAP).split('\n')

    truth = (
        r"\begin{funcdef}{MPI\_INFO\_GET}{(\mbox{info}, \mbox{key}, \mbox{valuelen}, \mbox{value}, \mbox{flag})}",
        r"\funcarg{\IN}{info}{info object (handle)}",
        r"\funcarg{\IN}{key}{key (string)}",
        r"\funcarg{\IN}{valuelen}{length of value associated with \mpiarg{key} (integer)}",
        r"\funcarg{\OUT}{value}{value (string)}",
        r"\funcarg{\OUT}{flag}{\mpicode{true} if \mpiarg{key} defined, \mpicode{false} if not (logical)}",
        r"\end{funcdef}"
        )

    truth = (line.replace('\\_', '_') for line in truth)

    for idx, pair in enumerate(zip(expression, truth)):
        assert pair[0] == pair[1], (f"line {idx} failed to match in MPI_INFO_GET" )

def test_mpi_is_thread_main(database):
    """
    Tests whether MPI_Is_thread_main is expressed correctly.
    """

    api = database['mpi_is_thread_main']

    bindinglis.init(None)
    expression = bindinglis.emit_binding(api, '', LIS_KIND_MAP).split('\n')

    truth = (
        r"\begin{funcdef}{MPI\_IS\_THREAD\_MAIN}{(\mbox{flag})}",
        r"\funcarg{\OUT}{flag}{true if calling thread is main thread, false otherwise (logical)}",
        r"\end{funcdef}"
        )

    truth = (line.replace('\\_', '_') for line in truth)

    for idx, pair in enumerate(zip(expression, truth)):
        assert pair[0] == pair[1], f"line {idx} failed to match"


def test_mpi_aint_add(database):
    """
    Tests whether MPI_Aint_add is expressed correctly.
    """

    api = database['mpi_aint_add']

    bindinglis.init(None)
    expression = bindinglis.emit_binding(api, '', LIS_KIND_MAP).split('\n')

    truth = (
        r"\begin{funcdef}{MPI\_AINT\_ADD}{(\mbox{base}, \mbox{disp})}",
        r"\funcarg{\IN}{base}{base address (integer)}",
        r"\funcarg{\IN}{disp}{displacement (integer)}",
        r"\end{funcdef}"
        )

    truth = (line.replace('\\_', '_') for line in truth)

    for idx, pair in enumerate(zip(expression, truth)):
        assert pair[0] == pair[1], f"line {idx} failed to match"


def test_mpi_aint_diff(database):
    """
    Tests whether MPI_Aint_diff is expressed correctly.
    """

    api = database['mpi_aint_diff']

    bindinglis.init(None)
    expression = bindinglis.emit_binding(api, '', LIS_KIND_MAP).split('\n')

    truth = (
        r"\begin{funcdef}{MPI\_AINT\_DIFF}{(\mbox{addr1}, \mbox{addr2})}",
        r"\funcarg{\IN}{addr1}{minuend address (integer)}",
        r"\funcarg{\IN}{addr2}{subtrahend address (integer)}",
        r"\end{funcdef}"
        )

    truth = (line.replace('\\_', '_') for line in truth)

    for idx, pair in enumerate(zip(expression, truth)):
        assert pair[0] == pair[1], f"line {idx} failed to match"


def test_mpi_get_address(database):
    """
    Tests whether MPI_Get_address is expressed correctly.
    """

    api = database['mpi_get_address']

    bindinglis.init(None)
    expression = bindinglis.emit_binding(api, '', LIS_KIND_MAP).split('\n')

    truth = (
        r"\begin{funcdef}{MPI\_GET\_ADDRESS}{(\mbox{location}, \mbox{address})}",
        r"\funcarg{\IN}{location}{location in caller memory (choice)}",
        r"\funcarg{\OUT}{address}{address of location (integer)}",
        r"\end{funcdef}"
        )

    truth = (line.replace('\\_', '_') for line in truth)

    for idx, pair in enumerate(zip(expression, truth)):
        assert pair[0] == pair[1], f"line {idx} failed to match"


def test_mpi_type_create_resized(database):
    """
    Tests whether MPI_Type_create_resized is expressed correctly.
    """

    api = database['mpi_type_create_resized']

    bindinglis.init(None)
    expression = bindinglis.emit_binding(api, '', LIS_KIND_MAP).split('\n')

    truth = (
        r"\begin{funcdef}{MPI\_TYPE\_CREATE\_RESIZED}{(\mbox{oldtype}, \mbox{lb}, "
        r"\mbox{extent}, \mbox{newtype})}",
        r"\funcarg{\IN}{oldtype}{input datatype (handle)}",
        r"\funcarg{\IN}{lb}{new lower bound of datatype (integer)}",
        r"\funcarg{\IN}{extent}{new extent of datatype (integer)}",
        r"\funcarg{\OUT}{newtype}{output datatype (handle)}",
        r"\end{funcdef}"
        )

    truth = (line.replace('\\_', '_') for line in truth)

    for idx, pair in enumerate(zip(expression, truth)):
        assert pair[0] == pair[1], f"line {idx} failed to match"


def test_mpi_allgatherv_init(database):
    """
    Tests whether MPI_Allgatherv_init is expressed correctly.
    """

    api = database['mpi_allgatherv_init']

    expression = bindingf08.emit_binding(api, '', SMALL_F08_KIND_MAP)

    truth = (
        r"\mpifnewbindmain{MPI\_Allgatherv\_init}{(sendbuf, sendcount, sendtype, "
        r"recvbuf, recvcounts, displs, recvtype, comm, info, request, ierror) "
        r"\fargs TYPE(*), DIMENSION(..), INTENT(IN), ASYNCHRONOUS\ ::\ \mbox{sendbuf}"
        r"\fnarg{}INTEGER, INTENT(IN)\ ::\ \mbox{sendcount}"
        r"\fnarg{}TYPE(MPI\_Datatype), INTENT(IN)\ ::\ \mbox{sendtype}, \mbox{recvtype}"
        r"\fnarg{}TYPE(*), DIMENSION(..), ASYNCHRONOUS\ ::\ \mbox{recvbuf}"
        r"\fnarg{}INTEGER, INTENT(IN), ASYNCHRONOUS\ ::\ \mbox{recvcounts(*)}, \mbox{displs(*)}"
        r"\fnarg{}TYPE(MPI\_Comm), INTENT(IN)\ ::\ \mbox{comm}"
        r"\fnarg{}TYPE(MPI\_Info), INTENT(IN)\ ::\ \mbox{info}"
        r"\fnarg{}TYPE(MPI\_Request), INTENT(OUT)\ ::\ \mbox{request}"
        r"\fnfinalarg{}INTEGER, OPTIONAL, INTENT(OUT)\ ::\ \mbox{ierror}}"
        )

    truth = truth.replace('\\_', '_')

    assert expression == truth


def test_mpi_neighbor_alltoallv(database):
    """
    Tests whether MPI_Neighbor_alltoallv is expressed correctly.
    """

    api = database['mpi_neighbor_alltoallv']

    expression = bindingf08.emit_binding(api, '', SMALL_F08_KIND_MAP)

    truth = (
        r"\mpifnewbindmain{MPI\_Neighbor\_alltoallv}{(sendbuf, sendcounts, sdispls, "
        r"sendtype, recvbuf, recvcounts, rdispls, recvtype, comm, ierror) "
        r"\fargs TYPE(*), DIMENSION(..), INTENT(IN)\ ::\ \mbox{sendbuf}"
        r"\fnarg{}INTEGER, INTENT(IN)\ ::\ \mbox{sendcounts(*)}, \mbox{sdispls(*)}, \mbox{recvcounts(*)}, "
        r"\mbox{rdispls(*)}"
        r"\fnarg{}TYPE(MPI\_Datatype), INTENT(IN)\ ::\ \mbox{sendtype}, \mbox{recvtype}"
        r"\fnarg{}TYPE(*), DIMENSION(..)\ ::\ \mbox{recvbuf}"
        r"\fnarg{}TYPE(MPI\_Comm), INTENT(IN)\ ::\ \mbox{comm}"
        r"\fnfinalarg{}INTEGER, OPTIONAL, INTENT(OUT)\ ::\ \mbox{ierror}}"
        )

    truth = truth.replace('\\_', '_')

    assert expression == truth


def test_mpi_null_delete_fn(database):
    """
    Tests whether the MPI_NULL_DELETE_FN is expressed correctly.
    """

    api = database['mpi_null_delete_fn']

    expression = bindingf08.emit_binding(api, '', SMALL_F08_KIND_MAP)

    assert expression is None


def test_mpi_datarep_extent_function(database):
    """
    Tests whether the MPI_Datarep_extent_function is expressed correctly.
    """

    api = database['mpi_datarep_extent_function']

    expression = bindingf08.emit_binding(api, '', SMALL_F08_KIND_MAP)

    truth = (
        r"\mpifnewsubbind{MPI\_Datarep\_extent\_function}{(datatype, extent, "
        r"extra\_state, ierror) \fargs "
        r"TYPE(MPI\_Datatype)\ ::\ \mbox{datatype}"
        r"\fnarg{}INTEGER(KIND=MPI\_ADDRESS\_KIND)\ ::\ \mbox{extent}, \mbox{extra\_state}\fnfinalarg{}"
        r"INTEGER\ ::\ \mbox{ierror}}"
        )

    truth = truth.replace('\\_', '_')

    assert expression == truth


def test_mpi_file_errhandler(database):
    """
    Tests whether the MPI_File_errhandler_function is expressed correctly.
    """

    api = database['mpi_file_errhandler_function']

    expression = bindingc.emit_binding(api, '', SMALL_C_KIND_MAP)

    truth = (
        r"\mpitypedefbindvoidmain{MPI\_File\_errhandler\_function}"
        r"{(\gb{}MPI\_File~*file, int~*error\_code, \ldots)}"
        )

    truth = truth.replace('\\_', '_')

    assert expression == truth
