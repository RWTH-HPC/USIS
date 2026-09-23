<!-- source: OpenMP API Specification, section 28.4.2 (omp_unset_nest_lock Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 28 Lock Routines -->

# 28.4.2 omp_unset_nest_lock Routine

Name: omp_unset_nest_lock                                  Properties: all-contention-group-
Category: subroutine                                       tasks-binding, lock-releasing, nestable-
                                                                       lock

Arguments
            Name                                         Type                          Properties
4
            nvar                                         nest_lock                     C/C++ pointer, omp

Prototypes
                                                         C / C++
void omp_unset_nest_lock(omp_nest_lock_t *nvar);
                                                         C / C++
                                                         Fortran
subroutine omp_unset_nest_lock(nvar)
integer (kind=omp_nest_lock_kind) nvar
                                                         Fortran
Effect
The omp_unset_nest_lock routine decrements the nesting count and, if the resulting nesting
count is zero, changes the lock state to the unlocked state.

Execution Model Events
The nest-lock-release event occurs in a thread that executes an omp_unset_nest_lock region
after it releases the associated lock but before it finishes the region. The nest-lock-held event occurs
in a thread that executes an omp_unset_nest_lock region before it finishes the region when
the thread still owns the lock after the nesting count is decremented.

Tool Callbacks
A thread dispatches a registered mutex_released callback with ompt_mutex_nest_lock
as the kind argument for each occurrence of a nest-lock-release event in that thread. A thread
dispatches a registered nest_lock callback with ompt_scope_end as its endpoint argument
for each occurrence of a nest-lock-held event in that thread. These callbacks occur in the
encountering task.

Cross References
• OMPT mutex Type, see Section 33.20
• mutex_released Callback, see Section 34.7.13
• nest_lock Callback, see Section 34.7.14
• OpenMP nest_lock Type, see Section 20.9.4
• OMPT scope_endpoint Type, see Section 33.27
