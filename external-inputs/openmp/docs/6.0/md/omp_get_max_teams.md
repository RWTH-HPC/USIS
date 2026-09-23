<!-- source: OpenMP API Specification, section 22.4 (omp_get_max_teams Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 22 Teams Region Routines -->

# 22.4 omp_get_max_teams Routine

Name: omp_get_max_teams                                  Properties: ICV-retrieving
13
      Category: function

Return Type
      Name                                        Type                        Properties
15
      <return type>                               integer                     default

Prototypes
                                                 C / C++
int omp_get_max_teams(void);
                                                 C / C++
                                                 Fortran
integer function omp_get_max_teams()
                                                 Fortran
Effect
The omp_get_max_teams routine returns the value of the nteams-var ICV of the current
device. If positive, this value is also an upper bound on the number of teams that can be created by
a teams construct without a num_teams clause that is encountered after execution returns from
this routine.

Cross References
• nteams-var ICV, see Table 3.1
• num_teams Clause, see Section 12.2.1
• teams Construct, see Section 12.2
