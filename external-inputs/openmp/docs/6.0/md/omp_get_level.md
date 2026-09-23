<!-- source: OpenMP API Specification, section 21.14 (omp_get_level Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 21 Parallel Region Support Routines -->

# 21.14 omp_get_level Routine

Name: omp_get_level                                       Properties: ICV-retrieving
 8
      Category: function

Return Type
      Name                                        Type                         Properties
10
      <return type>                               integer                      default

Prototypes
                                                 C / C++
int omp_get_level(void);
                                                 C / C++
                                                 Fortran
integer function omp_get_level()
                                                  Fortran
Effect
The omp_get_level routine returns the value of the levels-var ICV. Thus, its effect is to return
the number of nested parallel regions (whether active or inactive) that enclose the current task
such that all of the parallel regions are enclosed by the outermost initial task region on the
current device.

Cross References
• levels-var ICV, see Table 3.1
• parallel Construct, see Section 12.1
