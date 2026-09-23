<!-- source: OpenMP API Specification, section 27.1.4 (omp_get_device_and_host_memspace Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 27 Memory Management Routines -->

# 27.1.4 omp_get_device_and_host_memspace Routine

Name:                                                     Properties: all-device-threads-
omp_get_device_and_host_memspace                          binding, memory-management-routine,
      Category: function                                        memory-space-retrieving
Return Type and Arguments
      Name                                        Type                         Properties
      <return type>                               memspace_handle              default
18
      dev                                         integer                      intent(in)
      memspace                                    memspace_handle              intent(in), omp

Prototypes
                                                  C / C++
omp_memspace_handle_t omp_get_device_and_host_memspace(int dev,
omp_memspace_handle_t memspace);
                                                  C / C++
                                                  Fortran
integer (kind=omp_memspace_handle_kind) function &
omp_get_device_and_host_memspace(dev, memspace)
integer, intent(in) :: dev
integer (kind=omp_memspace_handle_kind), intent(in) :: memspace
                                                  Fortran

Effect
The omp_get_device_and_host_memspace routine is a memory-space-retrieving routine.
The devices selected by the routine are the host device and the device specified in the dev argument.

Cross References
• Memory Space Retrieving Routines, see Section 27.1
• OpenMP memspace_handle Type, see Section 20.8.11
