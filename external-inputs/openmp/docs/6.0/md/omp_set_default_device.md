<!-- source: OpenMP API Specification, section 24.1 (omp_set_default_device Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 24 Device Information Routines -->

# 24.1 omp_set_default_device Routine

Name: omp_set_default_device                                 Properties: device-information, ICV-
 9
            Category: subroutine                                         modifying

Arguments
            Name                                        Type                          Properties
11
            device_num                                  integer                       default

Prototypes
                                                        C / C++
void omp_set_default_device(int device_num);
                                                        C / C++
                                                        Fortran
subroutine omp_set_default_device(device_num)
integer device_num
                                                        Fortran
Effect
The effect of the omp_set_default_device routine is to set the value of the
default-device-var ICV of the current task to the value specified in the device-num argument, thus
determining the default target device. When called from within a target region, the effect of this
routine is unspecified.

Cross References
• default-device-var ICV, see Table 3.1
• target Construct, see Section 15.8
