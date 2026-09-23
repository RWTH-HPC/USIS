<!-- source: OpenMP API Specification, section 18.4.6 (omp_get_teams_thread_limit) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.4.6 omp_get_teams_thread_limit

Summary
The omp_get_teams_thread_limit routine returns the maximum number of OpenMP
threads available to participate in each contention group created by a teams construct.

Format
                                                       C / C++
int omp_get_teams_thread_limit(void);
                                                       C / C++
                                                       Fortran
integer function omp_get_teams_thread_limit()
                                                         Fortran
Binding
The binding task set for an omp_get_teams_thread_limit region is the generating task.

Effect
The omp_get_teams_thread_limit routine returns the value of the teams-thread-limit-var
ICV.

Cross References
• teams directive, see Section 10.2
• teams-thread-limit-var ICV, see Table 2.1
