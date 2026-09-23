<!-- source: OpenMP API Specification, section 24.9 (omp_is_initial_device Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 24 Device Information Routines -->

# 24.9 omp_is_initial_device Routine

Name: omp_is_initial_device                              Properties: device-information
18
      Category: function

Return Type
      Name                                        Type                        Properties
20
      <return type>                               logical                     default

Prototypes
                                                     C / C++
int omp_is_initial_device(void);
                                                     C / C++
                                                     Fortran
logical function omp_is_initial_device()
                                                     Fortran
Effect
The omp_is_initial_device routine returns true if the current task is executing on the host
device; otherwise, it returns false.
