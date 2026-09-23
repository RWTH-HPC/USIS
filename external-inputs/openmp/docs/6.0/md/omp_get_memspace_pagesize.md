<!-- source: OpenMP API Specification, section 27.3 (omp_get_memspace_pagesize Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 27 Memory Management Routines -->

# 27.3 omp_get_memspace_pagesize Routine

Name: omp_get_memspace_pagesize                      Properties: all-device-threads-binding,
Category: function                                   iso_c_binding, memory-management-
                                                           routine
Return Type and Arguments
      Name                                    Type                       Properties
<return type>                           c_size_t                   default
      memspace                                memspace_handle            intent(in), omp

Prototypes
                                                    C / C++
size_t omp_get_memspace_pagesize(omp_memspace_handle_t memspace);
                                                    C / C++
                                                    Fortran
integer (kind=c_size_t) function omp_get_memspace_pagesize(&
memspace) bind(c)
use, intrinsic :: iso_c_binding, only : c_size_t
integer (kind=omp_memspace_handle_kind), intent(in) :: memspace
                                                    Fortran
Effect
The omp_get_memspace_pagesize routine is a memory-management routine that returns the
page size that the memory space represented by the memspace handle supports.

Restrictions
The restrictions to the omp_get_memspace_pagesize routine are as follows:
• The memspace argument must be a valid memory space.

Cross References
• Memory Spaces, see Section 8.1
• OpenMP memspace_handle Type, see Section 20.8.11
