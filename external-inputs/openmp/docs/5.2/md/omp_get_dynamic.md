<!-- source: OpenMP API Specification, section 18.2.7 (omp_get_dynamic) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.2.7 omp_get_dynamic

Summary
The omp_get_dynamic routine returns the value of the dyn-var ICV, which determines whether
dynamic adjustment of the number of threads is enabled or disabled.

Format
                                                      C / C++
int omp_get_dynamic(void);
                                                      C / C++
                                                      Fortran
logical function omp_get_dynamic()
                                                      Fortran

Binding
The binding task set for an omp_get_dynamic region is the generating task.

Effect
This routine returns true if dynamic adjustment of the number of threads is enabled for the current
task; otherwise, it returns false. If an implementation does not support dynamic adjustment of the
number of threads, then this routine always returns false.

Cross References
• dyn-var ICV, see Table 2.1
