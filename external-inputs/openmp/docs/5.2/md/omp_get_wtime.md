<!-- source: OpenMP API Specification, section 18.10.1 (omp_get_wtime) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.10.1 omp_get_wtime

Summary
The omp_get_wtime routine returns elapsed wall clock time in seconds.

Format
                                                  C / C++
double omp_get_wtime(void);
                                                  C / C++
                                                  Fortran
double precision function omp_get_wtime()
                                                   Fortran
Binding
The binding thread set for an omp_get_wtime region is the encountering thread. The routine’s
return value is not guaranteed to be consistent across any set of threads.

Effect
The omp_get_wtime routine returns a value equal to the elapsed wall clock time in seconds
since some time-in-the-past. The actual time-in-the-past is arbitrary, but it is guaranteed not to
change during the execution of the application program. The time returned is a per-thread time, so
it is not required to be globally consistent across all threads that participate in an application.
