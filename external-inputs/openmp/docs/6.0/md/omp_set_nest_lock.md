<!-- source: OpenMP API Specification, section 28.3.2 (omp_set_nest_lock Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 28 Lock Routines -->

# 28.3.2 omp_set_nest_lock Routine

Name: omp_set_nest_lock                                  Properties: all-contention-group-
Category: subroutine                                     tasks-binding, lock-acquiring, nestable-
                                                               lock

Arguments
      Name                                        Type                        Properties
22
      nvar                                        nest_lock                   C/C++ pointer, omp

Prototypes
                                                 C / C++
void omp_set_nest_lock(omp_nest_lock_t *nvar);
                                                 C / C++
                                                 Fortran
subroutine omp_set_nest_lock(nvar)
integer (kind=omp_nest_lock_kind) nvar
                                                  Fortran

Effect
A nestable lock is available if it is in the unlocked state or if it is already owned by the task that
executes the routine. The task that executes the routine is granted, or retains, ownership of the lock,
and the nesting count for the lock is incremented.

Execution Model Events
The nest-lock-acquire event occurs in a thread that executes an omp_set_nest_lock region
before the associated lock is requested. The nest-lock-acquired event occurs in a thread that
executes an omp_set_nest_lock region if the task did not already own the lock, after it
acquires the associated lock but before it finishes the region. The nest-lock-owned event occurs in a
task when it already owns the lock and executes an omp_set_nest_lock region. The
nest-lock-owned event occurs after the nesting count is incremented but before the task finishes the
region.

Tool Callbacks
A thread dispatches a registered mutex_acquire callback for each occurrence of a
nest-lock-acquire event in that thread. A thread dispatches a registered mutex_acquired
callback for each occurrence of a nest-lock-acquired event in that thread. A thread dispatches a
registered nest_lock callback with ompt_scope_begin as its endpoint argument for each
occurrence of a nest-lock-owned event in that thread. These callbacks occur in the task that
encounters the omp_set_nest_lock routine and their kind argument is
ompt_mutex_nest_lock.

Cross References
• OMPT mutex Type, see Section 33.20
• mutex_acquire Callback, see Section 34.7.8
• mutex_acquired Callback, see Section 34.7.12
• nest_lock Callback, see Section 34.7.14
• OpenMP nest_lock Type, see Section 20.9.4
• OMPT scope_endpoint Type, see Section 33.27
