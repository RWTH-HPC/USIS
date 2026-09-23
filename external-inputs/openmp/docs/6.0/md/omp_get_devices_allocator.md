<!-- source: OpenMP API Specification, section 27.8.1 (omp_get_devices_allocator Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 27 Memory Management Routines -->

# 27.8.1 omp_get_devices_allocator Routine

Name: omp_get_devices_allocator                           Properties: all-device-threads-
Category: function                                        binding, memory-management-routine,
                                                                memory-allocator-retrieving

Return Type and Arguments
            Name                                    Type                      Properties
            <return type>                           allocator_handle          default
ndevs                                   integer                   intent(in), positive
            devs                                    integer                   intent(in), pointer
            memspace                                memspace_handle           intent(in), omp

Prototypes
                                                    C / C++
omp_allocator_handle_t omp_get_devices_allocator(int ndevs,
const int *devs, omp_memspace_handle_t memspace);
                                                    C / C++
                                                    Fortran
integer (kind=omp_allocator_handle_kind) function &
omp_get_devices_allocator(ndevs, devs, memspace)
integer, intent(in) :: ndevs, devs(*)
integer (kind=omp_memspace_handle_kind), intent(in) :: memspace
                                                    Fortran
Effect
The omp_get_devices_allocator routine is a memory-allocator-retrieving routine. The
devices selected by the routine are those specified in the devs argument.

Cross References
• OpenMP allocator_handle Type, see Section 20.8.1
• Memory Allocator Retrieving Routines, see Section 27.8
• OpenMP memspace_handle Type, see Section 20.8.11
