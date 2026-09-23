<!-- source: OpenMP API Specification, section 18.2.18 (omp_get_ancestor_thread_num) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.2.18 omp_get_ancestor_thread_num

Summary
The omp_get_ancestor_thread_num routine returns, for a given nested level of the current
thread, the thread number of the ancestor of the current thread.

Format
                                                       C / C++
int omp_get_ancestor_thread_num(int level);
                                                       C / C++
                                                       Fortran
integer function omp_get_ancestor_thread_num(level)
integer level
                                                       Fortran

Binding
The binding thread set for an omp_get_ancestor_thread_num region is the encountering
thread. The binding region for an omp_get_ancestor_thread_num region is the innermost
enclosing parallel region.

Effect
The omp_get_ancestor_thread_num routine returns the thread number of the ancestor at a
given nest level of the current thread or the thread number of the current thread. If the requested
nest level is outside the range of 0 and the nest level of the current thread, as returned by the
omp_get_level routine, the routine returns -1.
10

Note – When the omp_get_ancestor_thread_num routine is called with a value of
level=0, the routine always returns 0. If level=omp_get_level(), the routine has the
same effect as the omp_get_thread_num routine.
14

Cross References
• omp_get_level, see Section 18.2.17
• omp_get_thread_num, see Section 18.2.4
• parallel directive, see Section 10.1
