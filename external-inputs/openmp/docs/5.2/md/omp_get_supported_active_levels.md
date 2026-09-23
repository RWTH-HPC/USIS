<!-- source: OpenMP API Specification, section 18.2.14 (omp_get_supported_active_levels) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.2.14 omp_get_supported_active_levels

Summary
The omp_get_supported_active_levels routine returns the number of active levels of
parallelism supported by the implementation.

Format
                                                        C / C++
int omp_get_supported_active_levels(void);
                                                        C / C++
                                                        Fortran
integer function omp_get_supported_active_levels()
                                                        Fortran
Binding
The binding task set for an omp_get_supported_active_levels region is the generating
task.

Effect
The omp_get_supported_active_levels routine returns the number of active levels of
parallelism supported by the implementation. The max-active-levels-var ICV cannot have a value
that is greater than this number. The value that the omp_get_supported_active_levels
routine returns is implementation defined, but it must be greater than 0.

Cross References
• max-active-levels-var ICV, see Table 2.1
