<!-- source: OpenMP API Specification, section 27.1.3 (omp_get_devices_and_host_memspace Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 27 Memory Management Routines -->

# 27.1.3 omp_get_devices_and_host_memspace Routine

Name:                                               Properties: all-device-threads-
omp_get_devices_and_host_memspace                   binding, memory-management-routine,
            Category: function                                  memory-space-retrieving
Return Type and Arguments
            Name                                    Type                     Properties
            <return type>                           memspace_handle          default
ndevs                                   integer                  intent(in), positive
            devs                                    integer                  intent(in), pointer
            memspace                                memspace_handle          intent(in), omp

Prototypes
                                                  C / C++
omp_memspace_handle_t omp_get_devices_and_host_memspace(
int ndevs, const int *devs, omp_memspace_handle_t memspace);
                                                  C / C++
                                                  Fortran
integer (kind=omp_memspace_handle_kind) function &
omp_get_devices_and_host_memspace(ndevs, devs, memspace)
integer, intent(in) :: ndevs, devs(*)
integer (kind=omp_memspace_handle_kind), intent(in) :: memspace
                                                  Fortran
Effect
The omp_get_devices_and_host_memspace routine is a memory-space-retrieving
routine. The devices selected by the routine are the host device and those specified in the devs
argument.

Cross References
• Memory Space Retrieving Routines, see Section 27.1
• OpenMP memspace_handle Type, see Section 20.8.11
