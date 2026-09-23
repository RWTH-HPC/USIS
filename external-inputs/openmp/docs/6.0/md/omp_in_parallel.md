<!-- source: OpenMP API Specification, section 21.6 (omp_in_parallel Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 21 Parallel Region Support Routines -->

# 21.6 omp_in_parallel Routine

Name: omp_in_parallel                                    Properties: default
12
      Category: function

Return Type
      Name                                        Type                        Properties
14
      <return type>                               logical                     default

Prototypes
                                                 C / C++
int omp_in_parallel(void);
                                                 C / C++
                                                 Fortran
logical function omp_in_parallel()
                                                  Fortran
Effect
The effect of the omp_in_parallel routine is to return true if the current task is enclosed by an
active parallel region, and the parallel region is enclosed by the outermost initial task region on
the device. That is, it returns true if the active-levels-var ICV is greater than zero. Otherwise, it
returns false.

Cross References
• active-levels-var ICV, see Table 3.1
• parallel Construct, see Section 12.1
