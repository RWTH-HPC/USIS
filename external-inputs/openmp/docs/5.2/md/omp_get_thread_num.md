<!-- source: OpenMP API Specification, section 18.2.4 (omp_get_thread_num) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.2.4 omp_get_thread_num

Summary
The omp_get_thread_num routine returns the thread number, within the current team, of the
calling thread.
Format
                                                      C / C++
int omp_get_thread_num(void);
                                                      C / C++
                                                      Fortran
integer function omp_get_thread_num()
                                                      Fortran

Binding
The binding thread set for an omp_get_thread_num region is the current team. The binding
region for an omp_get_thread_num region is the innermost enclosing parallel region.

Effect
The omp_get_thread_num routine returns the thread number of the calling thread, within the
team that is executing the parallel region to which the routine region binds. The thread number is
an integer between 0 and one less than the value returned by omp_get_num_threads,
inclusive. The thread number of the primary thread of the team is 0.

Cross References
• omp_get_num_threads, see Section 18.2.2
