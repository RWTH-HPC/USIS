<!-- source: OpenMP API Specification, section 28.4.1 (omp_unset_lock Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 28 Lock Routines -->

# 28.4.1 omp_unset_lock Routine

Name: omp_unset_lock                                      Properties: all-contention-group-
Category: subroutine                                      tasks-binding, lock-releasing, simple-
                                                                lock

Arguments
      Name                                        Type                         Properties
 7
      svar                                        lock                         C/C++ pointer, omp

Prototypes
                                                 C / C++
void omp_unset_lock(omp_lock_t *svar);
                                                 C / C++
                                                 Fortran
subroutine omp_unset_lock(svar)
integer (kind=omp_lock_kind) svar
                                                  Fortran
Effect
The omp_unset_lock routine changes the lock state to the unlocked state.

Execution Model Events
The lock-release event occurs in a thread that executes an omp_unset_lock region after it
releases the associated lock but before it finishes the region.

Tool Callbacks
A thread dispatches a registered mutex_released callback with ompt_mutex_lock as the
kind argument for each occurrence of a lock-release event in that thread. This callback occurs in the
encountering task.

Cross References
• OpenMP lock Type, see Section 20.9.3
• OMPT mutex Type, see Section 33.20
• mutex_released Callback, see Section 34.7.13
