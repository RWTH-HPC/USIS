<!-- source: OpenMP API Specification, section 28.1.4 (omp_init_nest_lock_with_hint Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 28 Lock Routines -->

# 28.1.4 omp_init_nest_lock_with_hint Routine

Name: omp_init_nest_lock_with_hint                     Properties: all-contention-group-
Category: subroutine                                   tasks-binding, lock-initializing,
                                                             nestable-lock

Arguments
      Name                                     Type                        Properties
nvar                                     nest_lock                   C/C++ pointer, omp
      hint                                     sync_hint                   omp

Prototypes
                                               C / C++
void omp_init_nest_lock_with_hint(omp_nest_lock_t *nvar,
omp_sync_hint_t hint);
                                               C / C++
                                               Fortran
subroutine omp_init_nest_lock_with_hint(nvar, hint)
integer (kind=omp_nest_lock_kind) nvar
integer (kind=omp_sync_hint_kind) hint
                                               Fortran
Effect
The omp_init_nest_lock_with_hint routine is a lock-initializing routine.

Execution Model Events
The nest-lock-init-with-hint event occurs in a thread that executes an omp_init_nest_lock
region after initialization of the lock, but before it finishes the region.

Tool Callbacks
A thread dispatches a registered lock_init callback with the same value for its hint argument as
the hint argument of the call to omp_init_nest_lock_with_hint and
ompt_mutex_nest_lock as the kind argument for each occurrence of a nest-lock-init-with-hint
event in that thread This callback occurs in the task that encounters the routine.

Cross References
• lock_init Callback, see Section 34.7.9
• OMPT mutex Type, see Section 33.20
• OpenMP nest_lock Type, see Section 20.9.4
• OpenMP sync_hint Type, see Section 20.9.5
