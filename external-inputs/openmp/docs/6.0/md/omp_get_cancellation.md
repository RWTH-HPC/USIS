<!-- source: OpenMP API Specification, section 30.1 (omp_get_cancellation Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 30 Execution Control Routines -->

# 30.1 omp_get_cancellation Routine

Name: omp_get_cancellation                              Properties: ICV-retrieving
 9
            Category: function

Return Type
            Name                                       Type                        Properties
11
            <return type>                              logical                     default

Prototypes
                                                      C / C++
int omp_get_cancellation(void);
                                                      C / C++
                                                      Fortran
logical function omp_get_cancellation()
                                                      Fortran
Effect
The omp_get_cancellation routine returns the value of the cancel-var ICV. Thus, it returns
true if cancellation is enabled and otherwise it returns false.

Cross References
• cancel-var ICV, see Table 3.1
