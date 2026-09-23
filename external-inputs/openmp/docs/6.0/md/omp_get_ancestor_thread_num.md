<!-- source: OpenMP API Specification, section 21.15 (omp_get_ancestor_thread_num Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 21 Parallel Region Support Routines -->

# 21.15 omp_get_ancestor_thread_num Routine

Name: omp_get_ancestor_thread_num                         Properties: default
23
      Category: function

Return Type and Arguments
            Name                                         Type                         Properties
<return type>                                integer                      default
            level                                        integer                      default

Prototypes
                                                         C / C++
int omp_get_ancestor_thread_num(int level);
                                                         C / C++
                                                         Fortran
integer function omp_get_ancestor_thread_num(level)
integer level
                                                         Fortran
Effect
The omp_get_ancestor_thread_num routine returns the thread number of the ancestor
thread at a given nest level of the encountering thread or the thread number of the encountering
thread. If the requested nest level is outside the range of 0 and the nest level of the encountering
thread, as returned by the omp_get_level routine, the routine returns -1.
12
Note – When the omp_get_ancestor_thread_num routine is called with value of level =0,
the routine always returns 0. If level =omp_get_level(), the routine has the same effect as the
omp_get_thread_num routine.
16

Cross References
• omp_get_level Routine, see Section 21.14
• omp_get_thread_num Routine, see Section 21.3
