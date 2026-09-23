<!-- source: OpenMP API Specification, section 21.8 (omp_get_dynamic Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 21 Parallel Region Support Routines -->

# 21.8 omp_get_dynamic Routine

Name: omp_get_dynamic                                  Properties: ICV-retrieving
22
            Category: function

Return Type
            Name                                       Type                      Properties
24
            <return type>                              logical                   default

Prototypes
                                                 C / C++
int omp_get_dynamic(void);
                                                 C / C++
                                                 Fortran
logical function omp_get_dynamic()
                                                 Fortran
Effect
The omp_get_dynamic routine returns the value of the dyn-var ICV. Thus, this routine returns
true if dynamic adjustment of the number of threads is enabled for the current task; otherwise, it
returns false. If an implementation does not support dynamic adjustment of the number of threads,
then this routine always returns false.

Cross References
• dyn-var ICV, see Table 3.1
