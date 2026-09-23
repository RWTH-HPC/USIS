<!-- source: OpenMP API Specification, section 18.2.19 (omp_get_team_size) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.2.19 omp_get_team_size

Summary
The omp_get_team_size routine returns, for a given nested level of the current thread, the size
of the thread team to which the ancestor or the current thread belongs.

Format
                                                 C / C++
int omp_get_team_size(int level);
                                                 C / C++
                                                 Fortran
integer function omp_get_team_size(level)
integer level
                                                 Fortran
Binding
The binding thread set for an omp_get_team_size region is the encountering thread. The
binding region for an omp_get_team_size region is the innermost enclosing parallel
region.

Effect
The omp_get_team_size routine returns the size of the thread team to which the ancestor or
the current thread belongs. If the requested nested level is outside the range of 0 and the nested
level of the current thread, as returned by the omp_get_level routine, the routine returns -1.
Inactive parallel regions are regarded as active parallel regions executed with one thread.
 6

Note – When the omp_get_team_size routine is called with a value of level=0, the routine
always returns 1. If level=omp_get_level(), the routine has the same effect as the
omp_get_num_threads routine.
10

Cross References
• omp_get_level, see Section 18.2.17
• omp_get_num_threads, see Section 18.2.2
• parallel directive, see Section 10.1
