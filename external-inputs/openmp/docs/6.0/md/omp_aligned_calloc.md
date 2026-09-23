<!-- source: OpenMP API Specification, section 27.11.4 (omp_aligned_calloc Routine) -->
<!-- sliced from external-inputs/openmp/docs/6.0/text/OpenMP-API-Specification-6-0.txt by workflow/ingestion/openmp_spec_text.py -->
<!-- chapter: 27 Memory Management Routines -->

# 27.11.4 omp_aligned_calloc Routine

Name: omp_aligned_calloc                            Properties: aligned-memory-
      Category: function                                  allocating-routine, iso_c_binding,
memory-allocating-routine, memory-
                                                          management-routine, overloaded,
                                                          zeroed-memory-allocating-routine
Return Type and Arguments
      Name                                   Type                      Properties
      <return type>                          c_ptr                     default
      alignment                              c_size_t                  iso_c, value
 4
      nmemb                                  c_size_t                  iso_c, value
      size                                   c_size_t                  iso_c, value
      allocator                              allocator_handle          value, omp

Prototypes
                                                 C
void *omp_aligned_calloc(size_t alignment, size_t nmemb,
size_t size, omp_allocator_handle_t allocator);
                                                C
                                               C++
void *omp_aligned_calloc(size_t alignment, size_t nmemb,
size_t size,
omp_allocator_handle_t allocator = omp_null_allocator);
                                              C++
                                             Fortran
type (c_ptr) function omp_aligned_calloc(alignment, nmemb, size, &
allocator) bind(c)
use, intrinsic :: iso_c_binding, only : c_ptr, c_size_t
integer (kind=c_size_t), value :: alignment, nmemb, size
integer (kind=omp_allocator_handle_kind), value :: allocator
                                             Fortran
Effect
The omp_aligned_calloc routine is a zeroed-memory-allocating routine and an
aligned-memory-allocating routine.

Cross References
• OpenMP allocator_handle Type, see Section 20.8.1
• Memory Allocating Routines, see Section 27.11
