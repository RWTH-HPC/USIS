<!-- source: OpenMP API Specification, section 18.9.3 (omp_destroy_lock and omp_destroy_nest_lock) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->
<!-- section shared with: omp_destroy_lock -->

# 18.9.3 omp_destroy_lock and omp_destroy_nest_lock

Summary
These routines ensure that the OpenMP lock is uninitialized.

Format
                                                         C / C++
void omp_destroy_lock(omp_lock_t *lock);
void omp_destroy_nest_lock(omp_nest_lock_t *lock);
                                                         C / C++
                                                         Fortran
subroutine omp_destroy_lock(svar)
integer (kind=omp_lock_kind) svar
 9
subroutine omp_destroy_nest_lock(nvar)
integer (kind=omp_nest_lock_kind) nvar
                                                          Fortran
Constraints on Arguments
A program that accesses a lock that is not in the unlocked state through either routine is
non-conforming.

Effect
The effect of these routines is to change the state of the lock to uninitialized.

Execution Model Events
The lock-destroy event occurs in a thread that executes an omp_destroy_lock region before it
finishes the region. The nest-lock-destroy event occurs in a thread that executes an
omp_destroy_nest_lock region before it finishes the region.

Tool Callbacks
A thread dispatches a registered ompt_callback_lock_destroy callback with
ompt_mutex_lock as the kind argument for each occurrence of a lock-destroy event in that
thread. Similarly, a thread dispatches a registered ompt_callback_lock_destroy callback
with ompt_mutex_nest_lock as the kind argument for each occurrence of a nest-lock-destroy
event in that thread. These callbacks have the type signature ompt_callback_mutex_t and
occur in the task that encounters the routine.

Cross References
• ompt_callback_mutex_t, see Section 19.5.2.15
