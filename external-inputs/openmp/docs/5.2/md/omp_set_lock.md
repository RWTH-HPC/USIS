<!-- source: OpenMP API Specification, section 18.9.4 (omp_set_lock and omp_set_nest_lock) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->
<!-- section shared with: omp_set_nest_lock -->

# 18.9.4 omp_set_lock and omp_set_nest_lock

Summary
These routines provide a means of setting an OpenMP lock. The calling task region behaves as if it
was suspended until the lock can be set by this task.

Format
                                                   C / C++
void omp_set_lock(omp_lock_t *lock);
void omp_set_nest_lock(omp_nest_lock_t *lock);
                                                   C / C++
                                                   Fortran
subroutine omp_set_lock(svar)
integer (kind=omp_lock_kind) svar
10
subroutine omp_set_nest_lock(nvar)
integer (kind=omp_nest_lock_kind) nvar
                                                   Fortran
Constraints on Arguments
A program that accesses a lock that is in the uninitialized state through either routine is
non-conforming. A simple lock accessed by omp_set_lock that is in the locked state must not
be owned by the task that contains the call or deadlock will result.

Effect
Each of these routines has an effect equivalent to suspension of the task that is executing the routine
until the specified lock is available.
20

Note – The semantics of these routines is specified as if they serialize execution of the region
guarded by the lock. However, implementations may implement them in other ways provided that
the isolation properties are respected so that the actual execution delivers a result that could arise
from some serialization.
25

A simple lock is available if it is unlocked. Ownership of the lock is granted to the task that
executes the routine. A nestable lock is available if it is unlocked or if it is already owned by the
task that executes the routine. The task that executes the routine is granted, or retains, ownership of
the lock, and the nesting count for the lock is incremented.

Execution Model Events
The lock-acquire event occurs in a thread that executes an omp_set_lock region before the
associated lock is requested. The nest-lock-acquire event occurs in a thread that executes an
omp_set_nest_lock region before the associated lock is requested.
The lock-acquired event occurs in a thread that executes an omp_set_lock region after it
acquires the associated lock but before it finishes the region. The nest-lock-acquired event occurs in
a thread that executes an omp_set_nest_lock region if the thread did not already own the
lock, after it acquires the associated lock but before it finishes the region.
The nest-lock-owned event occurs in a thread when it already owns the lock and executes an
omp_set_nest_lock region. The event occurs after the nesting count is incremented but
before the thread finishes the region.
Tool Callbacks
A thread dispatches a registered ompt_callback_mutex_acquire callback for each
occurrence of a lock-acquire or nest-lock-acquire event in that thread. This callback has the type
signature ompt_callback_mutex_acquire_t.
A thread dispatches a registered ompt_callback_mutex_acquired callback for each
occurrence of a lock-acquired or nest-lock-acquired event in that thread. This callback has the type
signature ompt_callback_mutex_t.
A thread dispatches a registered ompt_callback_nest_lock callback with
ompt_scope_begin as its endpoint argument for each occurrence of a nest-lock-owned event in
that thread. This callback has the type signature ompt_callback_nest_lock_t.
The above callbacks occur in the task that encounters the lock function. The kind argument of these
callbacks is ompt_mutex_lock when the events arise from an omp_set_lock region while it
is ompt_mutex_nest_lock when the events arise from an omp_set_nest_lock region.
Cross References
• ompt_callback_mutex_acquire_t, see Section 19.5.2.14
• ompt_callback_mutex_t, see Section 19.5.2.15
• ompt_callback_nest_lock_t, see Section 19.5.2.16
