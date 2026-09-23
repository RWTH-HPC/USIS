<!-- source: OpenMP API Specification, section 28.2.1 (omp_destroy_lock Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 28 Lock Routines -->

# 28.2.1 omp_destroy_lock Routine

Name: omp_destroy_lock                                    Properties: all-contention-group-
Category: subroutine                                      tasks-binding, lock-destroying, simple-
                                                                      lock

Arguments
            Name                                         Type                       Properties
10
            svar                                         lock                       C/C++ pointer, omp

Prototypes
                                                        C / C++
void omp_destroy_lock(omp_lock_t *svar);
                                                        C / C++
                                                        Fortran
subroutine omp_destroy_lock(svar)
integer (kind=omp_lock_kind) svar
                                                        Fortran
Effect
The omp_destroy_lock routine is a lock-destroying routine.

Execution Model Events
The lock-destroy event occurs in a thread that executes an omp_destroy_lock region before it
finishes the region.

Tool Callbacks
A thread dispatches a registered lock_destroy callback with ompt_mutex_lock as the kind
argument for each occurrence of a lock-destroy event in that thread. This callback occurs in the task
that encounters the routine.

Cross References
• OpenMP lock Type, see Section 20.9.3
• lock_destroy Callback, see Section 34.7.11
• OMPT mutex Type, see Section 33.20
