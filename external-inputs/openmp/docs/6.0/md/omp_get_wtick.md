<!-- source: OpenMP API Specification, section 30.3.2 (omp_get_wtick Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 30 Execution Control Routines -->

# 30.3.2 omp_get_wtick Routine

Name: omp_get_wtick                                       Properties: default
16
      Category: function

Return Type
      Name                                        Type                           Properties
18
      <return type>                               double                         default

Prototypes
                                                  C / C++
double omp_get_wtick(void);
                                                  C / C++
                                                  Fortran
double precision function omp_get_wtick()
                                                  Fortran

Effect
The omp_get_wtick routine returns the precision of the timer used by omp_get_wtime as a
value equal to the number of seconds between successive clock ticks. The return value of the
omp_get_wtick routine is not guaranteed to be consistent across any set of threads.

Cross References
• omp_get_wtime Routine, see Section 30.3.1
