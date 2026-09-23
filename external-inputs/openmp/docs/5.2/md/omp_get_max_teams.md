<!-- source: OpenMP API Specification, section 18.4.4 (omp_get_max_teams) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.4.4 omp_get_max_teams

Summary
The omp_get_max_teams routine returns an upper bound on the number of teams that could be
created by a teams construct without a num_teams clause that is encountered after execution
returns from this routine.

Format
                                                        C / C++
int omp_get_max_teams(void);
                                                        C / C++
                                                        Fortran
integer function omp_get_max_teams()
                                                         Fortran
Binding
The binding task set for an omp_get_max_teams region is the generating task.

Effect
The value returned by omp_get_max_teams is the value of the nteams-var ICV of the current
device. This value is also an upper bound on the number of teams that can be created by a teams
construct without a num_teams clause that is encountered after execution returns from this
routine.

Cross References
• nteams-var ICV, see Table 2.1
• num_teams clause, see Section 10.2.1
• teams directive, see Section 10.2
