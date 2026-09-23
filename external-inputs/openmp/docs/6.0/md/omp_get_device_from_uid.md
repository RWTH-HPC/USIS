<!-- source: OpenMP API Specification, section 24.7 (omp_get_device_from_uid Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 24 Device Information Routines -->

# 24.7 omp_get_device_from_uid Routine

Name: omp_get_device_from_uid                          Properties: device-information
 6
            Category: function
Return Type and Arguments
            Name                                        Type                     Properties
<return type>                               integer                  default
            uid                                         char                     pointer, intent(in)

Prototypes
                                                        C / C++
int omp_get_device_from_uid(const char *uid);
                                                        C / C++
                                                        Fortran
integer function omp_get_device_from_uid(uid)
character(len=*), intent(in) :: uid
                                                        Fortran
Effect
The omp_get_device_from_uid routine returns the device number associated with the device
specified by the uid; if no device with that uid is available, the value of omp_invalid_device
is returned. When called from within a target region, the effect is unspecified.

Cross References
• available-devices-var ICV, see Table 3.1
• default-device-var ICV, see Table 3.1
• omp_get_uid_from_device Routine, see Section 24.8
