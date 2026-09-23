<!-- source: OpenMP API Specification, section 21.17 (omp_get_active_level Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 21 Parallel Region Support Routines -->

# 21.17 omp_get_active_level Routine

Name: omp_get_active_level                                Properties: ICV-retrieving
20
      Category: function

Return Type
      Name                                        Type                         Properties
22
      <return type>                               integer                      default

Prototypes
                                                  C / C++
int omp_get_active_level(void);
                                                  C / C++
                                                  Fortran
integer function omp_get_active_level()
                                                  Fortran

Effect
The effect of the omp_get_active_level routine is to return the number of nested active
parallel regions that enclose the current task such that all parallel regions are enclosed by
the outermost initial task region on the current device. Thus, the routine returns the value of the
active-levels-var ICV.

Cross References
• active-levels-var ICV, see Table 3.1
• parallel Construct, see Section 12.1
