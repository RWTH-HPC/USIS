<!-- source: OpenMP API Specification, section 18.9.6 (omp_test_lock and omp_test_nest_lock) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->
<!-- section shared with: omp_test_lock -->

# 18.9.6 omp_test_lock and omp_test_nest_lock

Summary
These routines attempt to set an OpenMP lock but do not suspend execution of the task that
executes the routine.

Format
                                                        C / C++
int omp_test_lock(omp_lock_t *lock);
int omp_test_nest_lock(omp_nest_lock_t *lock);
                                                        C / C++
                                                        Fortran
logical function omp_test_lock(svar)
integer (kind=omp_lock_kind) svar
10
integer function omp_test_nest_lock(nvar)
integer (kind=omp_nest_lock_kind) nvar
                                                        Fortran
Constraints on Arguments
A program that accesses a lock that is in the uninitialized state through either routine is
non-conforming. The behavior is unspecified if a simple lock accessed by omp_test_lock is in
the locked state and is owned by the task that contains the call.

Effect
These routines attempt to set a lock in the same manner as omp_set_lock and
omp_set_nest_lock, except that they do not suspend execution of the task that executes the
routine. For a simple lock, the omp_test_lock routine returns true if the lock is successfully
set; otherwise, it returns false. For a nestable lock, the omp_test_nest_lock routine returns
the new nesting count if the lock is successfully set; otherwise, it returns zero.

Execution Model Events
The lock-test event occurs in a thread that executes an omp_test_lock region before the
associated lock is tested. The nest-lock-test event occurs in a thread that executes an
omp_test_nest_lock region before the associated lock is tested.
The lock-test-acquired event occurs in a thread that executes an omp_test_lock region before it
finishes the region if the associated lock was acquired. The nest-lock-test-acquired event occurs in a
thread that executes an omp_test_nest_lock region before it finishes the region if the
associated lock was acquired and the thread did not already own the lock.
The nest-lock-owned event occurs in a thread that executes an omp_test_nest_lock region
before it finishes the region after the nesting count is incremented if the thread already owned the
lock.

Tool Callbacks
A thread dispatches a registered ompt_callback_mutex_acquire callback for each
occurrence of a lock-test or nest-lock-test event in that thread. This callback has the type signature
ompt_callback_mutex_acquire_t.
A thread dispatches a registered ompt_callback_mutex_acquired callback for each
occurrence of a lock-test-acquired or nest-lock-test-acquired event in that thread. This callback has
the type signature ompt_callback_mutex_t.
A thread dispatches a registered ompt_callback_nest_lock callback with
ompt_scope_begin as its endpoint argument for each occurrence of a nest-lock-owned event in
that thread. This callback has the type signature ompt_callback_nest_lock_t.
The above callbacks occur in the task that encounters the lock function. The kind argument of these
callbacks is ompt_mutex_test_lock when the events arise from an omp_test_lock
region while it is ompt_mutex_test_nest_lock when the events arise from an
omp_test_nest_lock region.

Cross References
• ompt_callback_mutex_acquire_t, see Section 19.5.2.14
• ompt_callback_mutex_t, see Section 19.5.2.15
• ompt_callback_nest_lock_t, see Section 19.5.2.16
