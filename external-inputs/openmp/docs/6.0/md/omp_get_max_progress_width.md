<!-- source: OpenMP API Specification, section 24.6 (omp_get_max_progress_width Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 24 Device Information Routines -->

# 24.6 omp_get_max_progress_width Routine

Name: omp_get_max_progress_width                           Properties: device-information
15
      Category: function
Return Type and Arguments
      Name                                         Type                         Properties
<return type>                                integer                      default
      device_num                                   integer                      default

Prototypes
                                                  C / C++
int omp_get_max_progress_width(int device_num);
                                                  C / C++
                                                  Fortran
integer function omp_get_max_progress_width(device_num)
integer device_num
                                                   Fortran

Effect
The omp_get_max_progress_width routine returns the maximum size, in terms of
hardware threads, of progress units on the device specified by device_num. When called from
within a target region the effect of this routine is unspecified.
