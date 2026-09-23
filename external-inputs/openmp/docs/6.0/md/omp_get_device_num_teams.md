<!-- source: OpenMP API Specification, section 24.11 (omp_get_device_num_teams Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 24 Device Information Routines -->

# 24.11 omp_get_device_num_teams Routine

Name: omp_get_device_num_teams                         Properties: device-information, ICV-
 2
      Category: function                                     retrieving
Return Type and Arguments
      Name                                      Type                       Properties
<return type>                             integer                    default
      device_num                                integer                    default

Prototypes
                                               C / C++
int omp_get_device_num_teams(int device_num);
                                               C / C++
                                               Fortran
integer function omp_get_device_num_teams(device_num)
integer device_num
                                                Fortran
Effect
The omp_get_device_num_teams routine returns the value of the nteams-var ICV in the
device data environment of device device_num. Thus, the routine returns the number of teams that
will be requested for a teams region on device device_num if the num_teams clause is not
specified. If device_num is the device number of the host device,
omp_get_device_num_teams is equivalent to omp_get_num_teams. If the device_num
argument has the value of omp_invalid_device or is not a conforming device number, the
routine returns zero. When called from within a target region, the effect of this routine is
unspecified.

Cross References
• nteams-var ICV, see Table 3.1
• num_teams Clause, see Section 12.2.1
• teams Construct, see Section 12.2
