<!-- source: OpenMP API Specification, section 22.2 (omp_set_num_teams Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 22 Teams Region Routines -->

# 22.2 omp_set_num_teams Routine

Name: omp_set_num_teams                              Properties: ICV-modifying
 2
            Category: subroutine

Arguments
            Name                                    Type                       Properties
 4
            num_teams                               integer                    non-negative

Prototypes
                                                    C / C++
void omp_set_num_teams(int num_teams);
                                                    C / C++
                                                    Fortran
subroutine omp_set_num_teams(num_teams)
integer num_teams
                                                    Fortran
Effect
The effect of the omp_set_num_teams routine is to set the value of the nteams-var ICV of the
host device to the value specified in the num_teams argument.

Restrictions
Restrictions to the omp_set_num_teams routine are as follows:
• An omp_set_num_teams region must be a strictly nested region of the implicit parallel
region that surrounds the whole OpenMP program.

Cross References
• nteams-var ICV, see Table 3.1
• num_teams Clause, see Section 12.2.1
• teams Construct, see Section 12.2
