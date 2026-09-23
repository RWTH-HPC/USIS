<!-- source: OpenMP API Specification, section 28.3.1 (omp_set_lock Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 28 Lock Routines -->

# 28.3.1 omp_set_lock Routine

Name: omp_set_lock                                         Properties: all-contention-group-
Category: subroutine                                       tasks-binding, lock-acquiring, simple-
                                                                       lock

Arguments
            Name                                         Type                          Properties
17
            svar                                         lock                          C/C++ pointer, omp

Prototypes
                                                         C / C++
void omp_set_lock(omp_lock_t *svar);
                                                         C / C++
                                                         Fortran
subroutine omp_set_lock(svar)
integer (kind=omp_lock_kind) svar
                                                         Fortran
Effect
A simple lock is available when it is in the unlocked state. Ownership of the lock is granted to the
task that executes the routine.

Execution Model Events
The lock-acquire event occurs in a thread that executes an omp_set_lock region before the
associated lock is requested. The lock-acquired event occurs in a thread that executes an
omp_set_lock region after it acquires the associated lock but before it finishes the region.

Tool Callbacks
A thread dispatches a registered mutex_acquire callback for each occurrence of a lock-acquire
event in that thread. A thread dispatches a registered mutex_acquired callback for each
occurrence of a lock-acquired event in that thread. These callbacks occur in the task that encounters
the omp_set_lock routine and their kind argument is ompt_mutex_lock.

Restrictions
Restrictions to the omp_set_lock routine are as follows:
• A task must not already own the lock that it accesses with a call to omp_set_lock (or
deadlock will result).

Cross References
• OpenMP lock Type, see Section 20.9.3
• OMPT mutex Type, see Section 33.20
• mutex_acquire Callback, see Section 34.7.8
• mutex_acquired Callback, see Section 34.7.12
