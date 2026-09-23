<!-- source: OpenMP API Specification, section 24.8 (omp_get_uid_from_device Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 24 Device Information Routines -->

# 24.8 omp_get_uid_from_device Routine

Name: omp_get_uid_from_device                          Properties: device-information
22
            Category: function

Return Type and Arguments
      Name                                        Type                        Properties
<return type>                               const char                  pointer
      device_num                                  integer                     intent(in)

Prototypes
                                                  C / C++
const char         *omp_get_uid_from_device(int device_num);
                                                  C / C++
                                                  Fortran
character(:) function omp_get_uid_from_device(device_num)
pointer :: omp_get_uid_from_device
integer, intent(in) :: device_num
                                                  Fortran
Effect
The omp_get_uid_from_device routine returns the implementation defined unique identifier
string that identifies the device specified by device_num. If the device_num argument has a value of
omp_invalid_device, the routine returns NULL. When called from within a target region,
the effect is unspecified.

Cross References
• available-devices-var ICV, see Table 3.1
• default-device-var ICV, see Table 3.1
• omp_get_device_from_uid Routine, see Section 24.7
