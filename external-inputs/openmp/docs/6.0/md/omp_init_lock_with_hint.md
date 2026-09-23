<!-- source: OpenMP API Specification, section 28.1.3 (omp_init_lock_with_hint Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 28 Lock Routines -->

# 28.1.3 omp_init_lock_with_hint Routine

Name: omp_init_lock_with_hint                           Properties: all-contention-group-
Category: subroutine                                    tasks-binding, lock-initializing, simple-
                                                                    lock

Arguments
            Name                                      Type                         Properties
svar                                      lock                         C/C++ pointer, omp
            hint                                      sync_hint                    omp

Prototypes
                                                      C / C++
void omp_init_lock_with_hint(omp_lock_t *svar,
omp_sync_hint_t hint);
                                                      C / C++
                                                      Fortran
subroutine omp_init_lock_with_hint(svar, hint)
integer (kind=omp_lock_kind) svar
integer (kind=omp_sync_hint_kind) hint
                                                      Fortran
Effect
The omp_init_lock_with_hint routine is a lock-initializing routine.

Execution Model Events
The lock-init-with-hint event occurs in a thread that executes an omp_init_lock_with_hint
region after initialization of the lock, but before it finishes the region.

Tool Callbacks
A thread dispatches a registered lock_init callback with the same value for its hint argument as
the hint argument of the call to omp_init_lock_with_hint and ompt_mutex_lock as
the kind argument for each occurrence of a lock-init-with-hint event in that thread. This callback
occurs in the task that encounters the routine.

Cross References
• OpenMP lock Type, see Section 20.9.3
• lock_init Callback, see Section 34.7.9
• OMPT mutex Type, see Section 33.20
• OpenMP sync_hint Type, see Section 20.9.5
