<!-- source: OpenMP API Specification, section 18.3.10 (omp_display_affinity) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.3.10 omp_display_affinity

Summary
The omp_display_affinity routine prints the OpenMP thread affinity information using the
format specification provided.
Format
                                                          C / C++
void omp_display_affinity(const char *format);
                                                          C / C++
                                                          Fortran
subroutine omp_display_affinity(format)
character(len=*),intent(in) :: format
                                                          Fortran
Binding
The binding thread set for an omp_display_affinity region is the encountering thread.

Effect
The omp_display_affinity routine prints the thread affinity information of the current
thread in the format specified by the format argument, followed by a new-line. If the format is
NULL (for C/C++) or a zero-length string (for Fortran and C/C++), the value of the
affinity-format-var ICV is used. If the format argument does not conform to the specified format
then the result is implementation defined.

Cross References
• affinity-format-var ICV, see Table 2.1
