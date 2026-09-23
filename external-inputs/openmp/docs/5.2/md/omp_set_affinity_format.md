<!-- source: OpenMP API Specification, section 18.3.8 (omp_set_affinity_format) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.3.8 omp_set_affinity_format

Summary
The omp_set_affinity_format routine sets the affinity format to be used on the device by
setting the value of the affinity-format-var ICV.

Format
                                                       C / C++
void omp_set_affinity_format(const char *format);
                                                       C / C++
                                                       Fortran
subroutine omp_set_affinity_format(format)
character(len=*),intent(in) :: format
                                                       Fortran

Binding
When called from a sequential part of the program, the binding thread set for an
omp_set_affinity_format region is the encountering thread. When called from within any
parallel or teams region, the binding thread set (and binding region, if required) for the
omp_set_affinity_format region is implementation defined.

Effect
The effect of omp_set_affinity_format routine is to copy the character string specified by
the format argument into the affinity-format-var ICV on the current device.
This routine has the described effect only when called from a sequential part of the program. When
called from within a parallel or teams region, the effect of this routine is implementation
defined.

Cross References
• Controlling OpenMP Thread Affinity, see Section 10.1.3
• OMP_AFFINITY_FORMAT, see Section 21.2.5
• OMP_DISPLAY_AFFINITY, see Section 21.2.4
• omp_capture_affinity, see Section 18.3.11
• omp_display_affinity, see Section 18.3.10
• omp_get_affinity_format, see Section 18.3.9
