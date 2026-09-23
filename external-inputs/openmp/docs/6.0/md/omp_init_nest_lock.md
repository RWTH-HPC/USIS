<!-- source: OpenMP API Specification, section 28.1.2 (omp_init_nest_lock Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 28 Lock Routines -->

# 28.1.2 omp_init_nest_lock Routine

Name: omp_init_nest_lock                                Properties: all-contention-group-
Category: subroutine                                    tasks-binding, lock-initializing,
                                                              nestable-lock

Arguments
      Name                                       Type                        Properties
 8
      nvar                                       nest_lock                   C/C++ pointer, omp

Prototypes
                                                C / C++
void omp_init_nest_lock(omp_nest_lock_t *nvar);
                                                C / C++
                                                Fortran
subroutine omp_init_nest_lock(nvar)
integer (kind=omp_nest_lock_kind) nvar
                                                 Fortran
Effect
The omp_init_nest_lock routine is a lock-initializing routine.

Execution Model Events
The nest-lock-init event occurs in a thread that executes an omp_init_nest_lock region after
initialization of the lock, but before it finishes the region.

Tool Callbacks
A thread dispatches a registered lock_init callback with omp_sync_hint_none as the hint
argument and ompt_mutex_nest_lock as the kind argument for each occurrence of a
nest-lock-init event in that thread. This callback occurs in the task that encounters the routine.

Cross References
• lock_init Callback, see Section 34.7.9
• OMPT mutex Type, see Section 33.20
• OpenMP nest_lock Type, see Section 20.9.4
