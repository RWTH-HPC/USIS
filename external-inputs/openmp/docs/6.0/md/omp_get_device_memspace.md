<!-- source: OpenMP API Specification, section 27.1.2 (omp_get_device_memspace Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 27 Memory Management Routines -->

# 27.1.2 omp_get_device_memspace Routine

Name: omp_get_device_memspace                       Properties: all-device-threads-
Category: function                                  binding, memory-management-routine,
                                                                memory-space-retrieving
Return Type and Arguments
            Name                                    Type                     Properties
            <return type>                           memspace_handle          default
 4
            dev                                     integer                  intent(in)
            memspace                                memspace_handle          intent(in), omp

Prototypes
                                                    C / C++
omp_memspace_handle_t omp_get_device_memspace(int dev,
omp_memspace_handle_t memspace);
                                                    C / C++
                                                    Fortran
integer (kind=omp_memspace_handle_kind) function &
omp_get_device_memspace(dev, memspace)
integer, intent(in) :: dev
integer (kind=omp_memspace_handle_kind), intent(in) :: memspace
                                                    Fortran
Effect
The omp_get_device_memspace routine is a memory-space-retrieving routine. The device
selected by the routine is the device specified in the dev argument.

Cross References
• Memory Space Retrieving Routines, see Section 27.1
• OpenMP memspace_handle Type, see Section 20.8.11
