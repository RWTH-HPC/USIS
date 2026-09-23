<!-- source: OpenMP API Specification, section 29.8 (omp_set_affinity_format Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 29 Thread Affinity Routines -->

# 29.8 omp_set_affinity_format Routine

Name: omp_set_affinity_format                           Properties: ICV-modifying
 5
      Category: subroutine

Arguments
      Name                                      Type                        Properties
 7
      format                                    char                        pointer, intent(in)

Prototypes
                                                C / C++
void omp_set_affinity_format(const char *format);
                                                C / C++
                                                Fortran
subroutine omp_set_affinity_format(format)
character(len=*), intent(in) :: format
                                                Fortran
Effect
The omp_set_affinity_format routine sets the affinity format to be used on the device by
setting the value of the affinity-format-var ICV. The value of the ICV is set by copying the
character string specified by the format argument into the ICV on the current device.
This routine has the described effect only when called from a sequential part of the program. When
called from within a parallel or teams region, the effect of this routine is implementation
defined.
When called from a sequential part of the program, the binding thread set for an
omp_set_affinity_format region is the encountering thread. When called from within any
parallel or teams region, the binding thread set (and binding region, if required) for the
omp_set_affinity_format region is implementation defined.

Restrictions
Restrictions to the omp_set_affinity_format routine are as follows:
• When called from within a target region the effect is unspecified.

Cross References
• OMP_AFFINITY_FORMAT, see Section 4.3.5
• OMP_DISPLAY_AFFINITY, see Section 4.3.4
• Controlling OpenMP Thread Affinity, see Section 12.1.3
• affinity-format-var ICV, see Table 3.1
• parallel Construct, see Section 12.1
• teams Construct, see Section 12.2
