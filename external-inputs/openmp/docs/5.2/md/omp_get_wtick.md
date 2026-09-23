<!-- source: OpenMP API Specification, section 18.10.2 (omp_get_wtick) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.10.2 omp_get_wtick

Summary
The omp_get_wtick routine returns the precision of the timer used by omp_get_wtime.

Format
                                                        C / C++
double omp_get_wtick(void);
                                                        C / C++
                                                        Fortran
double precision function omp_get_wtick()
                                                        Fortran
Binding
The binding thread set for an omp_get_wtick region is the encountering thread. The routine’s
return value is not guaranteed to be consistent across any set of threads.

Effect
The omp_get_wtick routine returns a value equal to the number of seconds between successive
clock ticks of the timer used by omp_get_wtime.
