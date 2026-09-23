<!-- source: OpenMP API Specification, section 21.13 (omp_get_max_active_levels Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 21 Parallel Region Support Routines -->

# 21.13 omp_get_max_active_levels Routine

Name: omp_get_max_active_levels                            Properties: ICV-retrieving
19
            Category: function

Return Type
            Name                                         Type                         Properties
21
            <return type>                                integer                      default

Prototypes
                                                        C / C++
int omp_get_max_active_levels(void);
                                                        C / C++
                                                        Fortran
integer function omp_get_max_active_levels()
                                                         Fortran

Effect
The omp_get_max_active_levels routine returns the value of the max-active-levels-var
ICV. The current task may only generate an active parallel region if the returned value is greater
than the value of the active-levels-var ICV.

Cross References
• max-active-levels-var ICV, see Table 3.1
