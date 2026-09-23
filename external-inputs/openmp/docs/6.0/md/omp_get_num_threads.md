<!-- source: OpenMP API Specification, section 21.2 (omp_get_num_threads Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 21 Parallel Region Support Routines -->

# 21.2 omp_get_num_threads Routine

Name: omp_get_num_threads                                Properties: default
 2
      Category: function

Return Type
      Name                                        Type                        Properties
 4
      <return type>                               integer                     default

Prototypes
                                                 C / C++
int omp_get_num_threads(void);
                                                 C / C++
                                                 Fortran
integer function omp_get_num_threads()
                                                 Fortran
Effect
The omp_get_num_threads routine returns the number of threads in the team that is executing
the parallel region to which the routine region binds.
