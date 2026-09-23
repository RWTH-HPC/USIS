<!-- source: OpenMP API Specification, section 21.16 (omp_get_team_size Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 21 Parallel Region Support Routines -->

# 21.16 omp_get_team_size Routine

Name: omp_get_team_size                                    Properties: default
21
            Category: function
Return Type and Arguments
            Name                                         Type                         Properties
<return type>                                integer                      default
            level                                        integer                      default

Prototypes
                                                  C / C++
int omp_get_team_size(int level);
                                                  C / C++
                                                  Fortran
integer function omp_get_team_size(level)
integer level
                                                  Fortran
Effect
The omp_get_team_size routine returns the size of the current team to which the ancestor
thread or the encountering task belongs. If the requested nested level is outside the range of 0 and
the nested level of the encountering thread, as returned by the omp_get_level routine, the
routine returns -1. Inactive parallel regions are regarded as active parallel regions executed with
one thread.
11

Note – When the omp_get_team_size routine is called with a value of level =0, the routine
always returns 1. If level =omp_get_level(), the routine has the same effect as the
omp_get_num_threads routine.
15

Cross References
• omp_get_level Routine, see Section 21.14
• omp_get_num_threads Routine, see Section 21.2
