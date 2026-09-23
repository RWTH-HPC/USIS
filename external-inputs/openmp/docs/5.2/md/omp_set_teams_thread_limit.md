<!-- source: OpenMP API Specification, section 18.4.5 (omp_set_teams_thread_limit) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.4.5 omp_set_teams_thread_limit

Summary
The omp_set_teams_thread_limit routine defines the maximum number of OpenMP
threads that can participate in each contention group created by a teams construct.

Format
                                                  C / C++
void omp_set_teams_thread_limit(int thread_limit);
                                                  C / C++
                                                  Fortran
subroutine omp_set_teams_thread_limit(thread_limit)
integer thread_limit
                                                  Fortran
Constraints on Arguments
The value of the argument passed to this routine must evaluate to a positive integer, or else the
behavior of this routine is implementation defined.

Binding
The binding task set for an omp_set_teams_thread_limit region is the generating task.

Effect
The omp_set_teams_thread_limit routine sets the value of the teams-thread-limit-var
ICV to the value of the thread_limit argument. If the value of thread_limit exceeds the number of
OpenMP threads that an implementation supports for each contention group created by a teams
construct, the value of the teams-thread-limit-var ICV will be set to the number that is supported by
the implementation.

Restrictions
Restrictions to the omp_set_teams_thread_limit routine are as follows:
• The routine may not be called from within a parallel region other than the implicit parallel region
that surrounds the whole OpenMP program.

Cross References
• teams directive, see Section 10.2
• teams-thread-limit-var ICV, see Table 2.1
• thread_limit clause, see Section 13.3
