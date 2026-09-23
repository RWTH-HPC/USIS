<!-- source: OpenMP API Specification, section 18.2.2 (omp_get_num_threads) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.2.2 omp_get_num_threads

Summary
The omp_get_num_threads routine returns the number of threads in the current team.

Format
                                                   C / C++
int omp_get_num_threads(void);
                                                   C / C++
                                                   Fortran
integer function omp_get_num_threads()
                                                   Fortran
Binding
The binding region for an omp_get_num_threads region is the innermost enclosing parallel
region.

Effect
The omp_get_num_threads routine returns the number of threads in the team that is executing
the parallel region to which the routine region binds.
