<!-- source: OpenMP API Specification, section 22.6 (omp_set_teams_thread_limit Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 22 Teams Region Routines -->

# 22.6 omp_set_teams_thread_limit Routine

Name: omp_set_teams_thread_limit                       Properties: ICV-modifying
20
            Category: subroutine

Arguments
            Name                                     Type                        Properties
22
            thread_limit                             integer                     positive

Prototypes
                                                C / C++
void omp_set_teams_thread_limit(int thread_limit);
                                                C / C++
                                                Fortran
subroutine omp_set_teams_thread_limit(thread_limit)
integer thread_limit
                                                 Fortran
Effect
The omp_set_teams_thread_limit routine sets the value of the teams-thread-limit-var
ICV to the value of the thread_limit argument and thus defines the maximum number of threads
that can execute tasks in each contention group that a teams construct creates on the host device.
If the value of thread_limit exceeds the number of threads that an implementation supports for each
contention group created by a teams construct, the value of the teams-thread-limit-var ICV will
be set to the number that is supported by the implementation.

Restrictions
Restrictions to the omp_set_teams_thread_limit routine are as follows:
• An omp_set_num_teams region must be a strictly nested region of the implicit parallel
region that surrounds the whole OpenMP program.

Cross References
• teams-thread-limit-var ICV, see Table 3.1
• teams Construct, see Section 12.2
• thread_limit Clause, see Section 15.3
