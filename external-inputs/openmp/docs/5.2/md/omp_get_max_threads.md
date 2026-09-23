<!-- source: OpenMP API Specification, section 18.2.3 (omp_get_max_threads) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.2.3 omp_get_max_threads

Summary
The omp_get_max_threads routine returns an upper bound on the number of threads that
could be used to form a new team if a parallel construct without a num_threads clause is
encountered after execution returns from this routine.
Format
                                                      C / C++
int omp_get_max_threads(void);
                                                      C / C++
                                                      Fortran
integer function omp_get_max_threads()
                                                      Fortran
Binding
The binding task set for an omp_get_max_threads region is the generating task.
Effect
The value returned by omp_get_max_threads is the value of the first element of the
nthreads-var ICV of the current task. This value is also an upper bound on the number of threads
that could be used to form a new team if a parallel region without a num_threads clause is
encountered after execution returns from this routine.
Cross References
• Determining the Number of Threads for a parallel Region, see Section 10.1.1
• nthreads-var ICV, see Table 2.1
• num_threads clause, see Section 10.1.2
• parallel directive, see Section 10.1
