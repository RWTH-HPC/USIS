<!-- source: OpenMP API Specification, section 24.13 (omp_get_device_teams_thread_limit) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 24 Device Information Routines -->

# 24.13 omp_get_device_teams_thread_limit

Routine
      Name:                                                Properties: device-information, ICV-
omp_get_device_teams_thread_limit                    retrieving
      Category: function
Return Type and Arguments
      Name                                     Type                      Properties
<return type>                            integer                   default
      device_num                               integer                   default

Prototypes
                                               C / C++
int omp_get_device_teams_thread_limit(int device_num);
                                               C / C++
                                               Fortran
integer function omp_get_device_teams_thread_limit(device_num)
integer device_num
                                               Fortran
Effect
The omp_get_device_teams_thread_limit routine returns the value of the
teams-thread-limit-var ICV in the device data environment of device device_num, which is the
maximum number of threads available to execute tasks in each contention group that a teams
construct creates on that device. If device_num is the device number of the host device,
omp_get_device_teams_thread_limit is equivalent to
omp_get_teams_thread_limit. If the device_num argument has the value of
omp_invalid_device or is not a conforming device number, the routine returns zero. When
called from within a target region, the effect of this routine is unspecified.

Cross References
• teams-thread-limit-var ICV, see Table 3.1
• teams Construct, see Section 12.2
