<!-- source: OpenMP API Specification, section 27.2 (omp_get_memspace_num_resources Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 27 Memory Management Routines -->

# 27.2 omp_get_memspace_num_resources Routine

Name: omp_get_memspace_num_resources                     Properties: all-device-threads-binding,
24
            Category: function                                       memory-management-routine

Return Type and Arguments
      Name                                    Type                       Properties
<return type>                           integer                    default
      memspace                                memspace_handle            intent(in), omp

Prototypes
                                              C / C++
int omp_get_memspace_num_resources(
omp_memspace_handle_t memspace);
                                              C / C++
                                              Fortran
integer function omp_get_memspace_num_resources(memspace)
integer (kind=omp_memspace_handle_kind), intent(in) :: memspace
                                              Fortran
Effect
The omp_get_memspace_num_resources routine is a memory-management routine that
returns the number of distinct storage resources that are associated with the memory space
represented by the memspace handle.
Restrictions
The restrictions to the omp_get_memspace_num_resources routine are as follows:
• The memspace argument must be a valid memory space.

Cross References
• Memory Spaces, see Section 8.1
• OpenMP memspace_handle Type, see Section 20.8.11
