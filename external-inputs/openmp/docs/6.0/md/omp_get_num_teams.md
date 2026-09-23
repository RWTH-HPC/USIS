<!-- source: OpenMP API Specification, section 22.1 (omp_get_num_teams Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 22 Teams Region Routines -->

# 22.1 omp_get_num_teams Routine

Name: omp_get_num_teams                                  Properties: ICV-retrieving, teams-
 5
      Category: function                                       nestable

Return Type
      Name                                       Type                         Properties
 7
      <return type>                              integer                      default

Prototypes
                                                 C / C++
int omp_get_num_teams(void);
                                                 C / C++
                                                 Fortran
integer function omp_get_num_teams()
                                                 Fortran
Effect
The omp_get_num_teams routine returns the value of the league-size-var ICV, which is the
number of initial teams in the current teams region. The routine returns 1 if it is called from
outside of a teams region.

Cross References
• league-size-var ICV, see Table 3.1
• teams Construct, see Section 12.2
