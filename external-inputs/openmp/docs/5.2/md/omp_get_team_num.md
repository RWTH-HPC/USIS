<!-- source: OpenMP API Specification, section 18.4.2 (omp_get_team_num) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.4.2 omp_get_team_num

Summary
The omp_get_team_num routine returns the initial team number of the calling thread.
Format
                                               C / C++
int omp_get_team_num(void);
                                               C / C++
                                               Fortran
integer function omp_get_team_num()
                                               Fortran
Binding
The binding task set for an omp_get_team_num region is the generating task.
Effect
The omp_get_team_num routine returns the initial team number of the calling thread. The
initial team number is an integer between 0 and one less than the value returned by
omp_get_num_teams(), inclusive. The routine returns 0 if it is called outside of a teams
region.
Cross References
• omp_get_num_teams, see Section 18.4.1
• teams directive, see Section 10.2
