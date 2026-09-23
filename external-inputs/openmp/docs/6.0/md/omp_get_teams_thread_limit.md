<!-- source: OpenMP API Specification, section 22.5 (omp_get_teams_thread_limit Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 22 Teams Region Routines -->

# 22.5 omp_get_teams_thread_limit Routine

Name: omp_get_teams_thread_limit                       Properties: ICV-retrieving
 6
            Category: function

Return Type
            Name                                     Type                        Properties
 8
            <return type>                            integer                     default

Prototypes
                                                     C / C++
int omp_get_teams_thread_limit(void);
                                                     C / C++
                                                     Fortran
integer function omp_get_teams_thread_limit()
                                                     Fortran
Effect
The omp_get_teams_thread_limit routine returns the value of the teams-thread-limit-var
ICV, which is the maximum number of threads available to execute tasks in each contention group
that a teams construct creates.

Cross References
• teams-thread-limit-var ICV, see Table 3.1
• teams Construct, see Section 12.2
