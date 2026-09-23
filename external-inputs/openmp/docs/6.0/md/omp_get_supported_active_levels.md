<!-- source: OpenMP API Specification, section 21.11 (omp_get_supported_active_levels) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 21 Parallel Region Support Routines -->

# 21.11 omp_get_supported_active_levels

Routine
      Name:                                                  Properties: default
omp_get_supported_active_levels
      Category: function

Return Type
      Name                                      Type                       Properties
 8
      <return type>                             integer                    default

Prototypes
                                               C / C++
int omp_get_supported_active_levels(void);
                                               C / C++
                                               Fortran
integer function omp_get_supported_active_levels()
                                               Fortran
Effect
The omp_get_supported_active_levels routine returns the number of supported active
levels. The max-active-levels-var ICV cannot have a value that is greater than this number. The
value that the omp_get_supported_active_levels routine returns is implementation
defined, but it must be greater than 0.

Cross References
• max-active-levels-var ICV, see Table 3.1
