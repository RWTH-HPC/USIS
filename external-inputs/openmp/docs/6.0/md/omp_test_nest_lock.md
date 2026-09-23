<!-- source: OpenMP API Specification, section 28.5.2 (omp_test_nest_lock Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 28 Lock Routines -->

# 28.5.2 omp_test_nest_lock Routine

Name: omp_test_nest_lock                                Properties: all-contention-group-
Category: function                                      tasks-binding, lock-testing, nestable-
                                                                    lock
Return Type and Arguments
            Name                                      Type                         Properties
<return type>                             integer                      default
            nvar                                      nest_lock                    C/C++ pointer, omp

Prototypes
                                                      C / C++
int omp_test_nest_lock(omp_nest_lock_t *nvar);
                                                      C / C++
                                                      Fortran
integer function omp_test_nest_lock(nvar)
integer (kind=omp_nest_lock_kind) nvar
                                                      Fortran
Effect
The omp_test_nest_lock routine returns the new nesting count if it successfully sets the lock;
otherwise, it returns zero.

Execution Model Events
The nest-lock-test event occurs in a thread that executes an omp_test_nest_lock region
before the associated lock is tested. The nest-lock-test-acquired event occurs in a thread that
executes an omp_test_nest_lock region before it finishes the region if the associated lock
was acquired and the thread did not already own the lock. The nest-lock-owned event occurs in a
thread that executes an omp_test_nest_lock region before it finishes the region after the
nesting count is incremented if the thread already owned the lock.

Tool Callbacks
A thread dispatches a registered mutex_acquire callback for each occurrence of a nest-lock-test
event in that thread. A thread dispatches a registered mutex_acquired callback for each
occurrence of a nest-lock-test-acquired event in that thread. A thread dispatches a registered
nest_lock callback with ompt_scope_begin as its endpoint argument for each occurrence
of a nest-lock-owned event in that thread. These callbacks occur in the encountering task and their
kind argument is ompt_mutex_test_nest_lock.

Cross References
• OMPT mutex Type, see Section 33.20
• mutex_acquire Callback, see Section 34.7.8
• mutex_acquired Callback, see Section 34.7.12
• nest_lock Callback, see Section 34.7.14
• OpenMP nest_lock Type, see Section 20.9.4
• OMPT scope_endpoint Type, see Section 33.27
