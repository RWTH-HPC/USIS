<!-- source: OpenMP API Specification, section 18.5.3 (omp_in_final) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.5.3 omp_in_final

Summary
The omp_in_final routine returns true if the routine is executed in a final task region;
otherwise, it returns false.
Format
                                                      C / C++
int omp_in_final(void);
                                                      C / C++
                                                      Fortran
logical function omp_in_final()
                                                       Fortran
Binding
The binding task set for an omp_in_final region is the generating task.
Effect
omp_in_final returns true if the enclosing task region is final. Otherwise, it returns false.
