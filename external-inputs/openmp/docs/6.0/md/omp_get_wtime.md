<!-- source: OpenMP API Specification, section 30.3.1 (omp_get_wtime Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 30 Execution Control Routines -->

# 30.3.1 omp_get_wtime Routine

Name: omp_get_wtime                                       Properties: default
 4
      Category: function

Return Type
      Name                                        Type                           Properties
 6
      <return type>                               double                         default

Prototypes
                                                  C / C++
double omp_get_wtime(void);
                                                  C / C++
                                                  Fortran
double precision function omp_get_wtime()
                                                  Fortran
Effect
The omp_get_wtime routine returns a value equal to the elapsed wall clock time in seconds
since some time-in-the-past. The actual time-in-the-past is arbitrary, but it is guaranteed not to
change during the execution of an OpenMP program. The time returned is a per-thread time, so it is
not required to be globally consistent across all threads that participate in an OpenMP program.
