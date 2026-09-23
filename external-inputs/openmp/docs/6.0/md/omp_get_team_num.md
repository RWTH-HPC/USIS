<!-- source: OpenMP API Specification, section 22.3 (omp_get_team_num Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 22 Teams Region Routines -->

# 22.3 omp_get_team_num Routine

Name: omp_get_team_num                               Properties: ICV-retrieving, teams-
21
            Category: function                                   nestable

Return Type
            Name                                    Type                       Properties
23
            <return type>                           integer                    default

Prototypes
                                                 C / C++
int omp_get_team_num(void);
                                                 C / C++
                                                 Fortran
integer function omp_get_team_num()
                                                 Fortran
Effect
The omp_get_team_num routine returns the value of the team-num-var ICV, which is the team
number of the current team and is an integer between 0 and one less than the value returned by
omp_get_num_teams, inclusive. The routine returns 0 if it is called outside of a teams region.

Cross References
• team-num-var ICV, see Table 3.1
• omp_get_num_teams Routine, see Section 22.1
• teams Construct, see Section 12.2
