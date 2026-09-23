<!-- source: OpenMP API Specification, section 21.5 (omp_get_thread_limit Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 21 Parallel Region Support Routines -->

# 21.5 omp_get_thread_limit Routine

Name: omp_get_thread_limit                               Properties: ICV-retrieving
22
            Category: function

Return Type
      Name                                        Type                        Properties
 2
      <return type>                               integer                     default

Prototypes
                                                 C / C++
int omp_get_thread_limit(void);
                                                 C / C++
                                                 Fortran
integer function omp_get_thread_limit()
                                                  Fortran
Effect
The omp_get_thread_limit routine returns the value of the thread-limit-var ICV. Thus, it
returns the maximum number of threads available to execute tasks in the current contention group.

Cross References
• thread-limit-var ICV, see Table 3.1
