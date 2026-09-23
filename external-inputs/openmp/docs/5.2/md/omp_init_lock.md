<!-- source: OpenMP API Specification, section 18.9.1 (omp_init_lock and omp_init_nest_lock) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->
<!-- section shared with: omp_init_nest_lock -->

# 18.9.1 omp_init_lock and omp_init_nest_lock

Summary
These routines initialize an OpenMP lock without a hint.

Format
                                                  C / C++
void omp_init_lock(omp_lock_t *lock);
void omp_init_nest_lock(omp_nest_lock_t *lock);
                                                  C / C++
                                                  Fortran
subroutine omp_init_lock(svar)
integer (kind=omp_lock_kind) svar
26
subroutine omp_init_nest_lock(nvar)
integer (kind=omp_nest_lock_kind) nvar
                                                  Fortran

Constraints on Arguments
A program that accesses a lock that is not in the uninitialized state through either routine is
non-conforming.

Effect
The effect of these routines is to initialize the lock to the unlocked state; that is, no task owns the
lock. In addition, the nesting count for a nestable lock is set to zero.

Execution Model Events
The lock-init event occurs in a thread that executes an omp_init_lock region after initialization
of the lock, but before it finishes the region. The nest-lock-init event occurs in a thread that executes
an omp_init_nest_lock region after initialization of the lock, but before it finishes the region.

Tool Callbacks
A thread dispatches a registered ompt_callback_lock_init callback with
omp_sync_hint_none as the hint argument and ompt_mutex_lock as the kind argument
for each occurrence of a lock-init event in that thread. Similarly, a thread dispatches a registered
ompt_callback_lock_init callback with omp_sync_hint_none as the hint argument
and ompt_mutex_nest_lock as the kind argument for each occurrence of a nest-lock-init
event in that thread. These callbacks have the type signature
ompt_callback_mutex_acquire_t and occur in the task that encounters the routine.

Cross References
• ompt_callback_mutex_acquire_t, see Section 19.5.2.14
