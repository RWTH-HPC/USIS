<!-- source: OpenMP API Specification, section 18.4.1 (omp_get_num_teams) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.4.1 omp_get_num_teams

Summary
The omp_get_num_teams routine returns the number of initial teams in the current teams
region.

Format
                                                       C / C++
int omp_get_num_teams(void);
                                                       C / C++
                                                       Fortran
integer function omp_get_num_teams()
                                                        Fortran
Binding
The binding task set for an omp_get_num_teams region is the generating task

Effect
The effect of this routine is to return the number of initial teams in the current teams region. The
routine returns 1 if it is called from outside of a teams region.

Cross References
• teams directive, see Section 10.2
