<!-- source: OpenMP API Specification, section 27.8.5 (omp_get_devices_all_allocator Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 27 Memory Management Routines -->

# 27.8.5 omp_get_devices_all_allocator Routine

Name: omp_get_devices_all_allocator                       Properties: all-device-threads-
Category: function                                        binding, memory-management-routine,
                                                                memory-allocator-retrieving
Return Type and Arguments
      Name                                        Type                         Properties
<return type>                               allocator_handle             default
      memspace                                    memspace_handle              intent(in), omp

Prototypes
                                                  C / C++
omp_allocator_handle_t omp_get_devices_all_allocator(
omp_memspace_handle_t memspace);
                                                  C / C++
                                                  Fortran
integer (kind=omp_allocator_handle_kind) function &
omp_get_devices_all_allocator(memspace)
integer (kind=omp_memspace_handle_kind), intent(in) :: memspace
                                                  Fortran

Effect
The omp_get_devices_all_allocator routine is a memory-allocator-retrieving routine.
The devices selected by the routine are all available devices.

Cross References
• OpenMP allocator_handle Type, see Section 20.8.1
• Memory Space Retrieving Routines, see Section 27.1
• OpenMP memspace_handle Type, see Section 20.8.11
