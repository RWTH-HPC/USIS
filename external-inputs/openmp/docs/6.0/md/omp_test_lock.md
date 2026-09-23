<!-- source: OpenMP API Specification, section 28.5.1 (omp_test_lock Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 28 Lock Routines -->

# 28.5.1 omp_test_lock Routine

Name: omp_test_lock                                        Properties: all-contention-group-
 9
      Category: function                                         tasks-binding, lock-testing, simple-lock
Return Type and Arguments
      Name                                         Type                         Properties
<return type>                                logical                      default
      svar                                         lock                         C/C++ pointer, omp

Prototypes
                                                  C / C++
int omp_test_lock(omp_lock_t *svar);
                                                  C / C++
                                                  Fortran
logical function omp_test_lock(svar)
integer (kind=omp_lock_kind) svar
                                                   Fortran
Effect
The omp_test_lock routine returns true if it successfully acquires the lock; otherwise, it returns
false.

Execution Model Events
The lock-test event occurs in a thread that executes an omp_test_lock region before the
associated lock is tested. The lock-test-acquired event occurs in a thread that executes an
omp_test_lock region before it finishes the region if the associated lock was acquired.

Tool Callbacks
A thread dispatches a registered mutex_acquire callback for each occurrence of a lock-test
event in that thread. A thread dispatches a registered mutex_acquired callback for each
occurrence of a lock-test-acquired event in that thread. These callbacks occur in the encountering
task and their kind argument is ompt_mutex_test_lock.

Restrictions
Restrictions to omp_test_lock routines are as follows:
• An omp_test_lock routine must not access a lock that is already owned by the
encountering task.

Cross References
• OpenMP lock Type, see Section 20.9.3
• OMPT mutex Type, see Section 33.20
• mutex_acquire Callback, see Section 34.7.8
• mutex_acquired Callback, see Section 34.7.12
