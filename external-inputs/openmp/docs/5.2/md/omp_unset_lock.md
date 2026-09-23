<!-- source: OpenMP API Specification, section 18.9.5 (omp_unset_lock and omp_unset_nest_lock) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->
<!-- section shared with: omp_unset_nest_lock -->

# 18.9.5 omp_unset_lock and omp_unset_nest_lock

Summary
These routines provide the means of unsetting an OpenMP lock.
Format
                                                        C / C++
void omp_unset_lock(omp_lock_t *lock);
void omp_unset_nest_lock(omp_nest_lock_t *lock);
                                                        C / C++

                                                   Fortran
subroutine omp_unset_lock(svar)
integer (kind=omp_lock_kind) svar
 3
subroutine omp_unset_nest_lock(nvar)
integer (kind=omp_nest_lock_kind) nvar
                                                   Fortran
Constraints on Arguments
A program that accesses a lock that is not in the locked state or that is not owned by the task that
contains the call through either routine is non-conforming.

Effect
For a simple lock, the omp_unset_lock routine causes the lock to become unlocked. For a
nestable lock, the omp_unset_nest_lock routine decrements the nesting count, and causes the
lock to become unlocked if the resulting nesting count is zero. For either routine, if the lock
becomes unlocked, and if one or more task regions were effectively suspended because the lock was
unavailable, the effect is that one task is chosen and given ownership of the lock.

Execution Model Events
The lock-release event occurs in a thread that executes an omp_unset_lock region after it
releases the associated lock but before it finishes the region. The nest-lock-release event occurs in a
thread that executes an omp_unset_nest_lock region after it releases the associated lock but
before it finishes the region.
The nest-lock-held event occurs in a thread that executes an omp_unset_nest_lock region
before it finishes the region when the thread still owns the lock after the nesting count is
decremented.

Tool Callbacks
A thread dispatches a registered ompt_callback_mutex_released callback with
ompt_mutex_lock as the kind argument for each occurrence of a lock-release event in that
thread. Similarly, a thread dispatches a registered ompt_callback_mutex_released
callback with ompt_mutex_nest_lock as the kind argument for each occurrence of a
nest-lock-release event in that thread. These callbacks have the type signature
ompt_callback_mutex_t and occur in the task that encounters the routine.
A thread dispatches a registered ompt_callback_nest_lock callback with
ompt_scope_end as its endpoint argument for each occurrence of a nest-lock-held event in that
thread. This callback has the type signature ompt_callback_nest_lock_t.

Cross References
• ompt_callback_mutex_t, see Section 19.5.2.15
• ompt_callback_nest_lock_t, see Section 19.5.2.16
