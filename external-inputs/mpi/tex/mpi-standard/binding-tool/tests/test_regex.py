'''
Tests for the REGEX patterns in regress.py.
'''


import patterns


BINDINGS_F90 = [
    (r'\mpifbind{MPI\_SEND(BUF, COUNT, DATATYPE, DEST, TAG, COMM, IERROR)'
     r'\fargs <type> BUF(*) \\ '
     r'INTEGER  COUNT, DATATYPE, DEST, TAG, COMM, IERROR}'),

    (r'\mpifbind{SUBROUTINE MPI\_SEND(BUF, COUNT, DATATYPE, DEST, TAG, '
     r'COMM, IERROR) \fargs <type> BUF(*) \\ '
     r'INTEGER  COUNT, DATATYPE, DEST, TAG, COMM, IERROR}'),

    (r'\mpifbind{SUBROUTINE COPY\_FUNCTION(OLDCOMM, KEYVAL, EXTRA\_STATE, '
     r'ATTRIBUTE\_VAL\_IN, ATTRIBUTE\_VAL\_OUT, FLAG, IERR)'
     r'\fargs INTEGER OLDCOMM, KEYVAL, EXTRA\_STATE, ATTRIBUTE\_VAL\_IN, '
     r'ATTRIBUTE\_VAL\_OUT, IERR \\ LOGICAL FLAG}'),
    
    ]

BINDINGS_F90_SUB = [
    (r'\mpifsubbind{MPI\_DATAREP\_EXTENT\_FUNCTION(DATATYPE, FILE\_EXTENT, '
     r'EXTRA\_STATE, IERROR) \fargs INTEGER DATATYPE, IERROR \\ '
     r'INTEGER(KIND=MPI\_ADDRESS\_KIND) FILE\_EXTENT, EXTRA\_STATE}'),

    ]


BINDINGS_F08 = [
    (r'\mpifnewbind{MPI\_Wait(request, status, ierror) \fargs '
     r'TYPE(MPI\_Request), INTENT(INOUT) :: request \\ '
     r'TYPE(MPI\_Status) :: status \\ '
     r'INTEGER, OPTIONAL, INTENT(OUT) :: ierror}'),

    (r'\mpifnewbind{MPI\_Isend(buf, count, datatype, dest, tag, comm, '
     r'request, ierror) \fargs '
     r'TYPE(*), DIMENSION(..), INTENT(IN), ASYNCHRONOUS :: buf \\ '
     r'INTEGER, INTENT(IN) :: count, dest, tag \\ '
     r'TYPE(MPI\_Datatype), INTENT(IN) :: datatype \\ '
     r'TYPE(MPI\_Comm), INTENT(IN) :: comm \\ '
     r'TYPE(MPI\_Request), INTENT(OUT) :: request \\ '
     r'INTEGER, OPTIONAL, INTENT(OUT) :: ierror}'),

    ]

BINDINGS_F08_SUB = [
    (r'\mpifnewsubbind{MPI\_Datarep\_extent\_function(datatype, '
     r'file\_extent, extra\_state, ierror) \fargs '
     r'TYPE(MPI\_Datatype), INTENT(IN) :: datatype \\ '
     r'INTEGER(KIND=MPI\_ADDRESS\_KIND), INTENT(OUT) :: file\_extent, '
     r'extra\_state \\ INTEGER :: ierror}'),

    ]


def test_f90_binding_pattern():
    '''
    Test all strings against the F90 binding pattern.
    '''

    bindings = []
    truth = []

    bindings.extend(BINDINGS_F08_SUB)
    truth.extend([False] * len(BINDINGS_F08_SUB))

    bindings.extend(BINDINGS_F08)
    truth.extend([False] * len(BINDINGS_F08))

    bindings.extend(BINDINGS_F90_SUB)
    truth.extend([False] * len(BINDINGS_F90_SUB))

    bindings.extend(BINDINGS_F90)
    truth.extend([True] * len(BINDINGS_F90))

    matches = [patterns.PATTERN_F90_BINDING.match(binding)
               for binding in bindings]

    assert all((a is not None) == b for a, b in zip(matches, truth))


def test_f90_sub_binding_pattern():
    '''
    Test all bindings against the F90 SUB pattern.
    '''

    bindings = []
    truth = []

    bindings.extend(BINDINGS_F08_SUB)
    truth.extend([False] * len(BINDINGS_F08_SUB))

    bindings.extend(BINDINGS_F08)
    truth.extend([False] * len(BINDINGS_F08))

    bindings.extend(BINDINGS_F90_SUB)
    truth.extend([True] * len(BINDINGS_F90_SUB))

    bindings.extend(BINDINGS_F90)
    truth.extend([False] * len(BINDINGS_F90))

    matches = [patterns.PATTERN_F90_SUB_BINDING.match(binding)
               for binding in bindings]

    assert all((a is not None) == b for a, b in zip(matches, truth))


def test_f08_binding_pattern():
    '''
    Test all bindings against the F08 binding pattern.
    '''

    bindings = []
    truth = []

    bindings.extend(BINDINGS_F08_SUB)
    truth.extend([False] * len(BINDINGS_F08_SUB))

    bindings.extend(BINDINGS_F08)
    truth.extend([True] * len(BINDINGS_F08))

    bindings.extend(BINDINGS_F90_SUB)
    truth.extend([False] * len(BINDINGS_F90_SUB))

    bindings.extend(BINDINGS_F90)
    truth.extend([False] * len(BINDINGS_F90))

    matches = [patterns.PATTERN_F08_BINDING.match(binding)
               for binding in bindings]

    assert all((a is not None) == b for a, b in zip(matches, truth))


def test_f08_sub_binding_pattern():
    '''
    Test all bindings against the F08 SUB binding.
    '''

    bindings = []
    truths = []

    bindings.extend(BINDINGS_F08_SUB)
    truths.extend([True] * len(BINDINGS_F08_SUB))

    bindings.extend(BINDINGS_F08)
    truths.extend([False] * len(BINDINGS_F08))

    bindings.extend(BINDINGS_F90_SUB)
    truths.extend([False] * len(BINDINGS_F90_SUB))

    bindings.extend(BINDINGS_F90)
    truths.extend([False] * len(BINDINGS_F90))

    matches = [patterns.PATTERN_F08_SUB_BINDING.match(binding)
               for binding in bindings]

    for match, truth, binding in zip(matches, truths, bindings):
        assert (match is not None) == truth, binding
