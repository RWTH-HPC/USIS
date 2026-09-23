<!-- source: OpenMP API Specification, section 18.4.3 (omp_set_num_teams) -->
<!-- sliced from external-inputs/openmp/docs/5.2/text/OpenMP-API-Specification-5-2.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 18 Runtime Library Routines -->

# 18.4.3 omp_set_num_teams

Summary
The omp_set_num_teams routine affects the number of threads to be used for subsequent
teams regions that do not specify a num_teams clause, by setting the value of the nteams-var
ICV of the current device.
Format
                                               C / C++
void omp_set_num_teams(int num_teams);
                                               C / C++
                                               Fortran
subroutine omp_set_num_teams(num_teams)
integer num_teams
                                               Fortran

Constraints on Arguments
The value of the argument passed to this routine must evaluate to a positive integer, or else the
behavior of this routine is implementation defined.

Binding
The binding task set for an omp_set_num_teams region is the generating task.

Effect
The effect of this routine is to set the value of the nteams-var ICV of the current device to the value
specified in the argument.

Restrictions
Restrictions to the omp_set_num_teams routine are as follows:
• The routine may not be called from within a parallel region that is not the implicit parallel region
that surrounds the whole OpenMP program.

Cross References
• nteams-var ICV, see Table 2.1
• num_teams clause, see Section 10.2.1
• teams directive, see Section 10.2
