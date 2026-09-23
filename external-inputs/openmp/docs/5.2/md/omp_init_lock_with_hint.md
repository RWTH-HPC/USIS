<!-- source: OpenMP API Specification, section 18.9.2 (omp_init_lock_with_hint and omp_init_nest_lock_with_hint) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->
<!-- section shared with: omp_init_nest_lock_with_hint -->

# 18.9.2 omp_init_lock_with_hint and omp_init_nest_lock_with_hint

omp_init_nest_lock_with_hint
Summary
These routines initialize an OpenMP lock with a hint. The effect of the hint is
implementation-defined. The OpenMP implementation can ignore the hint without changing
program semantics.

Format
                                                          C / C++
void omp_init_lock_with_hint(
omp_lock_t *lock,
omp_sync_hint_t hint
);
void omp_init_nest_lock_with_hint(
omp_nest_lock_t *lock,
omp_sync_hint_t hint
);
                                                          C / C++

                                                    Fortran
subroutine omp_init_lock_with_hint(svar, hint)
integer (kind=omp_lock_kind) svar
integer (kind=omp_sync_hint_kind) hint
 4
subroutine omp_init_nest_lock_with_hint(nvar, hint)
integer (kind=omp_nest_lock_kind) nvar
integer (kind=omp_sync_hint_kind) hint
                                                    Fortran
Constraints on Arguments
A program that accesses a lock that is not in the uninitialized state through either routine is
non-conforming. The second argument passed to these routines (hint) is a hint as described in
Section 15.1.

Effect
The effect of these routines is to initialize the lock to the unlocked state and, optionally, to choose a
specific lock implementation based on the hint. After initialization no task owns the lock. In
addition, the nesting count for a nestable lock is set to zero.

Execution Model Events
The lock-init-with-hint event occurs in a thread that executes an omp_init_lock_with_hint
region after initialization of the lock, but before it finishes the region. The nest-lock-init-with-hint
event occurs in a thread that executes an omp_init_nest_lock region after initialization of the
lock, but before it finishes the region.

Tool Callbacks
A thread dispatches a registered ompt_callback_lock_init callback with the same value
for its hint argument as the hint argument of the call to omp_init_lock_with_hint and
ompt_mutex_lock as the kind argument for each occurrence of a lock-init-with-hint event in
that thread. Similarly, a thread dispatches a registered ompt_callback_lock_init callback
with the same value for its hint argument as the hint argument of the call to
omp_init_nest_lock_with_hint and ompt_mutex_nest_lock as the kind argument
for each occurrence of a nest-lock-init-with-hint event in that thread. These callbacks have the type
signature ompt_callback_mutex_acquire_t and occur in the task that encounters the
routine.

Cross References
• Synchronization Hints, see Section 15.1
• ompt_callback_mutex_acquire_t, see Section 19.5.2.14
