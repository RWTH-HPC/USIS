<!-- source: OpenMP API Specification, section 28.2.2 (omp_destroy_nest_lock Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 28 Lock Routines -->

# 28.2.2 omp_destroy_nest_lock Routine

Name: omp_destroy_nest_lock                              Properties: all-contention-group-
Category: subroutine                                     tasks-binding, lock-destroying,
                                                               nestable-lock

Arguments
      Name                                        Type                        Properties
 8
      nvar                                        nest_lock                   C/C++ pointer, omp

Prototypes
                                                 C / C++
void omp_destroy_nest_lock(omp_nest_lock_t *nvar);
                                                 C / C++
                                                 Fortran
subroutine omp_destroy_nest_lock(nvar)
integer (kind=omp_nest_lock_kind) nvar
                                                  Fortran
Effect
The omp_destroy_nest_lock routine is a lock-destroying routine.

Execution Model Events
The nest-lock-destroy event occurs in a thread that executes an omp_destroy_nest_lock
region before it finishes the region.

Tool Callbacks
A thread dispatches a registered lock_destroy callback with ompt_mutex_nest_lock as
the kind argument for each occurrence of a nest-lock-destroy event in that thread. This occurs in the
task that encounters the routine.

Cross References
• lock_destroy Callback, see Section 34.7.11
• OMPT mutex Type, see Section 33.20
• OpenMP nest_lock Type, see Section 20.9.4
