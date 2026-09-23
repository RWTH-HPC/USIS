<!-- source: OpenMP API Specification, section 27.4 (omp_get_submemspace Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 27 Memory Management Routines -->

# 27.4 omp_get_submemspace Routine

Name: omp_get_submemspace                          Properties: all-device-threads-binding,
17
            Category: function                                 memory-management-routine
Return Type and Arguments
            Name                                    Type                     Properties
            <return type>                           memspace_handle          default
memspace                                memspace_handle          intent(in), omp
            num_resources                           integer                  intent(in), non-negative
            resources                               integer                  intent(in), pointer

Prototypes
                                                C / C++
omp_memspace_handle_t omp_get_submemspace(
omp_memspace_handle_t memspace, int num_resources,
const int *resources);
                                                C / C++
                                                Fortran
integer (kind=omp_memspace_handle_kind) function &
omp_get_submemspace(memspace, num_resources, resources)
integer (kind=omp_memspace_handle_kind), intent(in) :: memspace
integer, intent(in) :: num_resources, resources(*)
                                                Fortran
Effect
The omp_get_submemspace routine is a memory-management routine that returns a new
memory space that contains a subset of the resources of the original memory space. The new
memory space represents only the resources of the memory space represented by the memspace
handle that are specified by the resources argument. If num_resources is zero or a memory space
cannot be created for the requested resources, the special value omp_null_mem_space is
returned.

Restrictions
The restrictions to the omp_get_submemspace routine are as follows:
• The memspace argument must be a valid memory space.
• The resources array must contain at least as many entries as specified by the num_resources
argument.
• The value of each entry of the resources array must be between 0 and one less than the
number of resources associated with the memory space represented by the memspace
argument.

Cross References
• Memory Spaces, see Section 8.1
• OpenMP memspace_handle Type, see Section 20.8.11
