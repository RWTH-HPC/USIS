<!-- source: OpenMP API Specification, section 24.4 (omp_get_device_num Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 24 Device Information Routines -->

# 24.4 omp_get_device_num Routine

Name: omp_get_device_num                               Properties: device-information
 9
            Category: function

Return Type
            Name                                     Type                        Properties
11
            <return type>                            integer                     default

Prototypes
                                                     C / C++
int omp_get_device_num(void);
                                                     C / C++
                                                     Fortran
integer function omp_get_device_num()
                                                     Fortran
Effect
The omp_get_device_num routine returns the value of the device-num-var ICV, which is the
device number of the device on which the encountering thread is executing. When called on the
host device, it will return the same value as the omp_get_initial_device routine.

Cross References
• device-num-var ICV, see Table 3.1
• target Construct, see Section 15.8
