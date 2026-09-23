<!-- source: OpenMP API Specification, section 29.10 (omp_display_affinity Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 29 Thread Affinity Routines -->

# 29.10 omp_display_affinity Routine

Name: omp_display_affinity                               Properties: default
20
      Category: subroutine

Arguments
      Name                                         Type                       Properties
22
      format                                       char                       pointer, intent(in)

Prototypes
                                                   C / C++
void omp_display_affinity(const char *format);
                                                   C / C++

                                                         Fortran
subroutine omp_display_affinity(format)
character(len=*), intent(in) :: format
                                                         Fortran
Effect
The omp_display_affinity routine prints the thread affinity information of the encountering
thread in the format specified by the format argument, followed by a new-line. If the format is
NULL (for C/C++) or a zero-length string (for Fortran and C/C++), the value of the
affinity-format-var ICV is used. If the format argument does not conform to the specified format
then the result is implementation defined.

Restrictions
Restrictions to the omp_display_affinity routine are as follows:
• When called from within a target region the effect is unspecified.

Cross References
• affinity-format-var ICV, see Table 3.1
• target Construct, see Section 15.8
