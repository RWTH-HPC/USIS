<!-- source: OpenMP API Specification, section 24.12 (omp_set_device_num_teams Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 24 Device Information Routines -->

# 24.12 omp_set_device_num_teams Routine

Name: omp_set_device_num_teams                         Properties: device-information, ICV-
23
      Category: subroutine                                   modifying

Arguments
            Name                                      Type                       Properties
num_teams                                 integer                    non-negative
            device_num                                integer                    default

Prototypes
                                                     C / C++
void omp_set_device_num_teams(int num_teams, int device_num);
                                                     C / C++
                                                     Fortran
subroutine omp_set_device_num_teams(num_teams, device_num)
integer num_teams, device_num
                                                      Fortran
Effect
The effect of the omp_set_device_num_teams routine is to set the value of the nteams-var
ICV of device device_num to the value specified in the num_teams argument. Thus, the routine
determines the number of teams that will be requested for a teams region on device device_num if
the num_teams clause is not specified. If device_num is the device number of the host device,
omp_set_device_num_teams is equivalent to omp_set_num_teams. If the device_num
argument has the value of omp_invalid_device or is not a conforming device number,
runtime error termination occurs. When called from within a target region, the effect of this
routine is unspecified.

Restrictions
Restrictions to the omp_set_device_num_teams routine are as follows:
• The routine must not execute concurrently with any device-affecting construct on device
device_num.
• If device device_num is the host device, an omp_set_device_num_teams region must
be a strictly nested region of the implicit parallel region that surrounds the whole OpenMP
program.

Cross References
• nteams-var ICV, see Table 3.1
• num_teams Clause, see Section 12.2.1
• teams Construct, see Section 12.2
