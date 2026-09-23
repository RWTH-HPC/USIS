<!-- source: OpenMP API Specification, section 24.14 (omp_set_device_teams_thread_limit) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 24 Device Information Routines -->

# 24.14 omp_set_device_teams_thread_limit

Routine
      Name:                                                Properties: device-information, ICV-
omp_set_device_teams_thread_limit                    modifying
      Category: subroutine

Arguments
            Name                                       Type                         Properties
thread_limit                               integer                      positive
            device_num                                 integer                      default

Prototypes
                                                       C / C++
void omp_set_device_teams_thread_limit(int thread_limit,
int device_num);
                                                       C / C++
                                                       Fortran
subroutine omp_set_device_teams_thread_limit(thread_limit, &
device_num)
integer thread_limit, device_num
                                                       Fortran
Effect
The omp_set_device_teams_thread_limit routine sets the value of the
teams-thread-limit-var ICV in the device data environment of device device_num to the value of
the thread_limit argument and thus defines the maximum number of threads that can execute tasks
in each contention group that a teams construct creates on that device. If the value of thread_limit
exceeds the number of threads that an implementation supports for each contention group created
by a teams construct on device device_num, the value of the teams-thread-limit-var ICV will be
set to the number that is supported by the implementation. If device_num is the device number of
the host device, omp_set_device_teams_thread_limit is equivalent to
omp_set_teams_thread_limit. If the device_num argument has the value of
omp_invalid_device or is not a conforming device number, runtime error termination occurs.
When called from within a target region, the effect of this routine is unspecified.

Restrictions
Restrictions to the omp_set_device_teams_thread_limit routine are as follows:
• The routine must not execute concurrently with any device-affecting construct on device
device_num.
• If device device_num is the host device, an omp_set_device_teams_thread_limit
region must be a strictly nested region of the implicit parallel region that surrounds the whole
OpenMP program.

Cross References
• teams-thread-limit-var ICV, see Table 3.1
• teams Construct, see Section 12.2
• thread_limit Clause, see Section 15.3
