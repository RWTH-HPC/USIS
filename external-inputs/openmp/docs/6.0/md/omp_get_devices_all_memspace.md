<!-- source: OpenMP API Specification, section 27.1.5 (omp_get_devices_all_memspace Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 27 Memory Management Routines -->

# 27.1.5 omp_get_devices_all_memspace Routine

Name: omp_get_devices_all_memspace                       Properties: all-device-threads-
Category: function                                       binding, memory-management-routine,
                                                                     memory-space-retrieving
Return Type and Arguments
            Name                                        Type                        Properties
<return type>                               memspace_handle             default
            memspace                                    memspace_handle             intent(in), omp

Prototypes
                                                       C / C++
omp_memspace_handle_t omp_get_devices_all_memspace(
omp_memspace_handle_t memspace);
                                                       C / C++
                                                       Fortran
integer (kind=omp_memspace_handle_kind) function &
omp_get_devices_all_memspace(memspace)
integer (kind=omp_memspace_handle_kind), intent(in) :: memspace
                                                        Fortran
Effect
The omp_get_devices_all_memspace routine is a memory-space-retrieving routine. The
devices selected by the routine are all available devices.
Cross References
• Memory Space Retrieving Routines, see Section 27.1
• OpenMP memspace_handle Type, see Section 20.8.11
