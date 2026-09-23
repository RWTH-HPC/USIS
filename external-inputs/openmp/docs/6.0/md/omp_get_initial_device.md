<!-- source: OpenMP API Specification, section 24.10 (omp_get_initial_device Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 24 Device Information Routines -->

# 24.10 omp_get_initial_device Routine

Name: omp_get_initial_device                        Properties: device-information
 8
            Category: function

Return Type
            Name                                     Type                     Properties
10
            <return type>                            integer                  default

Prototypes
                                                     C / C++
int omp_get_initial_device(void);
                                                     C / C++
                                                     Fortran
integer function omp_get_initial_device()
                                                     Fortran
Effect
The effect of the omp_get_initial_device routine is to return the device number of the host
device. The value of the device number is the value of omp_initial_device or the value
returned by the omp_get_num_devices routine. When called from within a target region
the effect of this routine is unspecified.

Cross References
• target Construct, see Section 15.8
