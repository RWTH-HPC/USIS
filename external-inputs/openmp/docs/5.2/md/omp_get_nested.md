<!-- source: OpenMP API Specification, section 18.2.10 (omp_get_nested (Deprecated)) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.2.10 omp_get_nested (Deprecated)

Summary
The deprecated omp_get_nested routine returns whether nested parallelism is enabled or
disabled, according to the value of the max-active-levels-var ICV.

Format
                                                        C / C++
int omp_get_nested(void);
                                                        C / C++
                                                        Fortran
logical function omp_get_nested()
                                                         Fortran
Binding
The binding task set for an omp_get_nested region is the generating task.

Effect
This routine returns true if max-active-levels-var is greater than 1 and greater than active-levels-var
for the current task; it returns false otherwise. If an implementation does not support nested
parallelism, this routine always returns false. This routine has been deprecated.

Cross References
• max-active-levels-var ICV, see Table 2.1
