<!-- source: OpenMP API Specification, section 18.2.8 (omp_get_cancellation) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.2.8 omp_get_cancellation

Summary
The omp_get_cancellation routine returns the value of the cancel-var ICV, which
determines if cancellation is enabled or disabled.

Format
                                                   C / C++
int omp_get_cancellation(void);
                                                   C / C++
                                                   Fortran
logical function omp_get_cancellation()
                                                   Fortran
Binding
The binding task set for an omp_get_cancellation region is the whole program.

Effect
This routine returns true if cancellation is enabled. It returns false otherwise.

Cross References
• cancel-var ICV, see Table 2.1
